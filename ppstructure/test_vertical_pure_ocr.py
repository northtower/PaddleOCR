"""
繁体竖排纯OCR测试脚本
不使用ppstructure的layout检测，直接使用OCR检测所有文本
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, '..')))

from tools.infer.predict_system import TextSystem
from tools.infer.utility import init_args
from ppocr.utils.logging import get_logger

logger = get_logger()


def sorted_boxes_vertical_zhtw(dt_boxes):
    """
    繁体竖排专用排序：从右向左，从上到下
    """
    num_boxes = dt_boxes.shape[0]
    if num_boxes == 0:
        return dt_boxes
    
    # 计算每个框的中心点x坐标
    sorted_boxes = sorted(dt_boxes, key=lambda x: (x[0][0] + x[2][0]) / 2, reverse=True)
    
    _boxes = []
    i = 0
    while i < len(sorted_boxes):
        # 找到同一列的所有框（x坐标接近）
        current_x = (sorted_boxes[i][0][0] + sorted_boxes[i][2][0]) / 2
        column_boxes = [(sorted_boxes[i], (sorted_boxes[i][0][1] + sorted_boxes[i][2][1]) / 2)]
        
        j = i + 1
        while j < len(sorted_boxes):
            next_x = (sorted_boxes[j][0][0] + sorted_boxes[j][2][0]) / 2
            if abs(current_x - next_x) < 50:  # 同一列的阈值
                column_boxes.append((sorted_boxes[j], (sorted_boxes[j][0][1] + sorted_boxes[j][2][1]) / 2))
                j += 1
            else:
                break
        
        # 同一列内按y坐标从小到大排序（从上到下）
        column_boxes.sort(key=lambda x: x[1])
        _boxes.extend([box[0] for box in column_boxes])
        i = j
    
    return np.array(_boxes)


def draw_ocr_result(image_path, boxes, txts, scores, output_path, font_path):
    """
    绘制OCR结果
    """
    image = Image.open(image_path).convert('RGB')
    h, w = image.height, image.width
    
    img_left = image.copy()
    img_right = Image.new('RGB', (w, h), (255, 255, 255))
    
    draw_left = ImageDraw.Draw(img_left)
    draw_right = ImageDraw.Draw(img_right)
    
    random.seed(0)
    
    for idx, (box, txt, score) in enumerate(zip(boxes, txts, scores)):
        if score < 0.5:
            continue
            
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # 左侧：半透明填充
        box_list = [tuple(point) for point in box]
        draw_left.polygon(box_list, fill=color)
        
        # 右侧：边框 + 文字
        draw_right.polygon(box_list, outline=color, width=2)
        
        # 绘制文字
        if txt:
            box_height = int(np.sqrt((box[0][0] - box[3][0]) ** 2 + (box[0][1] - box[3][1]) ** 2))
            box_width = int(np.sqrt((box[0][0] - box[1][0]) ** 2 + (box[0][1] - box[1][1]) ** 2))
            is_vertical = box_height > box_width * 1.5
            
            center_x = int((box[0][0] + box[2][0]) / 2)
            center_y = int((box[0][1] + box[2][1]) / 2)
            
            if is_vertical:
                # 竖排文字
                font_size = max(int(box_width * 0.6), 12)
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except:
                    font = ImageFont.load_default()
                
                start_y = int(box[0][1]) + 5
                x_pos = center_x - font_size // 2
                
                for char in txt:
                    if start_y > box[2][1] - font_size:
                        break
                    draw_right.text((x_pos, start_y), char, fill=(0, 0, 0), font=font)
                    start_y += font_size + 2
            else:
                # 横排文字
                font_size = max(int(box_height * 0.6), 12)
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except:
                    font = ImageFont.load_default()
                
                start_x = int(box[0][0]) + 5
                y_pos = center_y - font_size // 2
                draw_right.text((start_x, y_pos), txt, fill=(0, 0, 0), font=font)
    
    # 合并左右图像
    img_left = Image.blend(image, img_left, 0.5)
    img_show = Image.new('RGB', (w * 2, h), (255, 255, 255))
    img_show.paste(img_left, (0, 0))
    img_show.paste(img_right, (w, 0))
    
    img_show.save(output_path)
    logger.info(f"Result saved to {output_path}")


def main():
    # 初始化参数
    args = init_args()
    
    # 设置参数
    args.image_dir = "C:\\codeBase\\pdf\\pdf-parser-clib\\build\\output\\h1\\image-20.jpg"
    args.det_model_dir = "inference/ch_PP-OCRv3_det_infer"
    args.rec_model_dir = "inference/ch_PP-OCRv3_rec_infer"
    args.rec_char_dict_path = "../ppocr/utils/ppocr_keys_v1.txt"
    args.vis_font_path = "../doc/fonts/chinese_cht.ttf"
    args.use_gpu = True
    args.use_angle_cls = False
    args.show_log = True
    args.save_crop_res = False
    args.crop_res_save_dir = "./output/crop_res"
    
    # 优化检测参数
    args.det_db_thresh = 0.2
    args.det_db_box_thresh = 0.45
    args.det_db_unclip_ratio = 1.6
    args.det_limit_side_len = 1920
    
    logger.info(f"繁体竖排OCR参数: det_db_thresh={args.det_db_thresh}, det_db_box_thresh={args.det_db_box_thresh}, det_db_unclip_ratio={args.det_db_unclip_ratio}, det_limit_side_len={args.det_limit_side_len}")
    
    # 初始化文本系统
    text_system = TextSystem(args)
    
    # 读取图像
    img = cv2.imread(args.image_dir)
    if img is None:
        logger.error(f"Cannot read image: {args.image_dir}")
        return
    
    logger.info(f"Processing image: {args.image_dir}")
    logger.info(f"Image shape: {img.shape}")
    
    # 进行OCR识别
    dt_boxes, rec_res, time_dict = text_system(img)
    
    logger.info(f"Detected {len(dt_boxes)} text boxes")
    
    if len(dt_boxes) == 0:
        logger.warning("No text detected!")
        return
    
    # 繁体竖排排序
    dt_boxes = sorted_boxes_vertical_zhtw(np.array(dt_boxes))
    
    # 提取文本和分数
    txts = [rec[0] for rec in rec_res]
    scores = [rec[1] for rec in rec_res]
    
    # 保存结果
    output_dir = "./output/vertical_zhtw_pure/"
    os.makedirs(output_dir, exist_ok=True)
    
    output_img = os.path.join(output_dir, "show_0.jpg")
    draw_ocr_result(args.image_dir, dt_boxes, txts, scores, output_img, args.vis_font_path)
    
    # 保存文本结果
    output_txt = os.path.join(output_dir, "res_0.txt")
    with open(output_txt, 'w', encoding='utf-8') as f:
        for box, txt, score in zip(dt_boxes, txts, scores):
            f.write(f"{txt}\t{score:.4f}\t{box.tolist()}\n")
    
    logger.info(f"Text results saved to {output_txt}")
    logger.info(f"Total time: {sum(time_dict.values()):.3f}s")


if __name__ == "__main__":
    main()

