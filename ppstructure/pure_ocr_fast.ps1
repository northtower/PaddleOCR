# Pure OCR Fast Mode
# Skip layout analysis, only detection + recognition (fastest)

# Set encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

param(
    [string]$ImagePath = "C:\codeBase\ocr\PaddleOCR\ppstructure\docs\img\0a4ad205277a55592971b5ebf7970cbb\image-3.jpg"
)

Write-Output "========================================"
Write-Output "  PaddleOCR Pure OCR Mode (Fastest)"
Write-Output "========================================"
Write-Output ""

# GPU acceleration settings
$env:CUDA_VISIBLE_DEVICES = "0"
$env:FLAGS_allocator_strategy = "auto_growth"
$env:FLAGS_fraction_of_gpu_memory_to_use = "0.8"

Write-Output "Image Path: $ImagePath"
Write-Output "Mode: Pure OCR (Detection + Recognition Only)"
Write-Output "GPU: Enabled (Optimized)"
Write-Output ""
Write-Output "Processing..."
Write-Output ""
$startTime = Get-Date

# Switch to project root directory
Push-Location ..

python tools/infer/predict_system.py `
    --image_dir="$ImagePath" `
    --det_model_dir="ppstructure/inference/ch_PP-OCRv3_det_infer" `
    --rec_model_dir="ppstructure/inference/ch_PP-OCRv3_rec_infer" `
    --rec_char_dict_path="ppocr/utils/ppocr_keys_v1.txt" `
    --vis_font_path="doc/fonts/chinese_cht.ttf" `
    --use_gpu=True `
    --use_angle_cls=False `
    --rec_batch_num=8 `
    --det_db_box_thresh=0.5 `
    --draw_img_save_dir="ppstructure/output/pure_ocr"

Pop-Location

$endTime = Get-Date
$elapsed = ($endTime - $startTime).TotalSeconds

Write-Output ""
Write-Output "========================================"
Write-Output "  Processing Complete!"
Write-Output "  Total Time: $([math]::Round($elapsed, 2)) seconds"
Write-Output "  Results: ./output/pure_ocr/"
Write-Output "========================================"
