# Batch OCR Processing with Concurrency Support
# Model initialized only once for better performance
# Supports 1-10 concurrent processes for faster batch processing

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
Write-Output "  PaddleOCR Batch Processing Mode"
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
Write-Output "Processing Mode: Batch (Model loaded once)"
Write-Output "Concurrency: $Concurrency processes"
Write-Output "GPU: Enabled"
Write-Output ""

if ($imageCount -eq 0) {
    Write-Output "[ERROR] No image files found in directory: $ImageDir"
    Write-Output "Please check the path or specify a different directory with -ImageDir parameter"
    exit 1
}

# Calculate optimal batch size based on concurrency
$recBatchNum = [Math]::Max(6, $Concurrency * 2)

Write-Output "Starting batch processing..."
Write-Output "Stage 1: Loading models..."
Write-Output "Optimization: rec_batch_num=$recBatchNum, process_num=$Concurrency"
Write-Output ""
$startTime = Get-Date

# Batch processing - model loaded only once with multi-process support
python predict_system.py `
    --image_dir="$ImageDir" `
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
    --use_gpu=True `
    --use_mp=True `
    --total_process_num=$Concurrency `
    --rec_batch_num=$recBatchNum `
    --det_db_box_thresh=0.5 `
    --table=False

$endTime = Get-Date
$elapsed = ($endTime - $startTime).TotalSeconds
$avgTime = if ($imageCount -gt 0) { [math]::Round($elapsed / $imageCount, 2) } else { 0 }
$throughput = if ($elapsed -gt 0) { [math]::Round($imageCount / $elapsed, 2) } else { 0 }

Write-Output ""
Write-Output "========================================"
Write-Output "  Batch Processing Complete!"
Write-Output "  Processed Images: $imageCount"
Write-Output "  Total Time: $([math]::Round($elapsed, 2)) seconds"
Write-Output "  Average Time: $avgTime seconds/image"
Write-Output "  Throughput: $throughput images/second"
Write-Output "  Concurrency: $Concurrency processes"
Write-Output "  Results: ./output/"
Write-Output "========================================"
