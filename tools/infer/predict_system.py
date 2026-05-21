# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
import subprocess

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, "../..")))

os.environ["FLAGS_allocator_strategy"] = "auto_growth"

import cv2
import copy
import numpy as np
import json
import time
import logging
from PIL import Image
import tools.infer.utility as utility
import tools.infer.predict_rec as predict_rec
import tools.infer.predict_det as predict_det
import tools.infer.predict_cls as predict_cls
from ppocr.utils.utility import get_image_file_list, check_and_read
from ppocr.utils.logging import get_logger
from tools.infer.utility import (
    draw_ocr_box_txt,
    get_rotate_crop_image,
    get_minarea_rect_crop,
    slice_generator,
    merge_fragmented,
)
from ppocr.utils.font_classifier import create_font_classifier

logger = get_logger()


class TextSystem(object):
    def __init__(self, args):
        if not args.show_log:
            logger.setLevel(logging.INFO)

        self.text_detector = predict_det.TextDetector(args)
        self.text_recognizer = predict_rec.TextRecognizer(args)
        self.use_angle_cls = args.use_angle_cls
        self.drop_score = args.drop_score
        if self.use_angle_cls:
            self.text_classifier = predict_cls.TextClassifier(args)

        # 初始化字体分类器
        self.font_classifier = create_font_classifier(args)
        self.enable_font_classifier = self.font_classifier is not None

        self.args = args
        self.crop_image_res_index = 0

    def draw_crop_rec_res(self, output_dir, img_crop_list, rec_res):
        os.makedirs(output_dir, exist_ok=True)
        bbox_num = len(img_crop_list)
        for bno in range(bbox_num):
            cv2.imwrite(
                os.path.join(
                    output_dir, f"mg_crop_{bno+self.crop_image_res_index}.jpg"
                ),
                img_crop_list[bno],
            )
            logger.debug(f"{bno}, {rec_res[bno]}")
        self.crop_image_res_index += bbox_num

    def __call__(self, img, cls=True, slice={}):
        time_dict = {"det": 0, "rec": 0, "cls": 0, "font": 0, "all": 0}

        if img is None:
            logger.debug("no valid image provided")
            return None, None, time_dict

        start = time.time()
        ori_im = img.copy()
        if slice:
            slice_gen = slice_generator(
                img,
                horizontal_stride=slice["horizontal_stride"],
                vertical_stride=slice["vertical_stride"],
            )
            elapsed = []
            dt_slice_boxes = []
            for slice_crop, v_start, h_start in slice_gen:
                dt_boxes, elapse = self.text_detector(slice_crop, use_slice=True)
                if dt_boxes.size:
                    dt_boxes[:, :, 0] += h_start
                    dt_boxes[:, :, 1] += v_start
                    dt_slice_boxes.append(dt_boxes)
                    elapsed.append(elapse)
            dt_boxes = np.concatenate(dt_slice_boxes)

            dt_boxes = merge_fragmented(
                boxes=dt_boxes,
                x_threshold=slice["merge_x_thres"],
                y_threshold=slice["merge_y_thres"],
            )
            elapse = sum(elapsed)
        else:
            dt_boxes, elapse = self.text_detector(img)

        time_dict["det"] = elapse

        if dt_boxes is None:
            logger.debug("no dt_boxes found, elapsed : {}".format(elapse))
            end = time.time()
            time_dict["all"] = end - start
            return None, None, time_dict
        else:
            logger.debug(
                "dt_boxes num : {}, elapsed : {}".format(len(dt_boxes), elapse)
            )
        img_crop_list = []

        dt_boxes = sorted_boxes(dt_boxes)

        for bno in range(len(dt_boxes)):
            tmp_box = copy.deepcopy(dt_boxes[bno])
            if self.args.det_box_type == "quad":
                img_crop = get_rotate_crop_image(ori_im, tmp_box)
            else:
                img_crop = get_minarea_rect_crop(ori_im, tmp_box)
            img_crop_list.append(img_crop)
        if self.use_angle_cls and cls:
            img_crop_list, angle_list, elapse = self.text_classifier(img_crop_list)
            time_dict["cls"] = elapse
            logger.debug(
                "cls num  : {}, elapsed : {}".format(len(img_crop_list), elapse)
            )
        if len(img_crop_list) > 1000:
            logger.debug(
                f"rec crops num: {len(img_crop_list)}, time and memory cost may be large."
            )

        rec_res, elapse = self.text_recognizer(img_crop_list)
        time_dict["rec"] = elapse
        logger.debug("rec_res num  : {}, elapsed : {}".format(len(rec_res), elapse))
        if self.args.save_crop_res:
            self.draw_crop_rec_res(self.args.crop_res_save_dir, img_crop_list, rec_res)
        
        # 字体分类 - 批量字符识别（GPU批处理优化）
        font_res = []
        if self.enable_font_classifier:
            font_start = time.time()
            
            # 第一步：收集所有字符图像和索引映射
            all_char_crops = []
            char_to_line_map = []  # (line_idx, char_idx)
            line_char_counts = []  # 每行的字符数
            
            for line_idx, (box, rec_result) in enumerate(zip(dt_boxes, rec_res)):
                rec_str, rec_conf = rec_result[0], rec_result[1]
                char_word_info = rec_result[2] if len(rec_result) > 2 else None
                
                if char_word_info is not None:
                    # 计算字符位置
                    from ppstructure.utility import cal_ocr_word_box
                    word_box_content_list, word_box_list = cal_ocr_word_box(
                        rec_str, box, char_word_info
                    )
                    
                    # 裁剪所有字符
                    for char_idx, (char, char_box) in enumerate(zip(word_box_content_list, word_box_list)):
                        try:
                            # char_box 格式: ((x1, y1), (x2, y2), (x3, y3), (x4, y4))
                            x_coords = [p[0] for p in char_box]
                            y_coords = [p[1] for p in char_box]
                            x_min = int(max(0, min(x_coords)))
                            x_max = int(min(ori_im.shape[1], max(x_coords)))
                            y_min = int(max(0, min(y_coords)))
                            y_max = int(min(ori_im.shape[0], max(y_coords)))
                            
                            if x_max > x_min and y_max > y_min:
                                char_crop = ori_im[y_min:y_max, x_min:x_max]
                                all_char_crops.append(char_crop)
                                char_to_line_map.append((line_idx, char_idx))
                        except Exception as e:
                            logger.debug(f"Character crop failed: {e}")
                    
                    line_char_counts.append(len(word_box_content_list))
                else:
                    # 如果没有字符位置信息，使用行级图像
                    line_char_counts.append(len(rec_str))
            
            # 第二步：批量预测所有字符（一次性GPU推理）
            if all_char_crops:
                logger.debug(f"Batch predicting {len(all_char_crops)} characters...")
                batch_font_results = self.font_classifier.predict_batch(all_char_crops)
                
                # 第三步：重组结果到每一行
                # 创建映射字典：(line_idx, char_idx) -> result
                result_map = {}
                for idx, (line_idx, char_idx) in enumerate(char_to_line_map):
                    result_map[(line_idx, char_idx)] = batch_font_results[idx] if idx < len(batch_font_results) else {}
                
                # 按行重组
                for line_idx in range(len(rec_res)):
                    char_count = line_char_counts[line_idx]
                    line_char_attrs = []
                    
                    for char_idx in range(char_count):
                        key = (line_idx, char_idx)
                        line_char_attrs.append(result_map.get(key, {}))
                    
                    font_res.append(line_char_attrs)
            else:
                # 没有字符，创建空结果
                for line_idx in range(len(rec_res)):
                    font_res.append([])
            
            font_elapse = time.time() - font_start
            time_dict["font"] = font_elapse
            logger.debug("font_res num : {}, elapsed : {:.3f}s (batch mode)".format(len(font_res), font_elapse))
            
            # 将字体信息添加到识别结果中
            for idx in range(len(rec_res)):
                if idx < len(font_res):
                    # 将 rec_res 转换为列表并添加字符级字体信息
                    rec_res[idx] = list(rec_res[idx]) + [font_res[idx]]
        
        filter_boxes, filter_rec_res = [], []
        for box, rec_result in zip(dt_boxes, rec_res):
            text, score = rec_result[0], rec_result[1]
            if score >= self.drop_score:
                filter_boxes.append(box)
                filter_rec_res.append(rec_result)
        end = time.time()
        time_dict["all"] = end - start
        return filter_boxes, filter_rec_res, time_dict


