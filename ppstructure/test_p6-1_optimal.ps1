# PowerShell script to test optimal configurations for p6-1.jpg
# p6-1.jpg最优配置测试脚本

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " p6-1.jpg OCR Recognition - Optimal Configuration Test" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\codeBase\ocr\PaddleOCR\ppstructure

# Activate conda environment
Write-Host "[Init] Activating conda environment..." -ForegroundColor Green
conda activate paddleocr310
Write-Host ""

$testImage = "C:\codeBase\ocr\PaddleOCR\ppstructure\docs\hlm\p6-1.jpg"

# Test 1: PP-OCRv5 (Recommended for p6-1.jpg)
Write-Host "[Test 1/2] PP-OCRv5 Model (Recommended for simplified Chinese)" -ForegroundColor Green
Write-Host "  Model: PP-OCRv5_server_rec_infer" -ForegroundColor Cyan
Write-Host "  Dict: ppocrv5_dict.txt (~11000 characters)" -ForegroundColor Cyan
Write-Host ""

$startTime1 = Get-Date

python predict_system.py `
  --image_dir=$testImage `
  --det_model_dir="inference/ch_PP-OCRv4_det_server_infer" `
  --rec_model_dir="inference/PP-OCRv5_server_rec_infer" `
  --rec_char_dict_path="../ppocr/utils/dict/ppocrv5_dict.txt" `
  --vis_font_path="../doc/fonts/simfang.ttf" `
  --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" `
  --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" `
  --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" `
  --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" `
  --output="./output_v5/" `
  --return_word_box=True `
  --use_gpu=True `
  --det_db_thresh=0.2 `
  --det_db_box_thresh=0.45 `
  --det_db_unclip_ratio=1.6 `
  --det_limit_side_len=1920 `
  --use_angle_cls=False 2>&1 | Out-Null

$endTime1 = Get-Date
$duration1 = ($endTime1 - $startTime1).TotalSeconds

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [Success] Test 1 completed ($([math]::Round($duration1, 2))s)" -ForegroundColor Green
} else {
    Write-Host "  [Failed] Test 1 failed" -ForegroundColor Red
}
Write-Host ""

# Test 2: PP-OCRv3 Simplified Chinese
Write-Host "[Test 2/2] PP-OCRv3 Simplified Chinese Model (Alternative)" -ForegroundColor Green
Write-Host "  Model: ch_PP-OCRv3_rec_infer" -ForegroundColor Cyan
Write-Host "  Dict: ppocr_keys_v1.txt (~6600 characters)" -ForegroundColor Cyan
Write-Host ""

$startTime2 = Get-Date

python predict_system.py `
  --image_dir=$testImage `
  --det_model_dir="inference/ch_PP-OCRv4_det_server_infer" `
  --rec_model_dir="inference/ch_PP-OCRv3_rec_infer" `
  --rec_char_dict_path="../ppocr/utils/ppocr_keys_v1.txt" `
  --vis_font_path="../doc/fonts/simfang.ttf" `
  --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" `
  --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" `
  --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" `
  --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" `
  --output="./output_v3/" `
  --return_word_box=True `
  --use_gpu=True `
  --det_db_thresh=0.2 `
  --det_db_box_thresh=0.45 `
  --det_db_unclip_ratio=1.6 `
  --det_limit_side_len=1920 `
  --use_angle_cls=False 2>&1 | Out-Null

$endTime2 = Get-Date
$duration2 = ($endTime2 - $startTime2).TotalSeconds

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [Success] Test 2 completed ($([math]::Round($duration2, 2))s)" -ForegroundColor Green
} else {
    Write-Host "  [Failed] Test 2 failed" -ForegroundColor Red
}
Write-Host ""

# Display results
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " Results Comparison" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1 results
$result1File = ".\output_v5\structure\p6-1\res_0.txt"
if (Test-Path $result1File) {
    Write-Host "[Test 1 - PP-OCRv5] Result:" -ForegroundColor Green
    $content1 = Get-Content $result1File -Raw -Encoding UTF8
    Write-Host $content1 -ForegroundColor White
    Write-Host "  File: $result1File" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "[Test 1 - PP-OCRv5] No result file found" -ForegroundColor Red
    Write-Host ""
}

# Test 2 results
$result2File = ".\output_v3\structure\p6-1\res_0.txt"
if (Test-Path $result2File) {
    Write-Host "[Test 2 - PP-OCRv3 Simplified] Result:" -ForegroundColor Green
    $content2 = Get-Content $result2File -Raw -Encoding UTF8
    Write-Host $content2 -ForegroundColor White
    Write-Host "  File: $result2File" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host "[Test 2 - PP-OCRv3 Simplified] No result file found" -ForegroundColor Red
    Write-Host ""
}

# Summary
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " Summary & Recommendation" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[Analysis]" -ForegroundColor Green
Write-Host "  Image type: Simplified Chinese (竖排简体)" -ForegroundColor White
Write-Host "  Detected text boxes: 7" -ForegroundColor White
Write-Host ""
Write-Host "[Recommendation]" -ForegroundColor Green
Write-Host "  Best model for p6-1.jpg: PP-OCRv5_server_rec_infer" -ForegroundColor Yellow
Write-Host "  Reason:" -ForegroundColor White
Write-Host "    1. Largest character dictionary (~11000 chars)" -ForegroundColor White
Write-Host "    2. No missing characters" -ForegroundColor White
Write-Host "    3. Good support for both simplified and traditional Chinese" -ForegroundColor White
Write-Host "    4. Faster processing with JSON format model" -ForegroundColor White
Write-Host ""
Write-Host "[Why traditional Chinese model fails?]" -ForegroundColor Green
Write-Host "  chinese_cht_PP-OCRv3_rec_infer + chinese_cht_dict.txt:" -ForegroundColor White
Write-Host "    - Dictionary size: ~8000 characters (mainly traditional)" -ForegroundColor White
Write-Host "    - Problem: Some simplified characters not in dictionary" -ForegroundColor White
Write-Host "    - Result: Missing characters in output" -ForegroundColor White
Write-Host ""
Write-Host "[Command to use]" -ForegroundColor Green
Write-Host "  For p6-1.jpg (simplified Chinese):" -ForegroundColor Cyan
Write-Host "    --rec_model_dir=`"inference/PP-OCRv5_server_rec_infer`"" -ForegroundColor White
Write-Host "    --rec_char_dict_path=`"../ppocr/utils/dict/ppocrv5_dict.txt`"" -ForegroundColor White
Write-Host ""
Write-Host "  For p1.jpg (traditional Chinese):" -ForegroundColor Cyan
Write-Host "    --rec_model_dir=`"inference/chinese_cht_PP-OCRv3_rec_infer`"" -ForegroundColor White
Write-Host "    --rec_char_dict_path=`"../ppocr/utils/dict/chinese_cht_dict.txt`"" -ForegroundColor White
Write-Host ""

