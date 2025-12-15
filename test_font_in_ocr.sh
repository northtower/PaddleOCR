#!/bin/bash
# 测试字体分类集成的脚本

cd /Users/zoutao03/codeBase/ocr/PaddleOCR

echo "==================== 测试字体分类集成 ===================="
echo ""
echo "1. 使用字体分类运行OCR..."

python tools/infer/predict_system.py \
  --image_dir=ppstructure/docs/img/0a4ad205277a55592971b5ebf7970cbb/image-3.jpg \
  --det_model_dir=ppstructure/inference/new-version/PP-OCRv5_server_det_infer \
  --rec_model_dir=ppstructure/inference/new-version/PP-OCRv5_server_rec_infer \
  --rec_char_dict_path=ppocr/utils/dict/ppocrv5_dict.txt \
  --enable_font_classifier=True \
  --font_model_path=inference/font_classifier/font_family.pdparams \
  --font_dict_path=inference/font_classifier/font_family_dict.txt \
  --draw_img_save_dir=./output_font_test/ \
  2>&1 | grep -E "(字体分类器|font_res num|Font:)" 

echo ""
echo "2. 检查输出结果..."
if [ -f "./output_font_test/system_results.txt" ]; then
    echo "✓ 结果文件已生成"
    
    # 检查是否包含字体信息
    if grep -q "font_family" "./output_font_test/system_results.txt"; then
        echo "✓ 结果包含字体信息!"
        echo ""
        echo "示例结果:"
        python -c "
import json
with open('./output_font_test/system_results.txt', 'r') as f:
    line = f.readline()
    parts = line.split('\t', 1)
    if len(parts) > 1:
        data = json.loads(parts[1])
        for i, item in enumerate(data[:3]):
            print(f'  [{i+1}] {item[\"transcription\"][:40]}...')
            if 'font_family' in item:
                print(f'      字体: {item[\"font_family\"]} (置信度: {item[\"font_confidence\"]:.3f})')
        "
    else
        echo "✗ 结果不包含字体信息"
    fi
else
    echo "✗ 结果文件未生成"
fi

echo ""
echo "==================== 测试完成 ===================="

