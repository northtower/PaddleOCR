#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体属性分类器
支持识别字体家族、粗细、斜体等属性
"""

import os
import sys
import numpy as np
import cv2
import paddle


class FontAttributeClassifier:
    """字体属性分类器"""
    
    def __init__(self, model_path, dict_path, use_gpu=False, enable_mkldnn=False):
        """
        初始化字体属性分类器
        
        Args:
            model_path (str): 模型文件路径（.pdparams文件）
            dict_path (str): 类别字典文件路径
            use_gpu (bool): 是否使用GPU
            enable_mkldnn (bool): 是否启用MKLDNN加速
        """
        self.model_path = model_path
        self.dict_path = dict_path
        self.use_gpu = use_gpu
        
        # 加载类别字典
        self.classes = self._load_classes()
        self.num_classes = len(self.classes)
        
        # 加载模型
        self.model = self._load_model()
        
        # 图像预处理参数
        self.input_size = (192, 48)  # (width, height)
        self.mean = np.array([0.485, 0.456, 0.406]).reshape((1, 1, 3))
        self.std = np.array([0.229, 0.224, 0.225]).reshape((1, 1, 3))
        
    def _load_classes(self):
        """加载类别字典"""
        if not os.path.exists(self.dict_path):
            raise FileNotFoundError(f"字典文件不存在: {self.dict_path}")
        
        classes = []
        with open(self.dict_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    classes.append(line)
        
        return classes
    
    def _load_model(self):
        """加载训练好的模型"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        # 动态导入PPLCNet模型
        try:
            # 尝试从ppcls导入（如果安装了paddleclas）
            from ppcls.arch.backbone.legendary_models.pp_lcnet import PPLCNet_x1_0
        except ImportError:
            # 尝试从本地PaddleClas导入
            try:
                ppclas_path = os.path.expanduser('/Users/zoutao03/codeBase/ocr/PaddleClas')
                if os.path.exists(ppclas_path) and ppclas_path not in sys.path:
                    sys.path.insert(0, ppclas_path)
                from ppcls.arch.backbone.legendary_models.pp_lcnet import PPLCNet_x1_0
            except ImportError:
                raise ImportError(
                    "需要安装paddleclas或确保本地PaddleClas目录可访问\n"
                    "1. pip install paddleclas\n"
                    "2. 或设置 PADDLECLAS_PATH 环境变量指向PaddleClas目录"
                )
        
        # 创建模型实例
        model = PPLCNet_x1_0(class_num=self.num_classes, use_last_conv=False)
        
        # 加载权重
        state_dict = paddle.load(self.model_path)
        model.set_state_dict(state_dict)
        model.eval()
        
        # 设置设备
        if self.use_gpu and paddle.is_compiled_with_cuda():
            paddle.set_device('gpu')
        else:
            paddle.set_device('cpu')
        
        return model
    
    def preprocess(self, img):
        """
        图像预处理
        
        Args:
            img (np.ndarray): BGR格式的图像，shape为(H, W, 3)
        
        Returns:
            np.ndarray: 预处理后的图像，shape为(1, 3, 48, 192)
        """
        if img is None or img.size == 0:
            return None
        
        # 调整大小
        img = cv2.resize(img, self.input_size)
        
        # BGR转RGB
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 归一化
        img = img.astype(np.float32) / 255.0
        img = (img - self.mean) / self.std
        
        # HWC -> CHW
        img = img.transpose((2, 0, 1))
        
        # 添加batch维度
        img = np.expand_dims(img, axis=0)
        
        return img.astype(np.float32)
    
    def predict(self, img_crop):
        """
        预测单张图像的字体属性
        
        Args:
            img_crop (np.ndarray): 裁剪后的文本行图像（BGR格式）
        
        Returns:
            dict: 包含预测结果的字典
                - class_id: 类别ID
                - class_name: 类别名称
                - confidence: 置信度
        """
        # 预处理
        img_tensor = self.preprocess(img_crop)
        if img_tensor is None:
            return None
        
        # 推理
        with paddle.no_grad():
            img_tensor = paddle.to_tensor(img_tensor)
            logits = self.model(img_tensor)
            probs = paddle.nn.functional.softmax(logits, axis=1)
            probs_np = probs.numpy()[0]
        
        # 获取top1结果
        class_id = int(np.argmax(probs_np))
        confidence = float(probs_np[class_id])
        class_name = self.classes[class_id]
        
        return {
            'class_id': class_id,
            'class_name': class_name,
            'confidence': confidence
        }
    
    def predict_batch(self, img_crop_list):
        """
        批量预测字体属性
        
        Args:
            img_crop_list (list): 裁剪后的文本行图像列表
        
        Returns:
            list: 预测结果列表，每个元素是一个字典
        """
        if not img_crop_list:
            return []
        
        results = []
        for img_crop in img_crop_list:
            result = self.predict(img_crop)
            results.append(result)
        
        return results


def create_font_classifier(args):
    """
    根据args创建字体分类器
    
    Args:
        args: 包含配置参数的对象
    
    Returns:
        FontAttributeClassifier: 字体分类器实例，如果不启用则返回None
    """
    if not getattr(args, 'enable_font_classifier', False):
        return None
    
    model_path = getattr(args, 'font_model_path', None)
    dict_path = getattr(args, 'font_dict_path', None)
    
    if not model_path or not dict_path:
        print("警告: 字体分类器未配置模型路径或字典路径")
        return None
    
    if not os.path.exists(model_path):
        print(f"警告: 字体模型不存在: {model_path}")
        return None
    
    if not os.path.exists(dict_path):
        print(f"警告: 字体字典不存在: {dict_path}")
        return None
    
    try:
        use_gpu = getattr(args, 'use_gpu', False)
        enable_mkldnn = getattr(args, 'enable_mkldnn', False)
        
        classifier = FontAttributeClassifier(
            model_path=model_path,
            dict_path=dict_path,
            use_gpu=use_gpu,
            enable_mkldnn=enable_mkldnn
        )
        
        print(f"字体分类器加载成功，支持 {classifier.num_classes} 种字体类别")
        return classifier
    
    except Exception as e:
        print(f"警告: 字体分类器初始化失败: {e}")
        return None

