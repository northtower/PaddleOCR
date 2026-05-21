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

"""
繁体竖排文本识别专用脚本
解决三个核心问题：
1. 语序错误：繁体竖排从右向左，修正排序逻辑
2. 繁体字识别错误：使用更好的繁体字典
3. show_0.jpg 可视化错误：修正竖排文字显示
"""

import os
import sys
import subprocess

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, "../")))

os.environ["FLAGS_allocator_strategy"] = "auto_growth"
import cv2
import json
import numpy as np
import time
import logging
import math
import random
from copy import deepcopy
from PIL import Image, ImageDraw, ImageFont
import PIL

from paddle.utils import try_import
from ppocr.utils.utility import get_image_file_list, check_and_read
from ppocr.utils.logging import get_logger
from ppocr.utils.visual import draw_ser_results, draw_re_results
from tools.infer.predict_system import TextSystem
from tools.infer.predict_rec import TextRecognizer
from ppstructure.layout.predict_layout import LayoutPredictor
from ppstructure.table.predict_table import TableSystem, to_excel
from ppstructure.utility import parse_args, cal_ocr_word_box
from ppstructure.line_detector import detect_all_lines, filter_lines_by_text_overlap

logger = get_logger()


def sorted_boxes_vertical_zhtw(dt_boxes):
    """
    繁体竖排专用排序：从右向左，从上到下
    args:
        dt_boxes(array): detected text boxes with shape [4, 2]
    return:
        sorted boxes(array): 从右向左排序的文本框
    """
    num_boxes = len(dt_boxes)
    if num_boxes == 0:
        return dt_boxes
    
    # 计算每个文本框的中心点 x 坐标（用于从右向左排序）
    boxes_with_x = []
    for box in dt_boxes:
        if isinstance(box, np.ndarray):
            box = box.tolist()
        # 计算中心点 x 坐标
        center_x = sum([p[0] for p in box]) / len(box)
        center_y = sum([p[1] for p in box]) / len(box)
        boxes_with_x.append((box, center_x, center_y))
    
    # 按 x 坐标从大到小排序（从右向左）
    # 对于 y 坐标相近的框，按 x 从大到小排序
    sorted_boxes = sorted(boxes_with_x, key=lambda x: (-x[1], x[2]))
    
    # 精细调整：同一列的框按 y 坐标排序
    _boxes = []
    i = 0
    while i < num_boxes:
        current_box = sorted_boxes[i]
        column_boxes = [current_box]
        j = i + 1
        
        # 找出同一列的所有框（x 坐标相近）
        while j < num_boxes:
            next_box = sorted_boxes[j]
            # 如果 x 坐标差距小于 50 像素，认为是同一列
            if abs(current_box[1] - next_box[1]) < 50:
                column_boxes.append(next_box)
                j += 1
            else:
                break
        
        # 同一列内按 y 坐标从小到大排序（从上到下）
        column_boxes.sort(key=lambda x: x[2])
        _boxes.extend([box[0] for box in column_boxes])
        i = j
    
    return _boxes


def draw_box_txt_fine_vertical(img_size, box, txt, font_path="./doc/fonts/simfang.ttf"):
    """
    针对竖排文字优化的绘制函数
    简化版本：直接在原图上绘制文字，不使用透视变换
    """
    box_height = int(
        math.sqrt((box[0][0] - box[3][0]) ** 2 + (box[0][1] - box[3][1]) ** 2)
    )
    box_width = int(
        math.sqrt((box[0][0] - box[1][0]) ** 2 + (box[0][1] - box[1][1]) ** 2)
    )

    # 创建空白图像
    img_right_text = np.ones((img_size[1], img_size[0], 3), dtype=np.uint8) * 255
    
    if txt and len(txt) > 0:
        # 判断是否为竖排文字（高度 > 宽度）
        is_vertical = box_height > box_width * 1.5
        
        # 计算文本框的中心点和角度
        center_x = int((box[0][0] + box[2][0]) / 2)
        center_y = int((box[0][1] + box[2][1]) / 2)
        
        # 转换为PIL图像以便绘制文字
        img_pil = Image.fromarray(img_right_text)
        draw = ImageDraw.Draw(img_pil)
        
        if is_vertical:
            # 竖排文字：逐字垂直绘制
            font_size = max(int(box_width * 0.7), 12)
            try:
                font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
            except:
                font = ImageFont.load_default()
            
            # 计算起始位置（从上到下）
            start_y = int(box[0][1]) + 5
            x_pos = center_x - font_size // 2
            
            for char in txt:
                if start_y > box[2][1] - font_size:
                    break
                draw.text((x_pos, start_y), char, fill=(0, 0, 0), font=font)
                start_y += font_size + 2
        else:
            # 横排文字
            font_size = max(int(box_height * 0.7), 12)
            try:
                font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
            except:
                font = ImageFont.load_default()
            
            # 计算文字位置
            start_x = int(box[0][0]) + 5
            y_pos = center_y - font_size // 2
            draw.text((start_x, y_pos), txt, fill=(0, 0, 0), font=font)
        
        img_right_text = np.array(img_pil)
    
    return img_right_text


