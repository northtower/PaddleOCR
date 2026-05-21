@echo off
chcp 65001 >nul
REM 繁体竖排文本批量识别脚本 - 使用纯OCR模式

echo ========================================
echo 繁体竖排文本批量识别（纯OCR模式）
echo ========================================
echo.

REM 激活 conda 环境
call conda activate paddleocr310
if errorlevel 1 (
    echo 错误：无法激活 paddleocr310 环境
    pause
    exit /b 1
)

echo 当前环境: paddleocr310
echo.

REM 设置环境变量
set CUDA_VISIBLE_DEVICES=0
set FLAGS_allocator_strategy=auto_growth

REM 运行批量识别
echo 正在批量识别繁体竖排文本...
echo.
echo 输入目录: C:\codeBase\pdf\pdf-parser-clib\build\output\h1
echo 输出目录: .\output\vertical_zhtw_batch
echo.
echo 使用优化参数：
echo   - det_db_thresh=0.2 (降低检测阈值)
echo   - det_db_box_thresh=0.45 (降低框过滤阈值)
echo   - det_db_unclip_ratio=1.6 (扩大检测框)
echo   - det_limit_side_len=1920 (更高分辨率)
echo.

python "batch_pure_ocr_zhtw .py"

if errorlevel 1 (
    echo.
    echo 错误：批量识别失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 批量识别完成！
echo ========================================
echo.
echo 结果保存在: .\output\vertical_zhtw_batch\
echo.
echo 每个图片都有独立的子目录，包含：
echo   1. <图片名>.jpg - 可视化结果（带文本框）
echo   2. system_results.txt - 检测到的文本和坐标
echo   3. ocr_result.txt - 完整的OCR输出日志
echo.

pause

