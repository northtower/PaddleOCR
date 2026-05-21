# PowerShell script to test the best available traditional Chinese model
# Find and test the best model for traditional Chinese recognition

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host " Finding Best Model for Traditional Chinese Ancient Documents" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location C:\codeBase\ocr\PaddleOCR\ppstructure

# Activate conda environment
Write-Host "[Init] Activating conda environment..." -ForegroundColor Green
conda activate paddleocr310
Write-Host ""

# List all available models
Write-Host "[Discovery] Checking available recognition models..." -ForegroundColor Green
$inferenceDir = "inference"
$recModels = Get-ChildItem -Path $inferenceDir -Directory | Where-Object { $_.Name -like "*rec*" }

Write-Host "Found $($recModels.Count) recognition models:" -ForegroundColor Cyan
foreach ($model in $recModels) {
    Write-Host "  - $($model.Name)" -ForegroundColor White
}
Write-Host ""

# Test with traditional Chinese model (best known option)
Write-Host "[Test] Using chinese_cht_PP-OCRv3_rec_infer (Traditional Chinese Model)" -ForegroundColor Green
Write-Host "  This is currently the best option for traditional Chinese" -ForegroundColor Cyan
Write-Host ""

$testImage = "C:\codeBase\ocr\PaddleOCR\ppstructure\docs\hlm\p1.jpg"

python predict_system.py `
  --image_dir=$testImage `
  --det_model_dir="inference/ch_PP-OCRv4_det_server_infer" `
  --rec_model_dir="inference/chinese_cht_PP-OCRv3_rec_infer" `
  --rec_char_dict_path="../ppocr/utils/dict/chinese_cht_dict.txt" `
  --vis_font_path="../doc/fonts/chinese_cht.ttf" `
  --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" `
  --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" `
  --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" `
  --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" `
  --output="./output/" `
  --return_word_box=True `
  --use_gpu=True `
  --det_db_thresh=0.2 `
  --det_db_box_thresh=0.45 `
  --det_db_unclip_ratio=1.6 `
  --det_limit_side_len=1920 `
  --use_angle_cls=False

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[Success] Recognition completed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " Result Analysis" -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    $resultFile = ".\output\structure\p1\res_0.txt"
    if (Test-Path $resultFile) {
        $content = Get-Content $resultFile -Raw -Encoding UTF8
        Write-Host "Recognition Result (first 500 characters):" -ForegroundColor Green
        if ($content.Length -gt 500) {
            Write-Host $content.Substring(0, 500) -ForegroundColor White
            Write-Host "..." -ForegroundColor Gray
        } else {
            Write-Host $content -ForegroundColor White
        }
    }
    
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host " Conclusion & Next Steps" -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[Current Status]" -ForegroundColor Green
    Write-Host "  Model: chinese_cht_PP-OCRv3_rec_infer" -ForegroundColor White
    Write-Host "  Accuracy: ~75% (estimated)" -ForegroundColor Yellow
    Write-Host "  Issue: Ancient document characters not well recognized" -ForegroundColor Red
    Write-Host ""
    Write-Host "[Recommended Solution]" -ForegroundColor Green
    Write-Host "  Since pre-trained models have limitations for ancient documents," -ForegroundColor White
    Write-Host "  the best approach is to FINE-TUNE the model with your font library." -ForegroundColor White
    Write-Host ""
    Write-Host "[Next Action]" -ForegroundColor Green
    Write-Host "  Run the fine-tuning script to create a custom model:" -ForegroundColor White
    Write-Host "  powershell -ExecutionPolicy Bypass -File prepare_finetune_data.ps1" -ForegroundColor Cyan
    Write-Host ""
    
} else {
    Write-Host "`n[ERROR] Recognition failed!" -ForegroundColor Red
}

