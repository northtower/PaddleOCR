@echo off
chcp 65001 >nul
REM 繁体竖排文本识别测试脚本 - 使用纯OCR模式

echo ========================================
echo 繁体竖排文本识别测试（纯OCR模式）
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

REM 运行繁体竖排识别（使用纯OCR，不使用ppstructure）
echo 正在识别繁体竖排文本...
echo 使用优化参数：
echo   - det_db_thresh=0.2 (降低检测阈值)
echo   - det_db_box_thresh=0.45 (降低框过滤阈值)
echo   - det_db_unclip_ratio=1.6 (扩大检测框)
echo   - det_limit_side_len=1920 (更高分辨率)
echo.

python ../tools/infer/predict_system.py `
  --image_dir="C:\codeBase\pdf\pdf-parser-clib\build\output\h1\image-20.jpg" `
  --det_model_dir="inference/ch_PP-OCRv3_det_infer" `
  --rec_model_dir="inference/ch_PP-OCRv3_rec_infer" `
  --rec_char_dict_path="../ppocr/utils/ppocr_keys_v1.txt" `
  --vis_font_path="../doc/fonts/chinese_cht.ttf" `
  --det_db_thresh=0.2 `
  --det_db_box_thresh=0.45 `
  --det_db_unclip_ratio=1.6 `
  --det_limit_side_len=1920 `
  --use_gpu=True `
  --use_angle_cls=False `
  --draw_img_save_dir="./output/vertical_zhtw" `
  --save_log_path="./output/vertical_zhtw"

if errorlevel 1 (
    echo.
    echo 错误：识别失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 识别完成！
echo 结果保存在: ./output/vertical_zhtw/
echo ========================================
echo.
echo 请检查以下文件：
echo 1. ./output/vertical_zhtw/image-20.jpg - 可视化结果
echo 2. ./output/vertical_zhtw/system_results.txt - 识别的文本内容
echo.

