#!/bin/bash

# 模型对比测试脚本
# 分别使用旧模型和新模型对同一张图片进行测试，并生成对比报告

# 激活conda环境
source ~/miniforge3/etc/profile.d/conda.sh
conda activate paddlex_env

TEST_IMAGE="./docs/img/0a4ad205277a55592971b5ebf7970cbb/image-3.jpg"
OUTPUT_OLD="./output_old_model"
OUTPUT_NEW="./output_new_model"

echo "================================================================================================"
echo "PaddleOCR 模型对比测试"
echo "================================================================================================"
echo ""
echo "测试图片: $TEST_IMAGE"
echo ""

# 测试旧模型 PP-OCRv3
echo "------------------------------------------------------------------------------------------------"
echo "1. 测试旧模型 PP-OCRv3"
echo "------------------------------------------------------------------------------------------------"

START_OLD=$(date +%s.%N)

python predict_system.py \
  --image_dir="$TEST_IMAGE" \
  --det_model_dir=inference/ch_PP-OCRv3_det_infer \
  --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
  --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
  --table_model_dir=inference/ch_ppstructure_mobile_v2.0_SLANet_infer \
  --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
  --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
  --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
  --vis_font_path=../doc/fonts/chinese_cht.ttf \
  --output="$OUTPUT_OLD" \
  --return_word_box=True \
  --enable_line_detection=True \
  --line_min_length=50 \
  --line_max_thickness=5 \
  2>&1 | tee test_old_model.log

END_OLD=$(date +%s.%N)
TIME_OLD=$(echo "$END_OLD - $START_OLD" | bc)

echo ""
echo "旧模型测试完成，耗时: ${TIME_OLD}秒"
echo "结果保存在: $OUTPUT_OLD"
echo ""

# 测试新模型 PP-OCRv5
echo "------------------------------------------------------------------------------------------------"
echo "2. 测试新模型 PP-OCRv5"
echo "------------------------------------------------------------------------------------------------"

START_NEW=$(date +%s.%N)

python predict_system.py \
  --image_dir="$TEST_IMAGE" \
  --det_model_dir=inference/new-version/PP-OCRv5_server_det_infer \
  --rec_model_dir=inference/new-version/PP-OCRv5_server_rec_infer \
  --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
  --table_model_dir=inference/new-version/SLANeXt_wired_infer \
  --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
  --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
  --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
  --vis_font_path=../doc/fonts/chinese_cht.ttf \
  --output="$OUTPUT_NEW" \
  --return_word_box=True \
  --enable_line_detection=True \
  --line_min_length=50 \
  --line_max_thickness=5 \
  2>&1 | tee test_new_model.log

END_NEW=$(date +%s.%N)
TIME_NEW=$(echo "$END_NEW - $START_NEW" | bc)

echo ""
echo "新模型测试完成，耗时: ${TIME_NEW}秒"
echo "结果保存在: $OUTPUT_NEW"
echo ""

# 生成对比报告
echo "================================================================================================"
echo "生成对比报告"
echo "================================================================================================"

python - <<EOF
import json
import os
from pathlib import Path

