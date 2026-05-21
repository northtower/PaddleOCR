@echo off
chcp 65001 >nul
REM 繁体竖排文本识别测试脚本
REM 解决三个核心问题：
REM 1. 语序错误：繁体竖排从右向左
REM 2. 繁体字识别错误
REM 3. show_0.jpg 可视化错误

echo ========================================
echo 繁体竖排文本识别测试
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

REM 运行繁体竖排识别
echo 正在识别繁体竖排文本...
echo.

python predict_system_vertical_zhtw.py ^
  --image_dir="C:\codeBase\pdf\pdf-parser-clib\build\output\h1\image-20.jpg" ^
  --det_model_dir="inference/ch_PP-OCRv3_det_infer" ^
  --rec_model_dir="inference/ch_PP-OCRv3_rec_infer" ^
  --rec_char_dict_path="../ppocr/utils/ppocr_keys_v1.txt" ^
  --table_model_dir="inference/ch_ppstructure_mobile_v2.0_SLANet_infer" ^
  --table_char_dict_path="../ppocr/utils/dict/table_structure_dict_ch.txt" ^
  --layout_model_dir="inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer" ^
  --layout_dict_path="../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt" ^
  --vis_font_path="../doc/fonts/chinese_cht.ttf" ^
  --output="./output/vertical_zhtw/" ^
  --return_word_box=True ^
  --use_gpu=True

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
echo 1. show_0.jpg - 可视化结果（应正确显示竖排文字）
echo 2. res_0.txt - 文本结果（应从右向左排序）
echo.