def draw_ocr_box_txt_vertical(
    image,
    boxes,
    txts=None,
    scores=None,
    drop_score=0.5,
    font_path="./doc/fonts/simfang.ttf",
):
    """
    针对竖排文字优化的可视化函数
    """
    h, w = image.height, image.width
    img_left = image.copy()
    img_right = np.ones((h, w, 3), dtype=np.uint8) * 255
    random.seed(0)

    draw_left = ImageDraw.Draw(img_left)
    if txts is None or len(txts) != len(boxes):
        txts = [None] * len(boxes)
    for idx, (box, txt) in enumerate(zip(boxes, txts)):
        if scores is not None and scores[idx] < drop_score:
            continue
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # 绘制左侧：半透明填充的文本框
        draw_left.polygon(box, fill=color)
        
        # 绘制右侧：文本框边框 + 文字内容
        # 先绘制边框
        pts = np.array(box, np.int32).reshape((-1, 1, 2))
        cv2.polylines(img_right, [pts], True, color, 2)
        
        # 再绘制文字（使用竖排优化的绘制函数）
        img_right_text = draw_box_txt_fine_vertical((w, h), box, txt, font_path)
        
        # 将文字叠加到右侧图像上（只保留非白色部分）
        mask = np.all(img_right_text == [255, 255, 255], axis=-1)
        img_right[~mask] = img_right_text[~mask]
        
    img_left = Image.blend(image, img_left, 0.5)
    img_show = Image.new("RGB", (w * 2, h), (255, 255, 255))
    img_show.paste(img_left, (0, 0, w, h))
    img_show.paste(Image.fromarray(img_right), (w, 0, w * 2, h))
    return np.array(img_show)


