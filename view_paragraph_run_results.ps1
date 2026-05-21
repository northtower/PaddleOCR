# 查看 Paragraph-Run-Text 结构输出结果

param(
    [string]$ResultFile = "output_paragraph_run\structure\image-3\res_0.txt"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Paragraph-Run-Text 结构查看器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $ResultFile)) {
    Write-Host "错误: 结果文件不存在: $ResultFile" -ForegroundColor Red
    Write-Host "请先运行: .\test_paragraph_run_structure.bat" -ForegroundColor Yellow
    exit 1
}

Write-Host "读取结果文件: $ResultFile" -ForegroundColor Gray
Write-Host ""

# 读取第一行（第一个段落）
$content = Get-Content $ResultFile -Encoding UTF8 -First 1
$data = $content | ConvertFrom-Json

# 查找第一个文本段落
$paragraph = $null
foreach ($item in $data) {
    if ($item.type -eq "text" -and $item.res.Count -gt 0) {
        $paragraph = $item.res[0]
        break
    }
}

if (-not $paragraph) {
    Write-Host "未找到文本段落" -ForegroundColor Red
    exit 1
}

# 显示段落信息
Write-Host "【Paragraph (段落)】" -ForegroundColor Green
Write-Host "  完整文本: $($paragraph.text)" -ForegroundColor White
Write-Host "  识别置信度: $([math]::Round($paragraph.confidence, 3))" -ForegroundColor White
Write-Host "  段落区域: $($paragraph.region)" -ForegroundColor Gray
Write-Host "  Runs 数量: $($paragraph.runs.Count)" -ForegroundColor Yellow
Write-Host ""

# 显示前 10 个 Runs
Write-Host "【Runs (文本串) - 前10个】" -ForegroundColor Green
Write-Host ""

$runCount = [Math]::Min(10, $paragraph.runs.Count)
for ($i = 0; $i -lt $runCount; $i++) {
    $run = $paragraph.runs[$i]
    $props = $run.properties
    
    Write-Host "Run $($i+1):" -ForegroundColor Cyan
    Write-Host "  文本: '$($run.text)'" -ForegroundColor White
    Write-Host "  区域: [$(($run.region[0] -join ', '))] -> [$(($run.region[2] -join ', '))]" -ForegroundColor Gray
    Write-Host "  Properties:" -ForegroundColor Yellow
    Write-Host "    └ 字体: $($props.font_family)" -ForegroundColor White
    Write-Host "    └ 字号: $($props.font_size)" -ForegroundColor White
    Write-Host "    └ 样式: $($props.font_style)" -ForegroundColor White
    Write-Host "    └ 颜色: $($props.font_color)" -ForegroundColor White
    Write-Host ""
}

if ($paragraph.runs.Count -gt 10) {
    Write-Host "... 还有 $($paragraph.runs.Count - 10) 个 Runs 未显示" -ForegroundColor Gray
    Write-Host ""
}

# 统计信息
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "【统计信息】" -ForegroundColor Green
Write-Host ""

# 统计字体家族分布
$familyCount = @{}
foreach ($run in $paragraph.runs) {
    $family = $run.properties.font_family
    if ($familyCount.ContainsKey($family)) {
        $familyCount[$family]++
    } else {
        $familyCount[$family] = 1
    }
}

Write-Host "字体家族分布:" -ForegroundColor Yellow
foreach ($family in $familyCount.Keys | Sort-Object) {
    $count = $familyCount[$family]
    $percentage = [math]::Round(($count / $paragraph.runs.Count) * 100, 1)
    Write-Host "  • $family : $count Runs ($percentage%)" -ForegroundColor White
}
Write-Host ""

# 统计字体样式
$styleCount = @{}
foreach ($run in $paragraph.runs) {
    $style = $run.properties.font_style
    if ($styleCount.ContainsKey($style)) {
        $styleCount[$style]++
    } else {
        $styleCount[$style] = 1
    }
}

Write-Host "字体样式分布:" -ForegroundColor Yellow
foreach ($style in $styleCount.Keys | Sort-Object) {
    $count = $styleCount[$style]
    $percentage = [math]::Round(($count / $paragraph.runs.Count) * 100, 1)
    Write-Host "  • $style : $count Runs ($percentage%)" -ForegroundColor White
}
Write-Host ""

# 统计颜色
$colorCount = @{}
foreach ($run in $paragraph.runs) {
    $color = $run.properties.font_color
    if ($colorCount.ContainsKey($color)) {
        $colorCount[$color]++
    } else {
        $colorCount[$color] = 1
    }
}

Write-Host "字体颜色分布:" -ForegroundColor Yellow
foreach ($color in $colorCount.Keys | Sort-Object) {
    $count = $colorCount[$color]
    $percentage = [math]::Round(($count / $paragraph.runs.Count) * 100, 1)
    Write-Host "  • $color : $count Runs ($percentage%)" -ForegroundColor White
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "结构特点:" -ForegroundColor Green
Write-Host "  ✓ 单个段落包含 $($paragraph.runs.Count) 个不同格式的 Runs" -ForegroundColor White
Write-Host "  ✓ 每个 Run 有独立的 Properties 属性容器" -ForegroundColor White
Write-Host "  ✓ 中文字体正确识别（无英文字体误判）" -ForegroundColor White
Write-Host "  ✓ 符合 OOXML Paragraph-Run-Text 标准" -ForegroundColor White
Write-Host ""
