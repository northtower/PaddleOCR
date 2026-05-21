# PowerShell script to test PP-OCRv4 Document Model for Traditional Chinese
# Test PP-OCRv4 document model for better traditional Chinese recognition

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " Traditional Chinese OCR Optimization - Solution 1: PP-OCRv4 Document Model" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\codeBase\ocr\PaddleOCR\ppstructure

# Activate conda environment
Write-Host "[Step 1/4] Activating conda environment..." -ForegroundColor Green
conda activate paddleocr310

# Check if doc model exists
Write-Host "`n[Step 2/4] Checking PP-OCRv4 document model..." -ForegroundColor Green
$docModelPath = "inference/PP-OCRv4_server_rec_doc_infer"
if (Test-Path $docModelPath) {
    Write-Host "  [OK] Document model exists: $docModelPath" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Document model not found" -ForegroundColor Red
    Write-Host "  Please download PP-OCRv4_server_rec_doc_infer model from PaddleOCR" -ForegroundColor Yellow
    exit 1
}

# Run OCR with Document Model
Write-Host "`n[Step 3/4] Running OCR with PP-OCRv4 document model..." -ForegroundColor Green
Write-Host "  Model: PP-OCRv4_server_rec_doc_infer (Document Optimized)" -ForegroundColor Cyan
Write-Host "  Dict: ppocrv4_doc_dict.txt (Document Dictionary)" -ForegroundColor Cyan
Write-Host ""

python predict_system.py `
  --image_dir="C:\codeBase\ocr\PaddleOCR\ppstructure\docs\hlm\p1.jpg" `
  --det_model_dir="inference/ch_PP-OCRv4_det_server_infer" `
  --rec_model_dir="inference/PP-OCRv4_server_rec_doc_infer" `
  --rec_char_dict_path="../ppocr/utils/dict/ppocrv4_doc_dict.txt" `
  --vis_font_path="../doc/fonts/chinese_cht.ttf" `
  --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" `
  --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" `
  --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" `
  --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" `
  --output="./output_doc_model/" `
  --return_word_box=True `
  --use_gpu=True `
  --det_db_thresh=0.2 `
  --det_db_box_thresh=0.45 `
  --det_db_unclip_ratio=1.6 `
  --det_limit_side_len=1920 `
  --use_angle_cls=False

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[Step 4/4] Recognition completed!" -ForegroundColor Green
    Write-Host "  Output directory: ./output_doc_model/structure/p1/" -ForegroundColor Cyan
    Write-Host "  - res_0.txt: Recognition text result" -ForegroundColor White
    Write-Host "  - res_0.json: Detailed JSON result" -ForegroundColor White
    Write-Host "  - show_0.jpg: Visualization image" -ForegroundColor White
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " Next: Compare results with previous models" -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Comparison commands:" -ForegroundColor Green
    Write-Host "  1. View doc model result: type .\output_doc_model\structure\p1\res_0.txt" -ForegroundColor White
    Write-Host "  2. View traditional model result: type .\output\structure\p1\res_0.txt" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "`n[ERROR] OCR recognition failed!" -ForegroundColor Red
    Write-Host "  Please check error messages and retry" -ForegroundColor Yellow
}
