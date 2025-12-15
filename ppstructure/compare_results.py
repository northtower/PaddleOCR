#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PP-OCRv3 vs PP-OCRv5 详细对比分析脚本
"""
import json
import os
from datetime import datetime

def load_json_results(file_path):
    """加载JSON格式的OCR结果"""
    results = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results

def analyze_text_recognition(results):
    """分析文本识别结果"""
    text_items = [r for r in results if r.get('type') == 'text']
    
    if not text_items:
        return {
            'total_text_regions': 0,
            'total_text_lines': 0,
            'avg_confidence': 0.0,
            'text_content': []
        }
    
    total_lines = 0
    total_confidence = 0.0
    text_content = []
    
    for item in text_items:
        res_list = item.get('res', [])
        total_lines += len(res_list)
        
        for res in res_list:
            text = res.get('text', '')
            conf = res.get('confidence', 0.0)
            total_confidence += conf
            text_content.append({
                'text': text,
                'confidence': conf,
                'region': res.get('text_region', [])
            })
    
    avg_conf = total_confidence / total_lines if total_lines > 0 else 0.0
    
    return {
        'total_text_regions': len(text_items),
        'total_text_lines': total_lines,
        'avg_confidence': avg_conf,
        'text_content': text_content
    }

def analyze_lines(results):
    """分析线条检测结果"""
    underlines = [r for r in results if r.get('type') == 'underline']
    lines = [r for r in results if r.get('type') == 'line']
    
    return {
        'underlines': len(underlines),
        'lines': len(lines),
        'total': len(underlines) + len(lines)
    }

def compare_models(old_file, new_file):
    """对比两个模型的结果"""
    print("=" * 100)
    print("PP-OCRv3 vs PP-OCRv5 详细对比报告")
    print("=" * 100)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 加载结果
    old_results = load_json_results(old_file)
    new_results = load_json_results(new_file)
    
    # 分析文本识别
    old_text = analyze_text_recognition(old_results)
    new_text = analyze_text_recognition(new_results)
    
    # 分析线条检测
    old_lines = analyze_lines(old_results)
    new_lines = analyze_lines(new_results)
    
    # 输出对比结果
    print("【1. 文本识别对比】")
    print("-" * 100)
    print(f"{'指标':<30} {'PP-OCRv3 (旧)':<25} {'PP-OCRv5 (新)':<25} {'变化':<20}")
    print("-" * 100)
    
    # 文本区域数量
    text_regions_diff = new_text['total_text_regions'] - old_text['total_text_regions']
    text_regions_pct = (text_regions_diff / old_text['total_text_regions'] * 100) if old_text['total_text_regions'] > 0 else 0
    print(f"{'文本区域数量':<30} {old_text['total_text_regions']:<25} {new_text['total_text_regions']:<25} {text_regions_diff:+d} ({text_regions_pct:+.1f}%)")
    
    # 文本行数
    text_lines_diff = new_text['total_text_lines'] - old_text['total_text_lines']
    text_lines_pct = (text_lines_diff / old_text['total_text_lines'] * 100) if old_text['total_text_lines'] > 0 else 0
    print(f"{'识别文本行数':<30} {old_text['total_text_lines']:<25} {new_text['total_text_lines']:<25} {text_lines_diff:+d} ({text_lines_pct:+.1f}%)")
    
    # 平均置信度
    conf_diff = new_text['avg_confidence'] - old_text['avg_confidence']
    conf_pct = (conf_diff / old_text['avg_confidence'] * 100) if old_text['avg_confidence'] > 0 else 0
    print(f"{'平均识别置信度':<30} {old_text['avg_confidence']:<25.4f} {new_text['avg_confidence']:<25.4f} {conf_diff:+.4f} ({conf_pct:+.2f}%)")
    
    print()
    print("【2. 线条检测对比】")
    print("-" * 100)
    print(f"{'指标':<30} {'PP-OCRv3 (旧)':<25} {'PP-OCRv5 (新)':<25} {'变化':<20}")
    print("-" * 100)
    
    # 下划线
    underline_diff = new_lines['underlines'] - old_lines['underlines']
    print(f"{'下划线数量':<30} {old_lines['underlines']:<25} {new_lines['underlines']:<25} {underline_diff:+d}")
    
    # 线条
    line_diff = new_lines['lines'] - old_lines['lines']
    print(f"{'线条数量':<30} {old_lines['lines']:<25} {new_lines['lines']:<25} {line_diff:+d}")
    
    # 总计
    total_diff = new_lines['total'] - old_lines['total']
    print(f"{'线条总数':<30} {old_lines['total']:<25} {new_lines['total']:<25} {total_diff:+d}")
    
    print()
    print("【3. 详细文本内容对比 (前10行)】")
    print("-" * 100)
    print(f"{'序号':<6} {'旧模型文本':<40} {'置信度':<12} {'新模型文本':<40} {'置信度':<12}")
    print("-" * 100)
    
    max_lines = min(10, old_text['total_text_lines'], new_text['total_text_lines'])
    for i in range(max_lines):
        old_item = old_text['text_content'][i] if i < len(old_text['text_content']) else {'text': '', 'confidence': 0}
        new_item = new_text['text_content'][i] if i < len(new_text['text_content']) else {'text': '', 'confidence': 0}
        
        old_txt = old_item['text'][:35] + '...' if len(old_item['text']) > 35 else old_item['text']
        new_txt = new_item['text'][:35] + '...' if len(new_item['text']) > 35 else new_item['text']
        
        print(f"{i+1:<6} {old_txt:<40} {old_item['confidence']:<12.4f} {new_txt:<40} {new_item['confidence']:<12.4f}")
    
    print()
    print("【4. 综合评估】")
    print("-" * 100)
    
    # 计算综合提升幅度
    improvements = []
    
    if text_lines_pct != 0:
        improvements.append(f"文本行识别数量: {text_lines_pct:+.1f}%")
    
    if conf_pct > 0:
        improvements.append(f"识别置信度: {conf_pct:+.2f}%")
    
    if total_diff != 0:
        improvements.append(f"线条检测: {total_diff:+d}条")
    
    if improvements:
        print("✅ PP-OCRv5 相比 PP-OCRv3 的改进：")
        for imp in improvements:
            print(f"   • {imp}")
    else:
        print("⚠️  两个模型在该测试图片上表现相近")
    
    # 重点差异
    print()
    if abs(conf_pct) > 5:
        print(f"💡 关键发现：PP-OCRv5的识别置信度{'提升' if conf_pct > 0 else '下降'}了 {abs(conf_pct):.2f}%")
    
    if abs(text_lines_pct) > 2:
        print(f"💡 关键发现：PP-OCRv5{'增加' if text_lines_pct > 0 else '减少'}了 {abs(text_lines_diff)} 行文本识别")
    
    print()
    print("=" * 100)
    print("报告结束")
    print("=" * 100)

if __name__ == '__main__':
    old_file = './output/structure/image-3/res_0.txt'
    new_file = './output_ppocr_v5_test/structure/image-3/res_0.txt'
    
    if not os.path.exists(old_file):
        print(f"错误: 旧模型结果文件不存在: {old_file}")
        exit(1)
    
    if not os.path.exists(new_file):
        print(f"错误: 新模型结果文件不存在: {new_file}")
        exit(1)
    
    compare_models(old_file, new_file)

