# Fast Batch OCR Processing with Concurrency
# Pure OCR mode (no layout/table analysis) for maximum speed
# Supports 1-10 concurrent processes

param(
    [string]$ImageDir,
    [int]$Concurrency = 3
)

# Set encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Validate Concurrency
if ($Concurrency -lt 1 -or $Concurrency -gt 10) {
    Write-Output "[ERROR] Concurrency must be between 1 and 10. Got: $Concurrency"
    exit 1
}

# Set default image directory if not provided
if (-not $ImageDir) {
    $ImageDir = Join-Path $PSScriptRoot "docs\img\0a4ad205277a55592971b5ebf7970cbb"
}

Write-Output "========================================"
Write-Output "  PaddleOCR Fast Batch Mode"
Write-Output "========================================"
Write-Output ""

# GPU acceleration settings
$env:CUDA_VISIBLE_DEVICES = "0"
$env:FLAGS_allocator_strategy = "auto_growth"

Write-Output "Image Directory: $ImageDir"

# Count images
$imageFiles = Get-ChildItem -Path $ImageDir -File | Where-Object { $_.Extension -in @('.jpg', '.jpeg', '.png', '.bmp') }
$imageCount = $imageFiles.Count
Write-Output "Image Count: $imageCount images"
Write-Output "Processing Mode: Pure OCR (Detection + Recognition only)"
Write-Output "Concurrency: $Concurrency processes"
Write-Output "GPU: Enabled"
Write-Output ""

if ($imageCount -eq 0) {
    Write-Output "[ERROR] No image files found in directory: $ImageDir"
    Write-Output "Please check the path or specify a different directory with -ImageDir parameter"
    exit 1
}

# Calculate optimal batch size
$recBatchNum = [Math]::Max(8, $Concurrency * 3)

Write-Output "Starting fast batch processing..."
Write-Output "Optimization: rec_batch_num=$recBatchNum, process_num=$Concurrency"
Write-Output ""
$startTime = Get-Date

# Switch to project root
Push-Location ..

# Pure OCR batch processing with multi-process
python tools/infer/predict_system.py `
    --image_dir="$ImageDir" `
    --det_model_dir="ppstructure/inference/ch_PP-OCRv3_det_infer" `
    --rec_model_dir="ppstructure/inference/ch_PP-OCRv3_rec_infer" `
    --rec_char_dict_path="ppocr/utils/ppocr_keys_v1.txt" `
    --vis_font_path="doc/fonts/chinese_cht.ttf" `
    --use_gpu=True `
    --use_mp=True `
    --total_process_num=$Concurrency `
    --use_angle_cls=False `
    --rec_batch_num=$recBatchNum `
    --det_db_box_thresh=0.5 `
    --draw_img_save_dir="ppstructure/output/batch_fast"

Pop-Location

$endTime = Get-Date
$elapsed = ($endTime - $startTime).TotalSeconds
$avgTime = if ($imageCount -gt 0) { [math]::Round($elapsed / $imageCount, 2) } else { 0 }
$throughput = if ($elapsed -gt 0) { [math]::Round($imageCount / $elapsed, 2) } else { 0 }

Write-Output ""
Write-Output "========================================"
Write-Output "  Fast Batch Processing Complete!"
Write-Output "  Processed Images: $imageCount"
Write-Output "  Total Time: $([math]::Round($elapsed, 2)) seconds"
Write-Output "  Average Time: $avgTime seconds/image"
Write-Output "  Throughput: $throughput images/second"
Write-Output "  Concurrency: $Concurrency processes"
Write-Output "  Results: ./output/batch_fast/"
Write-Output "========================================"
Write-Output ""
Write-Output "Performance Tips:"
Write-Output "  - Increase concurrency for more images: -Concurrency 5"
Write-Output "  - Default (3 processes) is optimal for most GPUs"
Write-Output "  - Higher concurrency may need more GPU memory"
