# PowerShell script to compare all available models
# 对比所有可用模型的识别效果

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host " 繁体古籍OCR - 多模型对比测试" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

Set-Location C:\codeBase\ocr\PaddleOCR\ppstructure

# Activate conda environment
Write-Host "[初始化] 激活conda环境..." -ForegroundColor Green
conda activate paddleocr310
Write-Host ""

# Test configurations
$models = @(
    @{
        Name = "PP-OCRv5简体模型"
        RecModel = "inference/PP-OCRv5_server_rec_infer"
        Dict = "../ppocr/utils/dict/ppocrv5_dict.txt"
        Output = "./output_v5_simplified"
        Color = "Red"
    },
    @{
        Name = "PP-OCRv3繁体模型"
        RecModel = "inference/chinese_cht_PP-OCRv3_rec_infer"
        Dict = "../ppocr/utils/dict/chinese_cht_dict.txt"
        Output = "./output_v3_traditional"
        Color = "Yellow"
    },
    @{
        Name = "PP-OCRv4文档模型"
        RecModel = "inference/PP-OCRv4_server_rec_doc_infer"
        Dict = "../ppocr/utils/dict/ppocrv4_doc_dict.txt"
        Output = "./output_v4_document"
        Color = "Green"
    }
)

$testImage = "C:\codeBase\ocr\PaddleOCR\ppstructure\docs\hlm\p1.jpg"
$testNum = 1

foreach ($model in $models) {
    Write-Host "[$testNum/3] 测试: $($model.Name)" -ForegroundColor $model.Color
    Write-Host "  模型: $($model.RecModel)" -ForegroundColor Cyan
    Write-Host "  字典: $($model.Dict)" -ForegroundColor Cyan
    
    # Check if model exists
    if (-not (Test-Path $model.RecModel)) {
        Write-Host "  ✗ 模型不存在,跳过" -ForegroundColor Red
        Write-Host ""
        $testNum++
        continue
    }
    
    Write-Host "  ✓ 开始识别..." -ForegroundColor White
    
    $startTime = Get-Date
    
    python predict_system.py `
      --image_dir=$testImage `
      --det_model_dir="inference/ch_PP-OCRv4_det_server_infer" `
      --rec_model_dir=$model.RecModel `
      --rec_char_dict_path=$model.Dict `
      --vis_font_path="../doc/fonts/chinese_cht.ttf" `
      --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" `
      --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" `
      --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" `
      --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" `
      --output=$model.Output `
      --return_word_box=True `
      --use_gpu=True `
      --det_db_thresh=0.2 `
      --det_db_box_thresh=0.45 `
      --det_db_unclip_ratio=1.6 `
      --det_limit_side_len=1920 `
      --use_angle_cls=False 2>&1 | Out-Null
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 识别完成 (耗时: $([math]::Round($duration, 2))秒)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 识别失败" -ForegroundColor Red
    }
    
    Write-Host ""
    $testNum++
}

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host " 测试完成! 结果对比" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Display results
foreach ($model in $models) {
    $resultFile = "$($model.Output)/structure/p1/res_0.txt"
    if (Test-Path $resultFile) {
        Write-Host "[$($model.Name)]" -ForegroundColor $model.Color
        Write-Host "输出文件: $resultFile" -ForegroundColor Cyan
        Write-Host "识别结果(前200字符):" -ForegroundColor White
        $content = Get-Content $resultFile -Raw -Encoding UTF8
        if ($content.Length -gt 200) {
            Write-Host $content.Substring(0, 200) -ForegroundColor Gray
            Write-Host "..." -ForegroundColor Gray
        } else {
            Write-Host $content -ForegroundColor Gray
        }
        Write-Host ""
    } else {
        Write-Host "[$($model.Name)] - 结果文件不存在" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host " 建议" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 仔细对比三个模型的识别结果" -ForegroundColor White
Write-Host "2. 选择准确率最高的模型作为基础模型" -ForegroundColor White
Write-Host "3. 如果效果仍不满意,考虑运行微调训练脚本: run_finetune.ps1" -ForegroundColor White
Write-Host ""