def draw_structure_result_vertical(image, result, font_path):
    """
    针对竖排文字优化的结构化结果绘制函数
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    boxes, txts, scores = [], [], []

    img_layout = image.copy()
    draw_layout = ImageDraw.Draw(img_layout)
    text_color = (255, 255, 255)
    text_background_color = (80, 127, 255)
    catid2color = {}
    font_size = 15
    try:
        font = ImageFont.truetype(font_path, font_size, encoding="utf-8")
    except:
        font = ImageFont.load_default()

    for region in result:
        if region["type"] not in catid2color:
            if region["type"] in ["underline", "line"]:
                box_color = (255, 0, 0)
            else:
                box_color = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
            catid2color[region["type"]] = box_color
        else:
            box_color = catid2color[region["type"]]
        box_layout = region["bbox"]
        
        line_width = 5 if region["type"] in ["underline", "line"] else 3
        draw_layout.rectangle(
            [(box_layout[0], box_layout[1]), (box_layout[2], box_layout[3])],
            outline=box_color,
            width=line_width,
        )

        label_text = region["type"]
        if region["type"] in ["underline", "line"] and "direction" in region:
            label_text = f"{region['type']}({region['direction']})"
        
        if int(PIL.__version__.split(".")[0]) < 10:
            text_w, text_h = font.getsize(label_text)
        else:
            left, top, right, bottom = font.getbbox(label_text)
            text_w, text_h = right - left, bottom - top

        draw_layout.rectangle(
            [
                (box_layout[0], box_layout[1]),
                (box_layout[0] + text_w, box_layout[1] + text_h),
            ],
            fill=text_background_color,
        )
        draw_layout.text(
            (box_layout[0], box_layout[1]), label_text, fill=text_color, font=font
        )

        if region["type"] == "table" or (
            region["type"] == "equation" and "latex" in region["res"]
        ):
            pass
        elif region["type"] in ["underline", "line"]:
            pass
        else:
            for text_result in region["res"]:
                text_region = text_result.get("region") or text_result.get("text_region")
                if text_region:
                    boxes.append(np.array(text_region))
                    txts.append(text_result["text"])
                    scores.append(text_result["confidence"])

                if "text_word_region" in text_result:
                    for word_region in text_result["text_word_region"]:
                        char_box = word_region
                        box_height = int(
                            math.sqrt(
                                (char_box[0][0] - char_box[3][0]) ** 2
                                + (char_box[0][1] - char_box[3][1]) ** 2
                            )
                        )
                        box_width = int(
                            math.sqrt(
                                (char_box[0][0] - char_box[1][0]) ** 2
                                + (char_box[0][1] - char_box[1][1]) ** 2
                            )
                        )
                        if box_height == 0 or box_width == 0:
                            continue
                        boxes.append(word_region)
                        txts.append("")
                        scores.append(1.0)

    # 使用竖排优化的可视化函数
    im_show = draw_ocr_box_txt_vertical(
        img_layout, boxes, txts, scores, font_path=font_path
    )
    return im_show


class StructureSystemVerticalZHTW(object):
    """
    繁体竖排专用的结构化系统
    """
    def __init__(self, args):
        self.mode = args.mode
        self.recovery = args.recovery

        self.image_orientation_predictor = None
        if args.image_orientation:
            import paddleclas
            self.image_orientation_predictor = paddleclas.PaddleClas(
                model_name="text_image_orientation"
            )

        self.enable_line_detection = getattr(args, 'enable_line_detection', False)
        self.line_min_length = getattr(args, 'line_min_length', 50)
        self.line_max_thickness = getattr(args, 'line_max_thickness', 5)
        self.filter_line_text_overlap = getattr(args, 'filter_line_text_overlap', True)

        if self.mode == "structure":
            if not args.show_log:
                logger.setLevel(logging.INFO)
            if args.layout == False and args.ocr == True:
                args.ocr = False
                logger.warning(
                    "When args.layout is false, args.ocr is automatically set to false"
                )
            
            self.layout_predictor = None
            self.text_system = None
            self.table_system = None
            self.formula_system = None
            
            if args.layout:
                self.layout_predictor = LayoutPredictor(args)
                if args.ocr:
                    self.text_system = TextSystem(args)
            if args.table:
                if self.text_system is not None:
                    self.table_system = TableSystem(
                        args,
                        self.text_system.text_detector,
                        self.text_system.text_recognizer,
                    )
                else:
                    self.table_system = TableSystem(args)
            if args.formula:
                args_formula = deepcopy(args)
                args_formula.rec_algorithm = args.formula_algorithm
                args_formula.rec_model_dir = args.formula_model_dir
                args_formula.rec_char_dict_path = args.formula_char_dict_path
                args_formula.rec_batch_num = args.formula_batch_num
                self.formula_system = TextRecognizer(args_formula)

        elif self.mode == "kie":
            from ppstructure.kie.predict_kie_token_ser_re import SerRePredictor
            self.kie_predictor = SerRePredictor(args)

        self.return_word_box = args.return_word_box

    def __call__(self, img, return_ocr_result_in_table=False, img_idx=0):
        time_dict = {
            "image_orientation": 0,
            "layout": 0,
            "table": 0,
            "table_match": 0,
            "formula": 0,
            "det": 0,
            "rec": 0,
            "kie": 0,
            "all": 0,
        }
        start = time.time()

        if self.image_orientation_predictor is not None:
            tic = time.time()
            cls_result = self.image_orientation_predictor.predict(input_data=img)
            cls_res = next(cls_result)
            angle = cls_res[0]["label_names"][0]
            cv_rotate_code = {
                "90": cv2.ROTATE_90_COUNTERCLOCKWISE,
                "180": cv2.ROTATE_180,
                "270": cv2.ROTATE_90_CLOCKWISE,
            }
            if angle in cv_rotate_code:
                img = cv2.rotate(img, cv_rotate_code[angle])
            toc = time.time()
            time_dict["image_orientation"] = toc - tic

        if self.mode == "structure":
            ori_im = img.copy()
            if self.layout_predictor is not None:
                layout_res, elapse = self.layout_predictor(img)
                time_dict["layout"] += elapse
            else:
                h, w = ori_im.shape[:2]
                layout_res = [dict(bbox=None, label="table", score=0.0)]

            text_res = None
            if self.text_system is not None:
                text_res, ocr_time_dict = self._predict_text(img)
                time_dict["det"] += ocr_time_dict["det"]
                time_dict["rec"] += ocr_time_dict["rec"]

            res_list = []
            for region in layout_res:
                res = ""
                if region["bbox"] is not None:
                    x1, y1, x2, y2 = region["bbox"]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    roi_img = ori_im[y1:y2, x1:x2, :]
                else:
                    x1, y1, x2, y2 = 0, 0, w, h
                    roi_img = ori_im
                bbox = [x1, y1, x2, y2]

                if region["label"] == "table":
                    if self.table_system is not None:
                        res, table_time_dict = self.table_system(
                            roi_img, return_ocr_result_in_table
                        )
                        time_dict["table"] += table_time_dict["table"]
                        time_dict["table_match"] += table_time_dict["match"]
                        time_dict["det"] += table_time_dict["det"]
                        time_dict["rec"] += table_time_dict["rec"]

                elif region["label"] == "equation" and self.formula_system is not None:
                    latex_res, formula_time = self.formula_system([roi_img])
                    time_dict["formula"] += formula_time
                    res = {"latex": latex_res[0]}

                else:
                    if text_res is not None:
                        res = self._filter_text_res(text_res, bbox)

                res_list.append(
                    {
                        "type": region["label"].lower(),
                        "bbox": bbox,
                        "img": roi_img,
                        "res": res,
                        "img_idx": img_idx,
                        "score": region["score"],
                    }
                )

            if self.enable_line_detection:
                tic = time.time()
                line_results = detect_all_lines(
                    ori_im, 
                    horizontal_min_length=self.line_min_length,
                    vertical_min_length=self.line_min_length,
                    max_thickness=self.line_max_thickness
                )
                
                if self.filter_line_text_overlap and text_res is not None:
                    text_boxes = [r["text_region"] for r in text_res]
                    line_results['horizontal'] = filter_lines_by_text_overlap(
                        line_results['horizontal'], text_boxes
                    )
                    line_results['vertical'] = filter_lines_by_text_overlap(
                        line_results['vertical'], text_boxes
                    )
                
                for line_box in line_results['horizontal']:
                    x1, y1, x2, y2 = line_box
                    roi_img = ori_im[y1:y2, x1:x2, :]
                    res_list.append({
                        'type': 'underline',
                        'bbox': line_box,
                        'img': roi_img,
                        'res': None,
                        'img_idx': img_idx,
                        'score': 1.0,
                        'direction': 'horizontal'
                    })
                
                for line_box in line_results['vertical']:
                    x1, y1, x2, y2 = line_box
                    roi_img = ori_im[y1:y2, x1:x2, :]
                    res_list.append({
                        'type': 'line',
                        'bbox': line_box,
                        'img': roi_img,
                        'res': None,
                        'img_idx': img_idx,
                        'score': 1.0,
                        'direction': 'vertical'
                    })
                
                toc = time.time()
                time_dict["line_detection"] = toc - tic

            end = time.time()
            time_dict["all"] = end - start
            return res_list, time_dict

        elif self.mode == "kie":
            re_res, elapse = self.kie_predictor(img)
            time_dict["kie"] = elapse
            time_dict["all"] = elapse
            return re_res[0], time_dict

        return None, None

    def _predict_text(self, img):
        """
        使用繁体竖排优化的文本预测
        """
        filter_boxes, filter_rec_res, ocr_time_dict = self.text_system(img)

        # 关键修改：使用繁体竖排排序
        sorted_boxes_list = sorted_boxes_vertical_zhtw(filter_boxes)
        
        # 根据排序后的顺序重新排列 rec_res
        # 创建原始 boxes 的索引映射
        box_to_idx = {}
        for idx, box in enumerate(filter_boxes):
            box_tuple = tuple(map(tuple, box.tolist() if isinstance(box, np.ndarray) else box))
            box_to_idx[box_tuple] = idx
        
        # 根据排序后的 boxes 重新排列 rec_res
        sorted_rec_res = []
        for sorted_box in sorted_boxes_list:
            box_tuple = tuple(map(tuple, sorted_box if isinstance(sorted_box, list) else sorted_box.tolist()))
            if box_tuple in box_to_idx:
                sorted_rec_res.append(filter_rec_res[box_to_idx[box_tuple]])
        
        filter_boxes = sorted_boxes_list
        filter_rec_res = sorted_rec_res

        style_token = [
            "<strike>", "<strike>", "<sup>", "</sub>", "<b>", "</b>",
            "<sub>", "</sup>", "<overline>", "</overline>",
            "<underline>", "</underline>", "<i>", "</i>",
        ]
        
        res = []
        for box, rec_res in zip(filter_boxes, filter_rec_res):
            rec_str, rec_conf = rec_res[0], rec_res[1]
            for token in style_token:
                if token in rec_str:
                    rec_str = rec_str.replace(token, "")
            
            char_font_attrs = None
            if len(rec_res) > 3 and isinstance(rec_res[3], list):
                char_font_attrs = rec_res[3]
            
            if self.return_word_box:
                # 确保 box 是 numpy array
                box_array = np.array(box) if not isinstance(box, np.ndarray) else box
                word_box_content_list, word_box_list = cal_ocr_word_box(
                    rec_str, box_array, rec_res[2]
                )
                
                runs = []
                if char_font_attrs and len(char_font_attrs) > 0:
                    runs = self._build_runs(word_box_content_list, word_box_list, char_font_attrs)
                else:
                    runs = [{
                        "text": "".join(word_box_content_list),
                        "chars": word_box_content_list,
                        "char_regions": word_box_list,
                    }]
                
                result_dict = {
                    "text": rec_str,
                    "confidence": float(rec_conf),
                    "region": box.tolist() if isinstance(box, np.ndarray) else box,
                    "runs": runs,
                }
                
                if getattr(self, 'return_word_box', True):
                    result_dict["text_word"] = word_box_content_list
                    result_dict["text_word_region"] = word_box_list
                
                res.append(result_dict)
            else:
                result_dict = {
                    "text": rec_str,
                    "confidence": float(rec_conf),
                    "region": box.tolist() if isinstance(box, np.ndarray) else box,
                }
                
                if char_font_attrs and len(char_font_attrs) > 0:
                    first_attr = char_font_attrs[0]
                    result_dict["runs"] = [{
                        "text": rec_str,
                        "region": box.tolist() if isinstance(box, np.ndarray) else box,
                        "properties": {
                            "font_family": first_attr.get("family", "unknown"),
                            "font_size": first_attr.get("size", "unknown"),
                            "font_style": first_attr.get("style", "unknown"),
                            "font_color": first_attr.get("color", "unknown")
                        }
                    }]
                
                res.append(result_dict)
        return res, ocr_time_dict
    
    def _build_runs(self, chars, char_regions, char_font_attrs):
        if not chars or not char_font_attrs:
            return []
        
        runs = []
        current_run = {
            "text": "",
            "region": None,
            "properties": {}
        }
        current_run_regions = []
        current_attrs = None
        
        for idx, (char, region, attrs) in enumerate(zip(chars, char_regions, char_font_attrs)):
            key_attrs = None
            if attrs:
                if "family" in attrs:
                    key_attrs = (
                        attrs.get("family", ""),
                        attrs.get("size", ""),
                        attrs.get("style", ""),
                        attrs.get("color", "")
                    )
                elif "class_name" in attrs:
                    key_attrs = (attrs.get("class_name", ""), "", "", "")
            
            if current_attrs is None or current_attrs == key_attrs:
                current_run["text"] += char
                current_run_regions.append(region)
                current_attrs = key_attrs
                
                if attrs and not current_run["properties"]:
                    if "family" in attrs:
                        current_run["properties"] = {
                            "font_family": attrs.get("family", "unknown"),
                            "font_size": attrs.get("size", "unknown"),
                            "font_style": attrs.get("style", "unknown"),
                            "font_color": attrs.get("color", "unknown")
                        }
                    elif "class_name" in attrs:
                        current_run["properties"] = {
                            "font_family": attrs.get("class_name", "unknown"),
                            "font_confidence": attrs.get("confidence", 0.0)
                        }
            else:
                if current_run["text"]:
                    current_run["region"] = self._merge_regions(current_run_regions)
                    runs.append(current_run)
                
                current_run = {
                    "text": char,
                    "region": None,
                    "properties": {}
                }
                current_run_regions = [region]
                current_attrs = key_attrs
                
                if attrs:
                    if "family" in attrs:
                        current_run["properties"] = {
                            "font_family": attrs.get("family", "unknown"),
                            "font_size": attrs.get("size", "unknown"),
                            "font_style": attrs.get("style", "unknown"),
                            "font_color": attrs.get("color", "unknown")
                        }
                    elif "class_name" in attrs:
                        current_run["properties"] = {
                            "font_family": attrs.get("class_name", "unknown"),
                            "font_confidence": attrs.get("confidence", 0.0)
                        }
        
        if current_run["text"]:
            current_run["region"] = self._merge_regions(current_run_regions)
            runs.append(current_run)
        
        return runs
    
    def _merge_regions(self, regions):
        if not regions:
            return [[0, 0], [0, 0], [0, 0], [0, 0]]
        
        if len(regions) == 1:
            return regions[0]
        
        all_x = []
        all_y = []
        for region in regions:
            for point in region:
                all_x.append(point[0])
                all_y.append(point[1])
        
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        
        return [
            [x_min, y_min],
            [x_max, y_min],
            [x_max, y_max],
            [x_min, y_max]
        ]

    def _filter_text_res(self, text_res, bbox):
        res = []
        for r in text_res:
            box = r.get("region") or r.get("text_region")
            if box:
                rect = box[0][0], box[0][1], box[2][0], box[2][1]
                if self._has_intersection(bbox, rect):
                    res.append(r)
        return res

    def _has_intersection(self, rect1, rect2):
        x_min1, y_min1, x_max1, y_max1 = rect1
        x_min2, y_min2, x_max2, y_max2 = rect2
        if x_min1 > x_max2 or x_max1 < x_min2:
            return False
        if y_min1 > y_max2 or y_max1 < y_min2:
            return False
        return True


def save_structure_res(res, save_folder, img_name, img_idx=0):
    excel_save_folder = os.path.join(save_folder, img_name)
    os.makedirs(excel_save_folder, exist_ok=True)
    res_cp = deepcopy(res)
    
    with open(
        os.path.join(excel_save_folder, "res_{}.txt".format(img_idx)),
        "w",
        encoding="utf8",
    ) as f:
        for region in res_cp:
            roi_img = region.pop("img")
            f.write("{}\n".format(json.dumps(region, ensure_ascii=False)))

            if (
                region["type"].lower() == "table"
                and len(region["res"]) > 0
                and "html" in region["res"]
            ):
                excel_path = os.path.join(
                    excel_save_folder, "{}_{}.xlsx".format(region["bbox"], img_idx)
                )
                to_excel(region["res"]["html"], excel_path)
            elif region["type"].lower() == "figure":
                img_path = os.path.join(
                    excel_save_folder, "{}_{}.jpg".format(region["bbox"], img_idx)
                )
                cv2.imwrite(img_path, roi_img)


def main(args):
    image_file_list = get_image_file_list(args.image_dir)
    image_file_list = image_file_list[args.process_id :: args.total_process_num]

    if not args.use_pdf2docx_api:
        structure_sys = StructureSystemVerticalZHTW(args)
        save_folder = os.path.join(args.output, structure_sys.mode)
        os.makedirs(save_folder, exist_ok=True)
    img_num = len(image_file_list)

    for i, image_file in enumerate(image_file_list):
        logger.info("[{}/{}] {}".format(i, img_num, image_file))
        img, flag_gif, flag_pdf = check_and_read(image_file)
        img_name = os.path.basename(image_file).split(".")[0]

        if args.recovery and args.use_pdf2docx_api and flag_pdf:
            try_import("pdf2docx")
            from pdf2docx.converter import Converter

            os.makedirs(args.output, exist_ok=True)
            docx_file = os.path.join(args.output, "{}_api.docx".format(img_name))
            cv = Converter(image_file)
            cv.convert(docx_file)
            cv.close()
            logger.info("docx save to {}".format(docx_file))
            continue

        if not flag_gif and not flag_pdf:
            img = cv2.imread(image_file)

        if not flag_pdf:
            if img is None:
                logger.error("error in loading image:{}".format(image_file))
                continue
            imgs = [img]
        else:
            imgs = img

        all_res = []
        for index, img in enumerate(imgs):
            res, time_dict = structure_sys(img, img_idx=index)
            img_save_path = os.path.join(
                save_folder, img_name, "show_{}.jpg".format(index)
            )
            os.makedirs(os.path.join(save_folder, img_name), exist_ok=True)
            if structure_sys.mode == "structure" and res != []:
                # 使用竖排优化的绘制函数
                draw_img = draw_structure_result_vertical(img, res, args.vis_font_path)
                save_structure_res(res, save_folder, img_name, index)
            elif structure_sys.mode == "kie":
                if structure_sys.kie_predictor.predictor is not None:
                    draw_img = draw_re_results(img, res, font_path=args.vis_font_path)
                else:
                    draw_img = draw_ser_results(img, res, font_path=args.vis_font_path)

                with open(
                    os.path.join(save_folder, img_name, "res_{}_kie.txt".format(index)),
                    "w",
                    encoding="utf8",
                ) as f:
                    res_str = "{}\t{}\n".format(
                        image_file, json.dumps({"ocr_info": res}, ensure_ascii=False)
                    )
                    f.write(res_str)
            if res != []:
                cv2.imwrite(img_save_path, draw_img)
                logger.info("result save to {}".format(img_save_path))
            if args.recovery and res != []:
                from ppstructure.recovery.recovery_to_doc import (
                    sorted_layout_boxes,
                    convert_info_docx,
                )
                from ppstructure.recovery.recovery_to_markdown import (
                    convert_info_markdown,
                )

                h, w, _ = img.shape
                res = sorted_layout_boxes(res, w)
                all_res += res

        if args.recovery and all_res != []:
            try:
                convert_info_docx(img, all_res, save_folder, img_name)
                if args.recovery_to_markdown:
                    convert_info_markdown(all_res, save_folder, img_name)
            except Exception as ex:
                logger.error(
                    "error in layout recovery image:{}, err msg: {}".format(
                        image_file, ex
                    )
                )
                continue
        logger.info("Predict time : {:.3f}s".format(time_dict["all"]))


if __name__ == "__main__":
    args = parse_args()
    
    # 针对繁体竖排优化检测参数
    # 关键：禁用layout检测，直接进行文本检测，避免整个区域被当作figure
    args.layout = False  # 禁用layout检测
    
    # 降低阈值以检测更多文本
    args.det_db_thresh = 0.2  # 从0.3降低到0.2，更容易检测小文本
    args.det_db_box_thresh = 0.45  # 从0.6降低到0.45，降低框过滤阈值
    args.det_db_unclip_ratio = 1.6  # 从1.5增加到1.6，适度扩大检测框
    args.det_limit_side_len = 1920  # 从960增加到1920，保持更高分辨率
    
    logger.info(f"繁体竖排优化参数: layout={args.layout}, det_db_thresh={args.det_db_thresh}, det_db_box_thresh={args.det_db_box_thresh}, det_db_unclip_ratio={args.det_db_unclip_ratio}, det_limit_side_len={args.det_limit_side_len}")
    
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

