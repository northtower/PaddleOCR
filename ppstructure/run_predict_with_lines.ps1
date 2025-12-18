# PaddleOCR Prediction Script with Line Detection for PowerShell
# This script runs PP-Structure prediction with GPU acceleration and line detection

# Activate conda environment
Write-Host "Activating conda environment: paddleocr310" -ForegroundColor Green
conda activate paddleocr310

# Change to ppstructure directory
Set-Location -Path $PSScriptRoot

# Set environment variables for GPU
$env:CUDA_VISIBLE_DEVICES = "0"
$env:FLAGS_allocator_strategy = "auto_growth"

# Define the image path (Windows style)
$imagePath = "C:\codeBase\ocr\PaddleOCR\ppstructure\docs\img\0a4ad205277a55592971b5ebf7970cbb\image-3.jpg"

Write-Host "Running PaddleOCR prediction with line detection..." -ForegroundColor Green
Write-Host "Image: $imagePath" -ForegroundColor Cyan

# Run the prediction with line detection enabled
python predict_system.py `
    --image_dir="$imagePath" `
    --det_model_dir="inference/ch_PP-OCRv3_det_infer" `
    --rec_model_dir="inference/ch_PP-OCRv3_rec_infer" `
    --rec_char_dict_path="../ppocr/utils/ppocr_keys_v1.txt" `
    --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" `
    --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" `
    --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" `
    --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" `
    --vis_font_path="../doc/fonts/chinese_cht.ttf" `
    --output="./output/" `
    --return_word_box=True `
    --enable_line_detection=True `
    --line_min_length=50 `
    --line_max_thickness=5 `
    --use_gpu=True

Write-Host "`nPrediction completed!" -ForegroundColor Green




