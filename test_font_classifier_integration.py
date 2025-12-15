#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试字体分类器集成
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_model_files():
    """测试模型文件是否存在"""
    print("=" * 60)
    print("测试1: 检查模型文件")
    print("=" * 60)
    
    model_path = './inference/font_classifier/font_family.pdparams'
    dict_path = './inference/font_classifier/font_family_dict.txt'
    
    model_exists = os.path.exists(model_path)
    dict_exists = os.path.exists(dict_path)
    
    print(f"模型文件 ({model_path}): {'✓ 存在' if model_exists else '✗ 不存在'}")
    print(f"字典文件 ({dict_path}): {'✓ 存在' if dict_exists else '✗ 不存在'}")
    
    if dict_exists:
        with open(dict_path, 'r', encoding='utf-8') as f:
            classes = [line.strip() for line in f if line.strip()]
        print(f"\n支持的字体类别 ({len(classes)}种):")
        for i, cls in enumerate(classes, 1):
            print(f"  {i}. {cls}")
    
    return model_exists and dict_exists


def test_font_classifier():
    """测试字体分类器类"""
    print("\n" + "=" * 60)
    print("测试2: 初始化字体分类器")
    print("=" * 60)
    
    try:
        from ppocr.utils.font_classifier import FontAttributeClassifier
        
        model_path = './inference/font_classifier/font_family.pdparams'
        dict_path = './inference/font_classifier/font_family_dict.txt'
        
        classifier = FontAttributeClassifier(
            model_path=model_path,
            dict_path=dict_path,
            use_gpu=False
        )
        
        print(f"✓ 字体分类器初始化成功")
        print(f"  - 模型路径: {model_path}")
        print(f"  - 类别数量: {classifier.num_classes}")
        print(f"  - 输入尺寸: {classifier.input_size}")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        print("\n建议安装: pip install paddleclas")
        return False
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        return False


def test_create_font_classifier():
    """测试 create_font_classifier 函数"""
    print("\n" + "=" * 60)
    print("测试3: 使用 create_font_classifier 函数")
    print("=" * 60)
    
    try:
        from ppocr.utils.font_classifier import create_font_classifier
        
        class Args:
            enable_font_classifier = True
            font_model_path = './inference/font_classifier/font_family.pdparams'
            font_dict_path = './inference/font_classifier/font_family_dict.txt'
            use_gpu = False
            enable_mkldnn = False
        
        args = Args()
        classifier = create_font_classifier(args)
        
        if classifier is not None:
            print(f"✓ 通过 create_font_classifier 创建成功")
            print(f"  - 支持类别: {classifier.num_classes}")
            return True
        else:
            print(f"✗ create_font_classifier 返回 None")
            return False
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


def test_predict_with_sample():
    """使用示例图像测试预测"""
    print("\n" + "=" * 60)
    print("测试4: 使用示例图像测试预测")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        from ppocr.utils.font_classifier import FontAttributeClassifier
        
        # 创建一个示例图像（模拟文本行）
        img = np.ones((48, 192, 3), dtype=np.uint8) * 255
        cv2.putText(img, "Test Font", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, (0, 0, 0), 2)
        
        model_path = './inference/font_classifier/font_family.pdparams'
        dict_path = './inference/font_classifier/font_family_dict.txt'
        
        classifier = FontAttributeClassifier(
            model_path=model_path,
            dict_path=dict_path,
            use_gpu=False
        )
        
        # 预测
        result = classifier.predict(img)
        
        if result is not None:
            print(f"✓ 预测成功")
            print(f"  - 字体类别: {result['class_name']}")
            print(f"  - 置信度: {result['confidence']:.4f}")
            print(f"  - 类别ID: {result['class_id']}")
            return True
        else:
            print(f"✗ 预测返回 None")
            return False
            
    except Exception as e:
        print(f"✗ 预测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_with_textsystem():
    """测试与 TextSystem 的集成"""
    print("\n" + "=" * 60)
    print("测试5: 与 TextSystem 集成测试")
    print("=" * 60)
    
    try:
        # 检查 utility.py 是否包含字体分类器参数
        utility_path = './tools/infer/utility.py'
        if not os.path.exists(utility_path):
            print(f"✗ 文件不存在: {utility_path}")
            return False
        
        with open(utility_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_params = ['enable_font_classifier', 'font_model_path', 'font_dict_path']
        all_present = all(param in content for param in required_params)
        
        if all_present:
            print(f"✓ 字体分类器参数已添加到 utility.py")
            for param in required_params:
                print(f"  - {param}: ✓")
            
            # 同样检查 ppstructure/utility.py
            ppstructure_utility = './ppstructure/utility.py'
            if os.path.exists(ppstructure_utility):
                with open(ppstructure_utility, 'r', encoding='utf-8') as f:
                    pp_content = f.read()
                pp_present = all(param in pp_content for param in required_params)
                if pp_present:
                    print(f"✓ 字体分类器参数已添加到 ppstructure/utility.py")
            
            return True
        else:
            missing = [p for p in required_params if p not in content]
            print(f"✗ 缺少参数: {missing}")
            return False
            
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n🔍 字体分类器集成测试")
    print("=" * 60)
    
    results = []
    
    # 运行测试
    results.append(("模型文件检查", test_model_files()))
    results.append(("字体分类器初始化", test_font_classifier()))
    results.append(("create_font_classifier", test_create_font_classifier()))
    results.append(("示例图像预测", test_predict_with_sample()))
    results.append(("TextSystem集成", test_integration_with_textsystem()))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name:<20s}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！字体分类器集成成功！")
        print("\n下一步：")
        print("1. 运行实际OCR测试:")
        print("   cd ppstructure")
        print("   python predict_system.py --image_dir=test.jpg --enable_font_classifier=True")
        print("\n2. 查看使用文档:")
        print("   cat FONT_CLASSIFIER_GUIDE.md")
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

