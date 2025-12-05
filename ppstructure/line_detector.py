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

import cv2
import numpy as np


def detect_underlines(img, min_length=50, max_height=5, direction='horizontal'):
    """
    检测图像中的横线（填空题下划线）
    
    输入:
        img: 原始图像 (RGB or BGR)
        min_length: 最小线条长度（像素），默认50
        max_height: 线条最大高度（像素），用于过滤非线条区域，默认5
        direction: 检测方向，'horizontal' 或 'vertical'
    
    输出:
        线条的坐标列表 [[x1, y1, x2, y2], ...]
    """
    # 1. 转灰度并二值化
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # 使用自适应阈值处理光照不均
    # 取反(~gray)是为了让黑色线条变成白色，便于形态学处理
    binary = cv2.adaptiveThreshold(
        ~gray, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        15, -2
    )
    
    # 2. 定义线条检测的核 (Kernel)
    if direction == 'horizontal':
        # 核的宽度决定了能检测到的最短线条长度，高度设为1检测水平线
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_length, 1))
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
    else:  # vertical
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, min_length))
        dilate_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
    
    # 3. 形态学开运算：腐蚀掉文字，只保留线条
    detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    # 膨胀一下让轮廓更清晰
    detected_lines = cv2.dilate(detected_lines, dilate_kernel, iterations=1)
    
    # 4. 查找轮廓
    contours, _ = cv2.findContours(
        detected_lines, 
        cv2.RETR_EXTERNAL, 
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    line_boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        
        # 过滤掉太细碎的噪点和非线条区域
        if direction == 'horizontal':
            # 横线：宽度要足够长，高度要足够小
            if w > min_length and h <= max_height:
                line_boxes.append([x, y, x + w, y + h])
        else:  # vertical
            # 竖线：高度要足够长，宽度要足够小
            if h > min_length and w <= max_height:
                line_boxes.append([x, y, x + w, y + h])
    
    return line_boxes


def detect_all_lines(img, horizontal_min_length=50, vertical_min_length=50, 
                     max_thickness=5):
    """
    同时检测横线和竖线
    
    输入:
        img: 原始图像 (RGB or BGR)
        horizontal_min_length: 横线最小长度（像素）
        vertical_min_length: 竖线最小长度（像素）
        max_thickness: 线条最大粗细（像素）
    
    输出:
        字典，包含横线和竖线：
        {
            'horizontal': [[x1, y1, x2, y2], ...],
            'vertical': [[x1, y1, x2, y2], ...]
        }
    """
    horizontal_lines = detect_underlines(
        img, 
        min_length=horizontal_min_length, 
        max_height=max_thickness,
        direction='horizontal'
    )
    
    vertical_lines = detect_underlines(
        img, 
        min_length=vertical_min_length, 
        max_height=max_thickness,
        direction='vertical'
    )
    
    return {
        'horizontal': horizontal_lines,
        'vertical': vertical_lines
    }


def filter_lines_by_text_overlap(line_boxes, text_boxes, overlap_threshold=0.5):
    """
    过滤掉与文字区域重叠过多的线条（可能是下划线或删除线）
    
    输入:
        line_boxes: 线条坐标列表 [[x1, y1, x2, y2], ...]
        text_boxes: 文字区域坐标列表（可能是多边形或矩形）
        overlap_threshold: 重叠阈值，0-1之间
    
    输出:
        过滤后的线条列表
    """
    filtered_lines = []
    
    for line_box in line_boxes:
        lx1, ly1, lx2, ly2 = line_box
        line_area = (lx2 - lx1) * (ly2 - ly1)
        
        has_large_overlap = False
        for text_box in text_boxes:
            # text_box 可能是多边形格式（list of list）或 numpy 数组，取外接矩形
            if isinstance(text_box, np.ndarray):
                tx1, ty1 = text_box[:, 0].min(), text_box[:, 1].min()
                tx2, ty2 = text_box[:, 0].max(), text_box[:, 1].max()
            elif isinstance(text_box, list):
                if len(text_box) > 0 and isinstance(text_box[0], (list, tuple)):
                    # 多边形格式 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    xs = [pt[0] for pt in text_box]
                    ys = [pt[1] for pt in text_box]
                    tx1, ty1 = min(xs), min(ys)
                    tx2, ty2 = max(xs), max(ys)
                elif len(text_box) >= 4:
                    # 直接是矩形格式 [x1, y1, x2, y2]
                    tx1, ty1, tx2, ty2 = text_box[:4]
                else:
                    continue
            else:
                continue
            
            # 计算重叠区域
            ix1 = max(lx1, tx1)
            iy1 = max(ly1, ty1)
            ix2 = min(lx2, tx2)
            iy2 = min(ly2, ty2)
            
            if ix1 < ix2 and iy1 < iy2:
                overlap_area = (ix2 - ix1) * (iy2 - iy1)
                overlap_ratio = overlap_area / line_area if line_area > 0 else 0
                
                if overlap_ratio > overlap_threshold:
                    has_large_overlap = True
                    break
        
        if not has_large_overlap:
            filtered_lines.append(line_box)
    
    return filtered_lines

