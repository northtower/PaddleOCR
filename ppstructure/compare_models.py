#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型对比测试脚本
对比 PP-OCRv3 和 PP-OCRv5 在同一图片上的识别效果
"""

import os
import sys
import json
import time
import cv2
import numpy as np
from pathlib import Path

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, "../")))

# 设置环境变量
os.environ["FLAGS_allocator_strategy"] = "auto_growth"

from ppocr.utils.utility import get_image_file_list, check_and_read
from ppocr.utils.logging import get_logger
from ppstructure.utility import parse_args
from ppstructure.predict_system import StructureSystem

logger = get_logger()


def test_old_model(image_path, args):
    """测试旧模型 PP-OCRv3"""
    logger.info("=" * 80)
    logger.info("开始测试旧模型 PP-OCRv3")
    logger.info("=" * 80)
    
    # 配置旧模型参数
    args.det_model_dir = "inference/ch_PP-OCRv3_det_infer"
    args.rec_model_dir = "inference/ch_PP-OCRv3_rec_infer"
    args.table_model_dir = "inference/ch_ppstructure_mobile_v2.0_SLANet_infer"
    
    # 初始化系统
    start_init = time.time()
    structure_sys = StructureSystem(args)
    init_time = time.time() - start_init
    
    # 读取图像
    img, flag_gif, flag_pdf = check_and_read(image_path)
    if not flag_gif and not flag_pdf:
        img = cv2.imread(image_path)
    
    # 预测
    start_pred = time.time()
    res, time_dict = structure_sys(img, img_idx=0)
    pred_time = time.time() - start_pred
    
    return {
        "model_version": "PP-OCRv3",
        "init_time": init_time,
        "pred_time": pred_time,
        "time_dict": time_dict,
        "results": res
    }


def test_new_model(image_path, args):
    """测试新模型 PP-OCRv5"""
    logger.info("=" * 80)
    logger.info("开始测试新模型 PP-OCRv5")
    logger.info("=" * 80)
    
    # 配置新模型参数
    args.det_model_dir = "inference/new-version/PP-OCRv5_server_det_infer"
    args.rec_model_dir = "inference/new-version/PP-OCRv5_server_rec_infer"
    args.table_model_dir = "inference/new-version/SLANeXt_wired_infer"
    
    # 初始化系统
    start_init = time.time()
    structure_sys = StructureSystem(args)
    init_time = time.time() - start_init
    
    # 读取图像
    img, flag_gif, flag_pdf = check_and_read(image_path)
    if not flag_gif and not flag_pdf:
        img = cv2.imread(image_path)
    
    # 预测
    start_pred = time.time()
    res, time_dict = structure_sys(img, img_idx=0)
    pred_time = time.time() - start_pred
    
    return {
        "model_version": "PP-OCRv5",
        "init_time": init_time,
        "pred_time": pred_time,
        "time_dict": time_dict,
        "results": res
    }


def compare_text_results(old_results, new_results):
    """比较文本识别结果"""
    old_texts = []
    new_texts = []
    
    # 提取旧模型文本
    for item in old_results:
        if item.get("type") == "text" and isinstance(item.get("res"), list):
            for text_item in item["res"]:
                if "text" in text_item:
                    old_texts.append({
                        "text": text_item["text"],
                        "confidence": text_item.get("confidence", 0),
                        "bbox": text_item.get("text_region", [])
                    })
    
    # 提取新模型文本
    for item in new_results:
        if item.get("type") == "text" and isinstance(item.get("res"), list):
            for text_item in item["res"]:
                if "text" in text_item:
                    new_texts.append({
                        "text": text_item["text"],
                        "confidence": text_item.get("confidence", 0),
                        "bbox": text_item.get("text_region", [])
                    })
    
    return old_texts, new_texts


def calculate_metrics(old_texts, new_texts):
    """计算评估指标"""
    metrics = {}
    
    # 文本数量
    metrics["old_text_count"] = len(old_texts)
    metrics["new_text_count"] = len(new_texts)
    
    # 平均置信度
    if old_texts:
        metrics["old_avg_confidence"] = sum(t["confidence"] for t in old_texts) / len(old_texts)
    else:
        metrics["old_avg_confidence"] = 0
    
    if new_texts:
        metrics["new_avg_confidence"] = sum(t["confidence"] for t in new_texts) / len(new_texts)
    else:
        metrics["new_avg_confidence"] = 0
    
    # 文本长度统计
    if old_texts:
        old_lengths = [len(t["text"]) for t in old_texts]
        metrics["old_total_chars"] = sum(old_lengths)
        metrics["old_avg_length"] = sum(old_lengths) / len(old_lengths)
    else:
        metrics["old_total_chars"] = 0
        metrics["old_avg_length"] = 0
    
    if new_texts:
        new_lengths = [len(t["text"]) for t in new_texts]
        metrics["new_total_chars"] = sum(new_lengths)
        metrics["new_avg_length"] = sum(new_lengths) / len(new_lengths)
    else:
        metrics["new_total_chars"] = 0
        metrics["new_avg_length"] = 0
    
    # 文本匹配率（简单字符串匹配）
    old_text_set = set(t["text"] for t in old_texts)
    new_text_set = set(t["text"] for t in new_texts)
    common_texts = old_text_set & new_text_set
    
    metrics["common_text_count"] = len(common_texts)
    metrics["old_unique_count"] = len(old_text_set - new_text_set)
    metrics["new_unique_count"] = len(new_text_set - old_text_set)
    
    return metrics


def generate_report(old_result, new_result, metrics, output_file):
    """生成对比报告"""
    report = []
    report.append("=" * 100)
    report.append("PaddleOCR 模型对比测试报告")
    report.append("=" * 100)
    report.append("")
    
    # 模型信息
    report.append("## 1. 模型信息")
    report.append("-" * 100)
    report.append(f"旧模型: {old_result['model_version']}")
    report.append(f"  - 检测模型: inference/ch_PP-OCRv3_det_infer")
    report.append(f"  - 识别模型: inference/ch_PP-OCRv3_rec_infer")
    report.append(f"  - 表格模型: inference/ch_ppstructure_mobile_v2.0_SLANet_infer")
    report.append("")
    report.append(f"新模型: {new_result['model_version']}")
    report.append(f"  - 检测模型: inference/new-version/PP-OCRv5_server_det_infer")
    report.append(f"  - 识别模型: inference/new-version/PP-OCRv5_server_rec_infer")
    report.append(f"  - 表格模型: inference/new-version/SLANeXt_wired_infer")
    report.append("")
    
    # 性能对比
    report.append("## 2. 性能对比")
    report.append("-" * 100)
    report.append(f"{'指标':<30} {'旧模型 (PP-OCRv3)':<25} {'新模型 (PP-OCRv5)':<25} {'提升':<20}")
    report.append("-" * 100)
    
    # 初始化时间
    old_init = old_result['init_time']
    new_init = new_result['init_time']
    init_diff = ((old_init - new_init) / old_init * 100) if old_init > 0 else 0
    report.append(f"{'模型加载时间 (秒)':<30} {old_init:<25.3f} {new_init:<25.3f} {init_diff:>+.2f}%")
    
    # 预测时间
    old_pred = old_result['pred_time']
    new_pred = new_result['pred_time']
    pred_diff = ((old_pred - new_pred) / old_pred * 100) if old_pred > 0 else 0
    report.append(f"{'总预测时间 (秒)':<30} {old_pred:<25.3f} {new_pred:<25.3f} {pred_diff:>+.2f}%")
    
    # 检测时间
    old_det = old_result['time_dict'].get('det', 0)
    new_det = new_result['time_dict'].get('det', 0)
    det_diff = ((old_det - new_det) / old_det * 100) if old_det > 0 else 0
    report.append(f"{'文本检测时间 (秒)':<30} {old_det:<25.3f} {new_det:<25.3f} {det_diff:>+.2f}%")
    
    # 识别时间
    old_rec = old_result['time_dict'].get('rec', 0)
    new_rec = new_result['time_dict'].get('rec', 0)
    rec_diff = ((old_rec - new_rec) / old_rec * 100) if old_rec > 0 else 0
    report.append(f"{'文本识别时间 (秒)':<30} {old_rec:<25.3f} {new_rec:<25.3f} {rec_diff:>+.2f}%")
    report.append("")
    
    # 识别结果对比
    report.append("## 3. 识别结果对比")
    report.append("-" * 100)
    report.append(f"{'指标':<30} {'旧模型':<25} {'新模型':<25} {'差异':<20}")
    report.append("-" * 100)
    
    # 文本数量
    old_count = metrics['old_text_count']
    new_count = metrics['new_text_count']
    count_diff = new_count - old_count
    report.append(f"{'检测文本行数':<30} {old_count:<25} {new_count:<25} {count_diff:>+d}")
    
    # 总字符数
    old_chars = metrics['old_total_chars']
    new_chars = metrics['new_total_chars']
    chars_diff = new_chars - old_chars
    report.append(f"{'识别总字符数':<30} {old_chars:<25} {new_chars:<25} {chars_diff:>+d}")
    
    # 平均置信度
    old_conf = metrics['old_avg_confidence']
    new_conf = metrics['new_avg_confidence']
    conf_diff = ((new_conf - old_conf) / old_conf * 100) if old_conf > 0 else 0
    report.append(f"{'平均置信度':<30} {old_conf:<25.4f} {new_conf:<25.4f} {conf_diff:>+.2f}%")
    
    # 平均文本长度
    old_len = metrics['old_avg_length']
    new_len = metrics['new_avg_length']
    len_diff = new_len - old_len
    report.append(f"{'平均文本长度':<30} {old_len:<25.2f} {new_len:<25.2f} {len_diff:>+.2f}")
    report.append("")
    
    # 文本匹配情况
    report.append("## 4. 文本匹配情况")
    report.append("-" * 100)
    report.append(f"两个模型共同识别的文本: {metrics['common_text_count']} 行")
    report.append(f"仅旧模型识别的文本: {metrics['old_unique_count']} 行")
    report.append(f"仅新模型识别的文本: {metrics['new_unique_count']} 行")
    report.append("")
    
    # 综合评价
    report.append("## 5. 综合评价")
    report.append("-" * 100)
    
    # 速度提升
    speed_improvement = pred_diff
    if speed_improvement > 0:
        report.append(f"✓ 速度提升: 新模型比旧模型快 {speed_improvement:.2f}%")
    elif speed_improvement < 0:
        report.append(f"✗ 速度下降: 新模型比旧模型慢 {abs(speed_improvement):.2f}%")
    else:
        report.append(f"- 速度相当")
    
    # 准确度提升
    accuracy_improvement = conf_diff
    if accuracy_improvement > 0:
        report.append(f"✓ 准确度提升: 新模型置信度提高 {accuracy_improvement:.2f}%")
    elif accuracy_improvement < 0:
        report.append(f"✗ 准确度下降: 新模型置信度降低 {abs(accuracy_improvement):.2f}%")
    else:
        report.append(f"- 准确度相当")
    
    # 检测能力
    if new_count > old_count:
        report.append(f"✓ 检测能力提升: 新模型多检测 {new_count - old_count} 行文本")
    elif new_count < old_count:
        report.append(f"✗ 检测能力下降: 新模型少检测 {old_count - new_count} 行文本")
    else:
        report.append(f"- 检测能力相当")
    
    # 识别字符数
    if new_chars > old_chars:
        report.append(f"✓ 识别字符数提升: 新模型多识别 {new_chars - old_chars} 个字符")
    elif new_chars < old_chars:
        report.append(f"✗ 识别字符数下降: 新模型少识别 {old_chars - new_chars} 个字符")
    else:
        report.append(f"- 识别字符数相当")
    
    report.append("")
    
    # 总体评分
    report.append("## 6. 总体评分")
    report.append("-" * 100)
    
    score = 0
    max_score = 0
    
    # 速度评分 (30分)
    max_score += 30
    if speed_improvement >= 20:
        score += 30
        report.append(f"速度评分: 30/30 (提升{speed_improvement:.1f}%，非常显著)")
    elif speed_improvement >= 10:
        score += 25
        report.append(f"速度评分: 25/30 (提升{speed_improvement:.1f}%，显著)")
    elif speed_improvement >= 0:
        score += 20
        report.append(f"速度评分: 20/30 (提升{speed_improvement:.1f}%，轻微)")
    elif speed_improvement >= -10:
        score += 15
        report.append(f"速度评分: 15/30 (下降{abs(speed_improvement):.1f}%，轻微)")
    else:
        score += 10
        report.append(f"速度评分: 10/30 (下降{abs(speed_improvement):.1f}%，明显)")
    
    # 准确度评分 (40分)
    max_score += 40
    if accuracy_improvement >= 5:
        score += 40
        report.append(f"准确度评分: 40/40 (提升{accuracy_improvement:.1f}%，非常显著)")
    elif accuracy_improvement >= 2:
        score += 35
        report.append(f"准确度评分: 35/40 (提升{accuracy_improvement:.1f}%，显著)")
    elif accuracy_improvement >= 0:
        score += 30
        report.append(f"准确度评分: 30/40 (提升{accuracy_improvement:.1f}%，轻微)")
    elif accuracy_improvement >= -2:
        score += 25
        report.append(f"准确度评分: 25/40 (下降{abs(accuracy_improvement):.1f}%，轻微)")
    else:
        score += 20
        report.append(f"准确度评分: 20/40 (下降{abs(accuracy_improvement):.1f}%，明显)")
    
    # 检测能力评分 (30分)
    max_score += 30
    detection_rate = (new_count / old_count - 1) * 100 if old_count > 0 else 0
    if detection_rate >= 10:
        score += 30
        report.append(f"检测能力评分: 30/30 (提升{detection_rate:.1f}%，非常显著)")
    elif detection_rate >= 5:
        score += 25
        report.append(f"检测能力评分: 25/30 (提升{detection_rate:.1f}%，显著)")
    elif detection_rate >= 0:
        score += 20
        report.append(f"检测能力评分: 20/30 (提升{detection_rate:.1f}%，轻微)")
    elif detection_rate >= -5:
        score += 15
        report.append(f"检测能力评分: 15/30 (下降{abs(detection_rate):.1f}%，轻微)")
    else:
        score += 10
        report.append(f"检测能力评分: 10/30 (下降{abs(detection_rate):.1f}%，明显)")
    
    report.append("")
    report.append(f"总体评分: {score}/{max_score} ({score/max_score*100:.1f}分)")
    
    if score >= 85:
        report.append("评级: A+ (新模型表现优秀，显著优于旧模型)")
    elif score >= 75:
        report.append("评级: A (新模型表现良好，明显优于旧模型)")
    elif score >= 65:
        report.append("评级: B (新模型表现不错，略优于旧模型)")
    elif score >= 55:
        report.append("评级: C (新模型表现一般，与旧模型相当)")
    else:
        report.append("评级: D (新模型表现不佳，建议继续使用旧模型)")
    
    report.append("")
    report.append("=" * 100)
    
    # 保存报告
    report_text = "\n".join(report)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report_text)
    
    # 打印到控制台
    print(report_text)
    
    return report_text


def save_detailed_results(old_texts, new_texts, output_dir):
    """保存详细的识别结果"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存旧模型结果
    with open(os.path.join(output_dir, "old_model_texts.json"), "w", encoding="utf-8") as f:
        json.dump(old_texts, f, ensure_ascii=False, indent=2)
    
    # 保存新模型结果
    with open(os.path.join(output_dir, "new_model_texts.json"), "w", encoding="utf-8") as f:
        json.dump(new_texts, f, ensure_ascii=False, indent=2)
    
    # 保存文本对比
    comparison = {
        "old_model": [t["text"] for t in old_texts],
        "new_model": [t["text"] for t in new_texts]
    }
    with open(os.path.join(output_dir, "text_comparison.json"), "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)
    
    logger.info(f"详细结果已保存到: {output_dir}")


def main():
    # 解析参数
    parser = parse_args()
    parser.add_argument("--test_image", type=str, required=True, help="测试图片路径")
    parser.add_argument("--comparison_output", type=str, default="./model_comparison_report.txt", 
                       help="对比报告输出路径")
    parser.add_argument("--detail_output_dir", type=str, default="./comparison_details",
                       help="详细结果输出目录")
    args = parser.parse_args()
    
    image_path = args.test_image
    
    # 测试旧模型
    try:
        old_result = test_old_model(image_path, args)
        logger.info("旧模型测试完成")
    except Exception as e:
        logger.error(f"旧模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 测试新模型
    try:
        new_result = test_new_model(image_path, args)
        logger.info("新模型测试完成")
    except Exception as e:
        logger.error(f"新模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 提取文本结果
    old_texts, new_texts = compare_text_results(old_result["results"], new_result["results"])
    
    # 计算指标
    metrics = calculate_metrics(old_texts, new_texts)
    
    # 生成报告
    generate_report(old_result, new_result, metrics, args.comparison_output)
    
    # 保存详细结果
    save_detailed_results(old_texts, new_texts, args.detail_output_dir)
    
    logger.info("=" * 80)
    logger.info(f"对比测试完成！报告已保存到: {args.comparison_output}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