def sorted_boxes(dt_boxes):
    """
    Sort text boxes in order from top to bottom, left to right
    args:
        dt_boxes(array):detected text boxes with shape [4, 2]
    return:
        sorted boxes(array) with shape [4, 2]
    """
    num_boxes = dt_boxes.shape[0]
    sorted_boxes = sorted(dt_boxes, key=lambda x: (x[0][1], x[0][0]))
    _boxes = list(sorted_boxes)

    for i in range(num_boxes - 1):
        for j in range(i, -1, -1):
            if abs(_boxes[j + 1][0][1] - _boxes[j][0][1]) < 10 and (
                _boxes[j + 1][0][0] < _boxes[j][0][0]
            ):
                tmp = _boxes[j]
                _boxes[j] = _boxes[j + 1]
                _boxes[j + 1] = tmp
            else:
                break
    return _boxes


def main(args):
    image_file_list = get_image_file_list(args.image_dir)
    image_file_list = image_file_list[args.process_id :: args.total_process_num]
    text_sys = TextSystem(args)
    is_visualize = True
    font_path = args.vis_font_path
    drop_score = args.drop_score
    draw_img_save_dir = args.draw_img_save_dir
    os.makedirs(draw_img_save_dir, exist_ok=True)
    save_results = []

    logger.info(
        "In PP-OCRv3, rec_image_shape parameter defaults to '3, 48, 320', "
        "if you are using recognition model with PP-OCRv2 or an older version, please set --rec_image_shape='3,32,320"
    )

    # warm up 10 times
    if args.warmup:
        img = np.random.uniform(0, 255, [640, 640, 3]).astype(np.uint8)
        for i in range(10):
            res = text_sys(img)

    total_time = 0
    cpu_mem, gpu_mem, gpu_util = 0, 0, 0
    _st = time.time()
    count = 0
    for idx, image_file in enumerate(image_file_list):
        img, flag_gif, flag_pdf = check_and_read(image_file)
        if not flag_gif and not flag_pdf:
            img = cv2.imread(image_file)
        if not flag_pdf:
            if img is None:
                logger.debug("error in loading image:{}".format(image_file))
                continue
            imgs = [img]
        else:
            page_num = args.page_num
            if page_num > len(img) or page_num == 0:
                page_num = len(img)
            imgs = img[:page_num]
        for index, img in enumerate(imgs):
            starttime = time.time()
            dt_boxes, rec_res, time_dict = text_sys(img)
            elapse = time.time() - starttime
            total_time += elapse
            if len(imgs) > 1:
                logger.debug(
                    str(idx)
                    + "_"
                    + str(index)
                    + "  Predict time of %s: %.3fs" % (image_file, elapse)
                )
            else:
                logger.debug(
                    str(idx) + "  Predict time of %s: %.3fs" % (image_file, elapse)
                )
            for rec_result in rec_res:
                text = rec_result[0]
                score = rec_result[1]
                logger.debug("{}, {:.3f}".format(text, score))
                # 如果包含字体信息，也打印出来
                if len(rec_result) > 3 and isinstance(rec_result[3], dict):
                    font_info = rec_result[3]
                    # 多属性字体信息打印
                    font_parts = []
                    if 'family' in font_info:
                        font_parts.append(f"Family: {font_info['family']} ({font_info.get('family_confidence', 0.0):.3f})")
                    if 'size' in font_info:
                        font_parts.append(f"Size: {font_info['size']} ({font_info.get('size_confidence', 0.0):.3f})")
                    if 'style' in font_info:
                        font_parts.append(f"Style: {font_info['style']} ({font_info.get('style_confidence', 0.0):.3f})")
                    if 'color' in font_info:
                        font_parts.append(f"Color: {font_info['color']} ({font_info.get('color_confidence', 0.0):.3f})")
                    # 兼容旧版本
                    if 'class_name' in font_info and 'family' not in font_info:
                        font_parts.append(f"Font: {font_info['class_name']} ({font_info.get('confidence', 0.0):.3f})")
                    if font_parts:
                        logger.debug("  " + ", ".join(font_parts))

            res = []
            for i in range(len(dt_boxes)):
                result_dict = {
                    "transcription": rec_res[i][0],
                    "points": np.array(dt_boxes[i]).astype(np.int32).tolist(),
                }
                # 如果包含字体信息，添加到结果中（支持多属性）
                if len(rec_res[i]) > 3 and isinstance(rec_res[i][3], dict):
                    font_info = rec_res[i][3]
                    # 添加多属性字体信息
                    if "family" in font_info:
                        result_dict["font_family"] = font_info.get("family", "unknown")
                        result_dict["font_family_confidence"] = font_info.get("family_confidence", 0.0)
                    if "size" in font_info:
                        result_dict["font_size"] = font_info.get("size", "unknown")
                        result_dict["font_size_confidence"] = font_info.get("size_confidence", 0.0)
                    if "style" in font_info:
                        result_dict["font_style"] = font_info.get("style", "unknown")
                        result_dict["font_style_confidence"] = font_info.get("style_confidence", 0.0)
                    if "color" in font_info:
                        result_dict["font_color"] = font_info.get("color", "unknown")
                        result_dict["font_color_confidence"] = font_info.get("color_confidence", 0.0)
                    # 兼容旧版本（只有class_name和confidence的情况）
                    if "class_name" in font_info and "family" not in font_info:
                        result_dict["font_family"] = font_info.get("class_name", "unknown")
                        result_dict["font_family_confidence"] = font_info.get("confidence", 0.0)
                res.append(result_dict)
            if len(imgs) > 1:
                save_pred = (
                    os.path.basename(image_file)
                    + "_"
                    + str(index)
                    + "\t"
                    + json.dumps(res, ensure_ascii=False)
                    + "\n"
                )
            else:
                save_pred = (
                    os.path.basename(image_file)
                    + "\t"
                    + json.dumps(res, ensure_ascii=False)
                    + "\n"
                )
            save_results.append(save_pred)

            if is_visualize:
                image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                boxes = dt_boxes
                txts = [rec_res[i][0] for i in range(len(rec_res))]
                scores = [rec_res[i][1] for i in range(len(rec_res))]

                draw_img = draw_ocr_box_txt(
                    image,
                    boxes,
                    txts,
                    scores,
                    drop_score=drop_score,
                    font_path=font_path,
                )
                if flag_gif:
                    save_file = image_file[:-3] + "png"
                elif flag_pdf:
                    save_file = image_file.replace(".pdf", "_" + str(index) + ".png")
                else:
                    save_file = image_file
                cv2.imwrite(
                    os.path.join(draw_img_save_dir, os.path.basename(save_file)),
                    draw_img[:, :, ::-1],
                )
                logger.debug(
                    "The visualized image saved in {}".format(
                        os.path.join(draw_img_save_dir, os.path.basename(save_file))
                    )
                )

    logger.info("The predict total time is {}".format(time.time() - _st))
    if args.benchmark:
        text_sys.text_detector.autolog.report()
        text_sys.text_recognizer.autolog.report()

    with open(
        os.path.join(draw_img_save_dir, "system_results.txt"), "w", encoding="utf-8"
    ) as f:
        f.writelines(save_results)


if __name__ == "__main__":
    args = utility.parse_args()
    if args.use_mp:
        p_list = []
        total_process_num = args.total_process_num
        for process_id in range(total_process_num):
            cmd = (
                [sys.executable, "-u"]
                + sys.argv
                + ["--process_id={}".format(process_id), "--use_mp={}".format(False)]
            )
            p = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stdout)
            p_list.append(p)
        for p in p_list:
            p.wait()
    else:
        main(args)
