# PowerShell script to test Traditional Chinese OCR
# 繁体中文OCR测试脚本

Set-Location C:\codeBase\ocr\PaddleOCR\ppstructure

# Activate conda environment
conda activate paddleocr310

# Run OCR with Traditional Chinese model
python predict_system.py `
  --image_dir="C:\codeBase\ocr\PaddleOCR\ppstructure\docs\hlm\p1.jpg" `
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

Write-Host "OCR processing completed. Check output folder for results."

