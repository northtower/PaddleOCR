#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较不同OCR命令的结果
用于验证组合方案是否同时实现了完整识别和字符位置
"""

import json
import os
from pathlib import Path


def load_json_result(json_path):
    """加载JSON结果文件"""
    if not os.path.exists(json_path):
        return None
    
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_txt_result(txt_path):
    """加载TXT结果文件"""
    if not os.path.exists(txt_path):
        return None
    
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析JSON格式的TXT文件（vertical_zhtw的输出）
    if content.strip().startswith('image-'):
        lines = content.strip().split('\n')
        if lines:
            # 提取JSON部分
            json_str = lines[0].split('\t', 1)[1] if '\t' in lines[0] else '[]'
            try:
                return json.loads(json_str)
            except:
                return []
    
    return content


def extract_texts_from_structure(data):
    """从structure格式提取所有文本"""
    texts = []
    
    if isinstance(data, dict):
        # Structure格式
        if 'res' in data:
            for item in data['res']:
                if 'text' in item:
                    texts.append(item['text'])
    elif isinstance(data, list):
        # 直接是结果列表
        for item in data:
            if isinstance(item, dict) and 'text' in item:
                texts.append(item['text'])
    
    return texts


def extract_texts_from_vertical(data):
    """从vertical_zhtw格式提取所有文本"""
    texts = []
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'transcription' in item:
                texts.append(item['transcription'])
    
    return texts


def check_char_positions(data):
    """检查是否包含字符级位置信息"""
    if isinstance(data, dict) and 'res' in data:
        for item in data['res']:
            if 'text_word_region' in item or 'char_regions' in item:
                return True
    return False


def main():
    """主函数"""
    print("=" * 80)
    print("OCR结果对比分析")
    print("=" * 80)
    print()
    
    # 定义结果路径
    results = {
        "命令1(原始-structure)": {
            "path": "./output/structure/image-20/res_0.json",
            "type": "structure"
        },
        "命令2(vertical_zhtw)": {
            "path": "./output/vertical_zhtw/system_results.txt",
            "type": "vertical"
        },
        "组合方案(combined)": {
            "path": "./output/combined/structure/image-20/res_0.json",
            "type": "structure"
        }
    }
    
    # 关键测试文本
    test_texts = [
        "第二齣 俠概",
        "第二齣",
        "俠概",
        "顯祖集",
        "五一〇",
        "那得胸"
    ]
    
    # 分析每个结果
    analysis = {}
    for name, info in results.items():
        print(f"分析 {name}...")
        print(f"  路径: {info['path']}")
        
        if info['type'] == 'structure':
            data = load_json_result(info['path'])
        else:
            data = load_txt_result(info['path'])
        
        if data is None:
            print(f"  状态: ❌ 文件不存在")
            analysis[name] = {
                'exists': False,
                'texts': [],
                'has_char_pos': False
            }
            print()
            continue
        
        # 提取文本
        if info['type'] == 'structure':
            texts = extract_texts_from_structure(data)
            has_char_pos = check_char_positions(data)
        else:
            texts = extract_texts_from_vertical(data)
            has_char_pos = False
        
        analysis[name] = {
            'exists': True,
            'texts': texts,
            'has_char_pos': has_char_pos,
            'data': data
        }
        
        print(f"  状态: ✓ 成功加载")
        print(f"  识别文本数: {len(texts)}")
        print(f"  字符位置: {'✓ 支持' if has_char_pos else '✗ 不支持'}")
        print()
    
    # 对比分析
    print("=" * 80)
    print("关键文本识别对比")
    print("=" * 80)
    print()
    
    # 表头
    print(f"{'测试文本':<20} ", end='')
    for name in results.keys():
        short_name = name.split('(')[0]
        print(f"{short_name:<15} ", end='')
    print()
    print("-" * 80)
    
    # 逐行对比
    for test_text in test_texts:
        print(f"{test_text:<20} ", end='')
        
        for name in results.keys():
            if not analysis[name]['exists']:
                print(f"{'N/A':<15} ", end='')
                continue
            
            # 检查是否包含测试文本
            found = False
            for text in analysis[name]['texts']:
                if test_text in text:
                    found = True
                    break
            
            status = "✓" if found else "✗"
            print(f"{status:<15} ", end='')
        
        print()
    
    print()
    print("=" * 80)
    print("功能对比")
    print("=" * 80)
    print()
    
    # 功能对比表
    print(f"{'功能':<20} ", end='')
    for name in results.keys():
        short_name = name.split('(')[0]
        print(f"{short_name:<15} ", end='')
    print()
    print("-" * 80)
    
    # 字符位置支持
    print(f"{'字符级位置':<20} ", end='')
    for name in results.keys():
        if not analysis[name]['exists']:
            status = "N/A"
        else:
            status = "✓" if analysis[name]['has_char_pos'] else "✗"
        print(f"{status:<15} ", end='')
    print()
    
    # 识别完整性
    print(f"{'识别完整性':<20} ", end='')
    for name in results.keys():
        if not analysis[name]['exists']:
            score = "N/A"
        else:
            count = sum(1 for test_text in test_texts 
                       if any(test_text in text for text in analysis[name]['texts']))
            score = f"{count}/{len(test_texts)}"
        print(f"{score:<15} ", end='')
    print()
    
    print()
    print("=" * 80)
    print("结论")
    print("=" * 80)
    print()
    
    # 检查组合方案是否达到预期
    if '组合方案(combined)' in analysis and analysis['组合方案(combined)']['exists']:
        combined = analysis['组合方案(combined)']
        
        # 检查识别完整性
        recognition_score = sum(1 for test_text in test_texts 
                               if any(test_text in text for text in combined['texts']))
        recognition_complete = recognition_score == len(test_texts)
        
        # 检查字符位置
        has_positions = combined['has_char_pos']
        
        print(f"识别完整性: {'✓ 通过' if recognition_complete else '✗ 未通过'} ({recognition_score}/{len(test_texts)})")
        print(f"字符位置: {'✓ 支持' if has_positions else '✗ 不支持'}")
        print()
        
        if recognition_complete and has_positions:
            print("🎉 组合方案成功！同时实现了完整识别和字符位置支持！")
        elif recognition_complete:
            print("⚠️  识别完整但缺少字符位置信息")
        elif has_positions:
            print("⚠️  支持字符位置但识别不完整")
        else:
            print("❌ 两个目标都未达成")
    else:
        print("⚠️  组合方案结果文件不存在，请先运行 test_combined.bat")
    
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
