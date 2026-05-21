#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型对比测试脚本
测试不同检测和识别模型的组合，评估最佳方案
"""

import subprocess
import time
import os
import json
from pathlib import Path

# 测试图片
TEST_IMAGE = r"C:\codeBase\pdf\pdf-parser-clib\build\output\h1\image-20.jpg"

# 模型配置
MODELS = {
    "det": {
        "v3": {
            "path": "inference/ch_PP-OCRv3_det_infer",
            "name": "PP-OCRv3 Det"
        },
        "v4": {
            "path": "inference/ch_PP-OCRv4_det_server_infer",
            "name": "PP-OCRv4 Det Server"
        },
        "v5": {
            "path": "inference/PP-OCRv5_server_det_infer",
            "name": "PP-OCRv5 Det Server"
        }
    },
    "rec": {
        "v3_ch": {
            "path": "inference/ch_PP-OCRv3_rec_infer",
            "dict": "../ppocr/utils/ppocr_keys_v1.txt",
            "name": "PP-OCRv3 Rec (简体)"
        },
        "v3_cht": {
            "path": "inference/chinese_cht_PP-OCRv3_rec_infer",
            "dict": "../ppocr/utils/dict/chinese_cht_dict.txt",
            "name": "PP-OCRv3 Rec (繁体)"
        },
        "v4_doc": {
            "path": "inference/PP-OCRv4_server_rec_doc_infer",
            "dict": "../ppocr/utils/dict/ppocrv4_doc_dict.txt",
            "name": "PP-OCRv4 Rec Doc Server"
        },
        "v5_rec": {
            "path": "inference/PP-OCRv5_server_rec_infer",
            "dict": "../ppocr/utils/dict/ppocrv5_dict.txt",
            "name": "PP-OCRv5 Rec Server"
        }
    }
}

# 优化参数
PARAMS = {
    "det_db_thresh": "0.2",
    "det_db_box_thresh": "0.45",
    "det_db_unclip_ratio": "1.6",
    "det_limit_side_len": "1920",
    "use_gpu": "True",
    "use_angle_cls": "False"  # 禁用角度分类器，因为没有cls模型
}


def run_ocr_test(det_key, rec_key, output_dir):
    """运行单次OCR测试"""
    det_model = MODELS["det"][det_key]
    rec_model = MODELS["rec"][rec_key]
    
    test_name = f"{det_key}_{rec_key}"
    print(f"\n{'='*70}")
    print(f"测试组合: {det_model['name']} + {rec_model['name']}")
    print(f"{'='*70}")
    
    # 创建输出目录
    test_output = os.path.join(output_dir, test_name)
    os.makedirs(test_output, exist_ok=True)
    
    # 构建命令
    cmd = [
        "python", "../tools/infer/predict_system.py",
        f"--image_dir={TEST_IMAGE}",
        f"--det_model_dir={det_model['path']}",
        f"--rec_model_dir={rec_model['path']}",
        f"--rec_char_dict_path={rec_model['dict']}",
        "--vis_font_path=../doc/fonts/chinese_cht.ttf",
        f"--det_db_thresh={PARAMS['det_db_thresh']}",
        f"--det_db_box_thresh={PARAMS['det_db_box_thresh']}",
        f"--det_db_unclip_ratio={PARAMS['det_db_unclip_ratio']}",
        f"--det_limit_side_len={PARAMS['det_limit_side_len']}",
        f"--use_gpu={PARAMS['use_gpu']}",
        f"--use_angle_cls={PARAMS['use_angle_cls']}",
        f"--draw_img_save_dir={test_output}",
        f"--save_log_path={test_output}"
    ]
    
    # 运行测试
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        elapsed_time = time.time() - start_time
        
        # 解析输出
        output_lines = result.stdout.split('\n')
        dt_boxes_num = 0
        rec_results = []
        
        for line in output_lines:
            if 'dt_boxes num' in line:
                try:
                    # 提取检测框数量（从日志中的实际数字）
                    dt_boxes_num = int(line.split(':')[1].split(',')[0].strip())
                except:
                    pass
            elif 'ppocr DEBUG:' in line:
                # 提取识别结果（包含置信度的行）
                parts = line.split('ppocr DEBUG:')
                if len(parts) > 1:
                    content = parts[1].strip()
                    # 只提取包含置信度的识别结果，排除其他DEBUG信息
                    if ', 0.' in content and 'Predict time' not in content and 'visualized' not in content:
                        rec_results.append(content)
        
        # 保存结果
        result_file = os.path.join(test_output, "test_result.txt")
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"测试组合: {det_model['name']} + {rec_model['name']}\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"检测模型: {det_model['path']}\n")
            f.write(f"识别模型: {rec_model['path']}\n")
            f.write(f"字典文件: {rec_model['dict']}\n\n")
            f.write(f"检测框数量: {dt_boxes_num}\n")
            f.write(f"处理时间: {elapsed_time:.2f}秒\n\n")
            f.write(f"识别结果:\n")
            f.write("-"*70 + "\n")
            for i, res in enumerate(rec_results, 1):
                f.write(f"{i}. {res}\n")
            f.write("\n\n完整输出:\n")
            f.write("="*70 + "\n")
            f.write(result.stdout)
        
        print(f"[OK] 测试成功")
        print(f"  - 检测框数量: {dt_boxes_num}")
        print(f"  - 处理时间: {elapsed_time:.2f}秒")
        print(f"  - 识别结果数: {len(rec_results)}")
        print(f"  - 结果保存至: {test_output}")
        
        return {
            "success": True,
            "det_model": det_model['name'],
            "rec_model": rec_model['name'],
            "dt_boxes_num": dt_boxes_num,
            "rec_results_num": len(rec_results),
            "elapsed_time": elapsed_time,
            "output_dir": test_output
        }
        
    except subprocess.CalledProcessError as e:
        elapsed_time = time.time() - start_time
        print(f"[FAIL] 测试失败: {e}")
        
        # 保存错误信息
        error_file = os.path.join(test_output, "error.txt")
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"测试失败\n")
            f.write(f"错误: {str(e)}\n\n")
            if e.stdout:
                f.write(f"Stdout:\n{e.stdout}\n\n")
            if e.stderr:
                f.write(f"Stderr:\n{e.stderr}\n")
        
        return {
            "success": False,
            "det_model": det_model['name'],
            "rec_model": rec_model['name'],
            "error": str(e),
            "elapsed_time": elapsed_time
        }
    except Exception as e:
        print(f"[ERROR] 意外错误: {e}")
        return {
            "success": False,
            "det_model": det_model['name'],
            "rec_model": rec_model['name'],
            "error": str(e)
        }


def main():
    print("="*70)
    print("PaddleOCR 模型对比测试")
    print("="*70)
    print(f"\n测试图片: {TEST_IMAGE}")
    print(f"\n优化参数:")
    for key, value in PARAMS.items():
        print(f"  - {key}: {value}")
    print()
    
    # 创建输出目录
    output_dir = "./output/model_comparison"
    os.makedirs(output_dir, exist_ok=True)
    
    # 测试组合
    test_combinations = [
        ("v3", "v3_ch"),    # PP-OCRv3 Det + PP-OCRv3 Rec 简体
        ("v3", "v3_cht"),   # PP-OCRv3 Det + PP-OCRv3 Rec 繁体
        ("v3", "v4_doc"),   # PP-OCRv3 Det + PP-OCRv4 Rec Doc
        ("v4", "v3_ch"),    # PP-OCRv4 Det + PP-OCRv3 Rec 简体
        ("v4", "v3_cht"),   # PP-OCRv4 Det + PP-OCRv3 Rec 繁体
        ("v4", "v4_doc"),   # PP-OCRv4 Det + PP-OCRv4 Rec Doc
        ("v5", "v5_rec"),    # 纯血 V5 组合 (推荐)
        ("v5", "v3_cht"),    # V5检测 + V3繁体识别 (对比用)
        ("v4", "v5_rec"),    # V4检测 + V5识别 (对比用)
    ]
    
    print(f"将测试 {len(test_combinations)} 种模型组合\n")
    
    # 运行所有测试
    results = []
    for i, (det_key, rec_key) in enumerate(test_combinations, 1):
        print(f"\n[{i}/{len(test_combinations)}]")
        result = run_ocr_test(det_key, rec_key, output_dir)
        results.append(result)
        time.sleep(1)  # 短暂延迟
    
    # 生成对比报告
    print(f"\n{'='*70}")
    print("测试完成 - 结果汇总")
    print(f"{'='*70}\n")
    
    # 按成功/失败分组
    success_results = [r for r in results if r.get('success')]
    failed_results = [r for r in results if not r.get('success')]
    
    if success_results:
        print(f"成功的测试 ({len(success_results)}):")
        print("-"*70)
        
        # 按检测框数量排序
        success_results.sort(key=lambda x: x.get('dt_boxes_num', 0), reverse=True)
        
        for i, r in enumerate(success_results, 1):
            print(f"\n{i}. {r['det_model']} + {r['rec_model']}")
            print(f"   检测框数: {r['dt_boxes_num']}")
            print(f"   识别结果: {r['rec_results_num']}")
            print(f"   处理时间: {r['elapsed_time']:.2f}秒")
            print(f"   输出目录: {r['output_dir']}")
        
        # 推荐最佳组合
        best = success_results[0]
        print(f"\n{'='*70}")
        print("推荐最佳组合:")
        print(f"{'='*70}")
        print(f"检测模型: {best['det_model']}")
        print(f"识别模型: {best['rec_model']}")
        print(f"检测框数: {best['dt_boxes_num']}")
        print(f"处理时间: {best['elapsed_time']:.2f}秒")
        print(f"结果目录: {best['output_dir']}")
    
    if failed_results:
        print(f"\n\n失败的测试 ({len(failed_results)}):")
        print("-"*70)
        for i, r in enumerate(failed_results, 1):
            print(f"{i}. {r['det_model']} + {r['rec_model']}")
            print(f"   错误: {r.get('error', 'Unknown')}")
    
    # 保存汇总报告
    summary_file = os.path.join(output_dir, "summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_image": TEST_IMAGE,
            "parameters": PARAMS,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n\n汇总报告已保存: {summary_file}")
    print(f"所有结果保存在: {output_dir}")
    print()


if __name__ == "__main__":
    # 检查conda环境
    current_env = os.environ.get('CONDA_DEFAULT_ENV', '')
    if current_env != 'paddleocr310':
        print(f"警告: 当前不在 paddleocr310 环境中")
        print(f"当前环境: {current_env or 'None'}")
        print(f"\n请先激活环境:")
        print(f"  conda activate paddleocr310")
        print()
        response = input("继续测试? (y/n): ")
        if response.lower() != 'y':
            exit(1)
    
    main()