def load_result(output_dir):
    """加载识别结果"""
    result_dir = Path(output_dir) / "structure" / "image-3"
    result_file = result_dir / "res_0.txt"
    
    if not result_file.exists():
        print(f"警告: 结果文件不存在: {result_file}")
        return None
    
    with open(result_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    results = []
    for line in lines:
        if line.strip():
            results.append(json.loads(line))
    
    return results

def extract_texts(results):
    """提取文本内容"""
    texts = []
    for item in results:
        if item.get("type") == "text" and isinstance(item.get("res"), list):
            for text_item in item["res"]:
                if "text" in text_item:
                    texts.append({
                        "text": text_item["text"],
                        "confidence": text_item.get("confidence", 0)
                    })
    return texts

def count_lines(results):
    """统计检测到的行数（包括文本和线条）"""
    line_count = 0
    underline_count = 0
    for item in results:
        if item.get("type") == "underline":
            underline_count += 1
        elif item.get("type") == "text":
            line_count += len(item.get("res", []))
    return line_count, underline_count

print("\\n" + "=" * 100)
print("模型对比报告")
print("=" * 100)

# 加载结果
old_results = load_result("$OUTPUT_OLD")
new_results = load_result("$OUTPUT_NEW")

if old_results is None or new_results is None:
    print("\\n错误: 无法加载结果文件，请检查模型运行是否成功")
    exit(1)

# 提取文本
old_texts = extract_texts(old_results)
new_texts = extract_texts(new_results)

# 统计行数
old_line_count, old_underline_count = count_lines(old_results)
new_line_count, new_underline_count = count_lines(new_results)

print("\\n## 1. 基本信息")
print("-" * 100)
print(f"测试图片: $TEST_IMAGE")
print(f"旧模型版本: PP-OCRv3")
print(f"新模型版本: PP-OCRv5")

print("\\n## 2. 性能对比")
print("-" * 100)
time_old = float("$TIME_OLD")
time_new = float("$TIME_NEW")
speed_improvement = ((time_old - time_new) / time_old * 100) if time_old > 0 else 0
print(f"{'指标':<40} {'旧模型 (PP-OCRv3)':<25} {'新模型 (PP-OCRv5)':<25} {'差异':<15}")
print("-" * 100)
print(f"{'总预测时间 (秒)':<40} {time_old:<25.3f} {time_new:<25.3f} {speed_improvement:>+.2f}%")

print("\\n## 3. 识别结果对比")
print("-" * 100)
print(f"{'指标':<40} {'旧模型':<25} {'新模型':<25} {'差异':<15}")
print("-" * 100)

# 文本行数
line_diff = new_line_count - old_line_count
print(f"{'检测文本行数':<40} {old_line_count:<25} {new_line_count:<25} {line_diff:>+d}")

# 横线数
underline_diff = new_underline_count - old_underline_count
print(f"{'检测横线数':<40} {old_underline_count:<25} {new_underline_count:<25} {underline_diff:>+d}")

# 总字符数
old_char_count = sum(len(t["text"]) for t in old_texts)
new_char_count = sum(len(t["text"]) for t in new_texts)
char_diff = new_char_count - old_char_count
print(f"{'识别总字符数':<40} {old_char_count:<25} {new_char_count:<25} {char_diff:>+d}")

# 平均置信度
old_avg_conf = sum(t["confidence"] for t in old_texts) / len(old_texts) if old_texts else 0
new_avg_conf = sum(t["confidence"] for t in new_texts) / len(new_texts) if new_texts else 0
conf_diff = ((new_avg_conf - old_avg_conf) / old_avg_conf * 100) if old_avg_conf > 0 else 0
print(f"{'平均置信度':<40} {old_avg_conf:<25.4f} {new_avg_conf:<25.4f} {conf_diff:>+.2f}%")

# 文本匹配
old_text_set = set(t["text"] for t in old_texts)
new_text_set = set(t["text"] for t in new_texts)
common_count = len(old_text_set & new_text_set)
old_unique = len(old_text_set - new_text_set)
new_unique = len(new_text_set - old_text_set)

print("\\n## 4. 文本匹配情况")
print("-" * 100)
print(f"两个模型共同识别的文本: {common_count} 行")
print(f"仅旧模型识别的文本: {old_unique} 行")
print(f"仅新模型识别的文本: {new_unique} 行")

print("\\n## 5. 详细文本对比")
print("-" * 100)

# 仅旧模型识别的文本
if old_unique > 0:
    print(f"\\n仅旧模型识别的文本 ({old_unique} 行):")
    for i, text in enumerate(sorted(old_text_set - new_text_set), 1):
        if i <= 10:  # 只显示前10条
            print(f"  {i}. {text}")
    if old_unique > 10:
        print(f"  ... 还有 {old_unique - 10} 行未显示")

# 仅新模型识别的文本
if new_unique > 0:
    print(f"\\n仅新模型识别的文本 ({new_unique} 行):")
    for i, text in enumerate(sorted(new_text_set - old_text_set), 1):
        if i <= 10:  # 只显示前10条
            print(f"  {i}. {text}")
    if new_unique > 10:
        print(f"  ... 还有 {new_unique - 10} 行未显示")

print("\\n## 6. 综合评价")
print("-" * 100)

# 评分系统
score = 0
max_score = 100

# 速度评分 (30分)
if speed_improvement >= 20:
    score += 30
    print(f"✓ 速度评分: 30/30 (提升{speed_improvement:.1f}%，非常显著)")
elif speed_improvement >= 10:
    score += 25
    print(f"✓ 速度评分: 25/30 (提升{speed_improvement:.1f}%，显著)")
elif speed_improvement >= 0:
    score += 20
    print(f"○ 速度评分: 20/30 (提升{speed_improvement:.1f}%，轻微)")
elif speed_improvement >= -10:
    score += 15
    print(f"△ 速度评分: 15/30 (下降{abs(speed_improvement):.1f}%，轻微)")
else:
    score += 10
    print(f"✗ 速度评分: 10/30 (下降{abs(speed_improvement):.1f}%，明显)")

# 准确度评分 (40分)
if conf_diff >= 5:
    score += 40
    print(f"✓ 准确度评分: 40/40 (提升{conf_diff:.1f}%，非常显著)")
elif conf_diff >= 2:
    score += 35
    print(f"✓ 准确度评分: 35/40 (提升{conf_diff:.1f}%，显著)")
elif conf_diff >= 0:
    score += 30
    print(f"○ 准确度评分: 30/40 (提升{conf_diff:.1f}%，轻微)")
elif conf_diff >= -2:
    score += 25
    print(f"△ 准确度评分: 25/40 (下降{abs(conf_diff):.1f}%，轻微)")
else:
    score += 20
    print(f"✗ 准确度评分: 20/40 (下降{abs(conf_diff):.1f}%，明显)")

# 检测能力评分 (30分)
detection_rate = ((new_line_count / old_line_count - 1) * 100) if old_line_count > 0 else 0
if detection_rate >= 10:
    score += 30
    print(f"✓ 检测能力评分: 30/30 (提升{detection_rate:.1f}%，非常显著)")
elif detection_rate >= 5:
    score += 25
    print(f"✓ 检测能力评分: 25/30 (提升{detection_rate:.1f}%，显著)")
elif detection_rate >= 0:
    score += 20
    print(f"○ 检测能力评分: 20/30 (提升{detection_rate:.1f}%，轻微)")
elif detection_rate >= -5:
    score += 15
    print(f"△ 检测能力评分: 15/30 (下降{abs(detection_rate):.1f}%，轻微)")
else:
    score += 10
    print(f"✗ 检测能力评分: 10/30 (下降{abs(detection_rate):.1f}%，明显)")

print("\\n" + "-" * 100)
print(f"总体评分: {score}/{max_score} ({score*100/max_score:.1f}分)")

if score >= 85:
    print("评级: A+ (新模型表现优秀，显著优于旧模型)")
elif score >= 75:
    print("评级: A (新模型表现良好，明显优于旧模型)")
elif score >= 65:
    print("评级: B (新模型表现不错，略优于旧模型)")
elif score >= 55:
    print("评级: C (新模型表现一般，与旧模型相当)")
else:
    print("评级: D (新模型表现不佳，建议继续使用旧模型)")

print("\\n" + "=" * 100)
print("\\n结果文件:")
print(f"  旧模型结果: $OUTPUT_OLD/structure/image-3/res_0.txt")
print(f"  新模型结果: $OUTPUT_NEW/structure/image-3/res_0.txt")
print(f"  旧模型可视化: $OUTPUT_OLD/structure/image-3/show_0.jpg")
print(f"  新模型可视化: $OUTPUT_NEW/structure/image-3/show_0.jpg")
print("\\n" + "=" * 100)
EOF

echo ""
echo "对比测试完成！"

