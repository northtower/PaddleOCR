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
    """单个字体属性分类器"""
    
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
                # 尝试从环境变量获取PaddleClas路径
                ppclas_path = os.environ.get('PADDLECLAS_PATH')
                if not ppclas_path:
                    # 尝试常见路径
                    possible_paths = [
                        'C:/codeBase/ocr/PaddleClas',
                        '../PaddleClas',
                        '../../PaddleClas',
                        os.path.expanduser('~/codeBase/ocr/PaddleClas')
                    ]
                    for path in possible_paths:
                        if os.path.exists(path):
                            ppclas_path = path
                            break
                
                if ppclas_path and os.path.exists(ppclas_path) and ppclas_path not in sys.path:
                    sys.path.insert(0, ppclas_path)
                    from ppcls.arch.backbone.legendary_models.pp_lcnet import PPLCNet_x1_0
                else:
                    raise ImportError("PaddleClas path not found")
            except ImportError:
                raise ImportError(
                    "PaddleClas module not found. Please:\n"
                    "1. pip install paddleclas\n"
                    "2. OR set PADDLECLAS_PATH environment variable to PaddleClas directory"
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
    
    def predict_batch(self, img_crop_list, batch_size=64):
        """
        批量预测字体属性（真正的GPU批处理）
        
        Args:
            img_crop_list (list): 裁剪后的文本行图像列表
            batch_size (int): 批处理大小
        
        Returns:
            list: 预测结果列表，每个元素是一个字典
        """
        if not img_crop_list:
            return []
        
        # 预处理所有图像
        img_tensors = []
        valid_indices = []
        for idx, img_crop in enumerate(img_crop_list):
            img_tensor = self.preprocess(img_crop)
            if img_tensor is not None:
                img_tensors.append(img_tensor)
                valid_indices.append(idx)
        
        if not img_tensors:
            return [None] * len(img_crop_list)
        
        # 合并为批次tensor
        batch_tensor = np.concatenate(img_tensors, axis=0)
        
        # 分批推理
        all_probs = []
        with paddle.no_grad():
            for i in range(0, len(batch_tensor), batch_size):
                batch_data = batch_tensor[i:i+batch_size]
                batch_input = paddle.to_tensor(batch_data)
                logits = self.model(batch_input)
                probs = paddle.nn.functional.softmax(logits, axis=1)
                all_probs.append(probs.numpy())
        
        # 合并所有批次结果
        all_probs = np.concatenate(all_probs, axis=0)
        
        # 构建结果列表
        results = [None] * len(img_crop_list)
        for i, idx in enumerate(valid_indices):
            probs_np = all_probs[i]
            class_id = int(np.argmax(probs_np))
            confidence = float(probs_np[class_id])
            class_name = self.classes[class_id]
            
            results[idx] = {
                'class_id': class_id,
                'class_name': class_name,
                'confidence': confidence
            }
        
        return results


class MultiFontAttributeClassifier:
    """多属性字体分类器 - 支持家族、字号、样式、颜色等多个属性"""
    
    def __init__(self, use_gpu=False, enable_mkldnn=False,
                 family_model=None, family_dict=None,
                 size_model=None, size_dict=None,
                 style_model=None, style_dict=None,
                 color_model=None, color_dict=None,
                 batch_size=64):
        """
        初始化多属性字体分类器
        
        Args:
            use_gpu (bool): 是否使用GPU
            enable_mkldnn (bool): 是否启用MKLDNN加速
            family_model (str): 字体家族模型路径
            family_dict (str): 字体家族字典路径
            size_model (str): 字号模型路径
            size_dict (str): 字号字典路径
            style_model (str): 字体样式模型路径
            style_dict (str): 字体样式字典路径
            color_model (str): 字体颜色模型路径
            color_dict (str): 字体颜色字典路径
            batch_size (int): 批处理大小
        """
        self.classifiers = {}
        self.batch_size = batch_size
        
        # 加载字体家族分类器
        if family_model and family_dict and os.path.exists(family_model) and os.path.exists(family_dict):
            try:
                self.classifiers['family'] = FontAttributeClassifier(
                    family_model, family_dict, use_gpu, enable_mkldnn
                )
                print(f"[OK] Font family classifier loaded ({self.classifiers['family'].num_classes} classes)")
            except Exception as e:
                print(f"[WARN] Font family classifier failed: {e}")
        
        # 加载字号分类器
        if size_model and size_dict and os.path.exists(size_model) and os.path.exists(size_dict):
            try:
                self.classifiers['size'] = FontAttributeClassifier(
                    size_model, size_dict, use_gpu, enable_mkldnn
                )
                print(f"[OK] Font size classifier loaded ({self.classifiers['size'].num_classes} classes)")
            except Exception as e:
                print(f"[WARN] Font size classifier failed: {e}")
        
        # 加载字体样式分类器
        if style_model and style_dict and os.path.exists(style_model) and os.path.exists(style_dict):
            try:
                self.classifiers['style'] = FontAttributeClassifier(
                    style_model, style_dict, use_gpu, enable_mkldnn
                )
                print(f"[OK] Font style classifier loaded ({self.classifiers['style'].num_classes} classes)")
            except Exception as e:
                print(f"[WARN] Font style classifier failed: {e}")
        
        # 加载字体颜色分类器
        if color_model and color_dict and os.path.exists(color_model) and os.path.exists(color_dict):
            try:
                self.classifiers['color'] = FontAttributeClassifier(
                    color_model, color_dict, use_gpu, enable_mkldnn
                )
                print(f"[OK] Font color classifier loaded ({self.classifiers['color'].num_classes} classes)")
            except Exception as e:
                print(f"[WARN] Font color classifier failed: {e}")
        
        if not self.classifiers:
            raise RuntimeError("没有成功加载任何字体属性分类器")
    
    def predict(self, img_crop):
        """
        预测单张图像的所有字体属性
        
        Args:
            img_crop (np.ndarray): 裁剪后的文本行图像（BGR格式）
        
        Returns:
            dict: 包含所有属性预测结果的字典
        """
        results = {}
        
        for attr_name, classifier in self.classifiers.items():
            try:
                result = classifier.predict(img_crop)
                if result:
                    results[attr_name] = result['class_name']
                    results[f'{attr_name}_confidence'] = result['confidence']
            except Exception as e:
                print(f"[WARN] {attr_name} classification failed: {e}")
        
        return results
    
    def predict_batch(self, img_crop_list):
        """
        批量预测字体属性（GPU批处理优化）
        
        Args:
            img_crop_list (list): 裁剪后的文本行图像列表
        
        Returns:
            list: 预测结果列表，每个元素是一个字典
        """
        if not img_crop_list:
            return []
        
        # 初始化结果列表
        num_images = len(img_crop_list)
        final_results = [{} for _ in range(num_images)]
        
        # 对每个分类器进行批量预测
        for attr_name, classifier in self.classifiers.items():
            try:
                # 使用单个分类器的批量预测方法
                attr_results = classifier.predict_batch(img_crop_list, self.batch_size)
                
                # 合并结果
                for idx, result in enumerate(attr_results):
                    if result:
                        final_results[idx][attr_name] = result['class_name']
                        final_results[idx][f'{attr_name}_confidence'] = result['confidence']
            except Exception as e:
                print(f"[WARN] {attr_name} batch classification failed: {e}")
        
        return final_results


def create_font_classifier(args):
    """
    根据args创建字体分类器（支持多属性或简化模式）
    
    Args:
        args: 包含配置参数的对象
    
    Returns:
        FontAttributeClassifier or MultiFontAttributeClassifier: 字体分类器实例，如果不启用则返回None
    """
    if not getattr(args, 'enable_font_classifier', False):
        return None
    
    try:
        use_gpu = getattr(args, 'use_gpu', False)
        enable_mkldnn = getattr(args, 'enable_mkldnn', False)
        batch_size = getattr(args, 'font_classifier_batch_size', 64)
        use_simple = getattr(args, 'use_simple_font', False)
        
        # 如果使用简化模型（推荐，性能更好）
        if use_simple:
            simple_model = getattr(args, 'font_simple_model_path', None)
            simple_dict = getattr(args, 'font_simple_dict_path', None)
            
            if simple_model and simple_dict and os.path.exists(simple_model) and os.path.exists(simple_dict):
                print(f"[INFO] Using simplified font model (4 classes) for better performance")
                classifier = FontAttributeClassifier(
                    model_path=simple_model,
                    dict_path=simple_dict,
                    use_gpu=use_gpu,
                    enable_mkldnn=enable_mkldnn
                )
                # 给简化分类器添加batch_size属性
                classifier.batch_size = batch_size
                print(f"[OK] Simplified font classifier loaded ({classifier.num_classes} classes, batch_size={batch_size})")
                return classifier
            else:
                print(f"[WARN] Simplified font model not found, falling back to multi-attribute models")
        
        # 使用多属性模型
        family_model = getattr(args, 'font_family_model_path', None)
        family_dict = getattr(args, 'font_family_dict_path', None)
        size_model = getattr(args, 'font_size_model_path', None)
        size_dict = getattr(args, 'font_size_dict_path', None)
        style_model = getattr(args, 'font_style_model_path', None)
        style_dict = getattr(args, 'font_style_dict_path', None)
        color_model = getattr(args, 'font_color_model_path', None)
        color_dict = getattr(args, 'font_color_dict_path', None)
        
        # 兼容旧版本参数
        if not family_model:
            family_model = getattr(args, 'font_model_path', None)
        if not family_dict:
            family_dict = getattr(args, 'font_dict_path', None)
        
        classifier = MultiFontAttributeClassifier(
            use_gpu=use_gpu,
            enable_mkldnn=enable_mkldnn,
            family_model=family_model,
            family_dict=family_dict,
            size_model=size_model,
            size_dict=size_dict,
            style_model=style_model,
            style_dict=style_dict,
            color_model=color_model,
            color_dict=color_dict,
            batch_size=batch_size
        )
        
        print(f"[OK] Multi-attribute font classifier initialized with {len(classifier.classifiers)} classifiers (batch_size={batch_size})")
        return classifier
    
    except Exception as e:
        print(f"[WARN] Font classifier initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

