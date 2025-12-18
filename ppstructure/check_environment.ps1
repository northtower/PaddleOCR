# Check PaddleOCR Environment

# Set encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Output "========================================"
Write-Output "  PaddleOCR Environment Check"
Write-Output "========================================"
Write-Output ""

# Check Conda environment
Write-Output "1. Conda Environment Check"
$currentEnv = $env:CONDA_DEFAULT_ENV
if ($currentEnv) {
    Write-Output "   Current Environment: $currentEnv"
    if ($currentEnv -eq "paddleocr310") {
        Write-Output "   [OK] Correct environment"
    } else {
        Write-Output "   [WARNING] Recommend using paddleocr310"
    }
} else {
    Write-Output "   [ERROR] No Conda environment activated"
    Write-Output "   Run: conda activate paddleocr310"
}

Write-Output ""
Write-Output "2. Python Environment Check"
python --version
Write-Output ""

# Check key dependencies
Write-Output "3. Key Dependencies Check"
$packages = @(
    @{Name="paddle"; Import="paddle"},
    @{Name="opencv-python"; Import="cv2"},
    @{Name="pillow"; Import="PIL"},
    @{Name="numpy"; Import="numpy"},
    @{Name="premailer"; Import="premailer"},
    @{Name="tablepyxl"; Import="tablepyxl"}
)

foreach ($pkg in $packages) {
    try {
        $result = python -c "import $($pkg.Import); print('OK')" 2>&1
        if ($result -match "OK") {
            Write-Output "   [OK] $($pkg.Name)"
        } else {
            Write-Output "   [MISSING] $($pkg.Name)"
            Write-Output "      Install: pip install $($pkg.Name)"
        }
    } catch {
        Write-Output "   [MISSING] $($pkg.Name)"
        Write-Output "      Install: pip install $($pkg.Name)"
    }
}

Write-Output ""
Write-Output "4. GPU Check"
try {
    $gpuResult = python -c "import paddle; print('GPU' if paddle.is_compiled_with_cuda() else 'CPU')" 2>&1
    if ($gpuResult -match "GPU") {
        Write-Output "   [OK] GPU Available"
    } else {
        Write-Output "   [WARNING] CPU Only"
    }
} catch {
    Write-Output "   [ERROR] Cannot check GPU status"
}

Write-Output ""
Write-Output "5. Model Files Check"
$models = @(
    "inference/ch_PP-OCRv3_det_infer/inference.pdiparams",
    "inference/ch_PP-OCRv3_rec_infer/inference.pdiparams",
    "inference/ch_ppstructure_mobile_v2.0_SLANet_infer/inference.pdiparams",
    "inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer/model.pdiparams"
)

foreach ($model in $models) {
    if (Test-Path $model) {
        $size = [math]::Round((Get-Item $model).Length / 1MB, 1)
        Write-Output "   [OK] $model (${size}MB)"
    } else {
        Write-Output "   [MISSING] $model"
    }
}

Write-Output ""
Write-Output "========================================"
Write-Output "  Environment Check Complete"
Write-Output "========================================"
Write-Output ""
Write-Output "To install missing dependencies, run:"
Write-Output "  .\install_dependencies.ps1"
