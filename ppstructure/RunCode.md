conda activate paddlex_env
---
pd 博客
https://github.com/PaddlePaddle/PaddleOCR/pull/10515
https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/ppstructure/kie/README_ch.md
https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/ppstructure/docs/quickstart.md#pp-structure-%E5%BF%AB%E9%80%9F%E5%BC%80%E5%A7%8B

测试分栏数据
python predict_system.py \
    --image_dir=./docs/doc-struct/l21.jpg \
    --det_model_dir=inference/ch_PP-OCRv3_det_infer \
    --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
    --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
    --table_model_dir=inference/ch_ppstructure_mobile_v2.0_SLANet_infer \
    --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
    --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
    --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
    --vis_font_path=../doc/fonts/chinese_cht.ttf \
    --recovery=True \
    --output=../output/ \
    --return_word_box=True


单字位置
python predict_system.py \
    --image_dir=./docs/table/4.jpg \
    --det_model_dir=inference/ch_PP-OCRv3_det_infer \
    --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
    --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
    --table_model_dir=inference/ch_ppstructure_mobile_v2.0_SLANet_infer \
    --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
    --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
    --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
    --vis_font_path=../doc/fonts/chinese_cht.ttf \
    --recovery=True \
    --output=../output/ \
    --return_word_box=True


--
python predict_system.py \
  --image_dir=./docs/table/4.jpg \
  --det_model_dir=inference/ch_PP-OCRv3_det_infer \
  --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
  --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
  --table_model_dir=inference/ch_ppstructure_mobile_v2.0_SLANet_infer \
  --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
  --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
  --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
  --vis_font_path=../doc/fonts/chinese_cht.ttf \
  --recovery=True \
  --output=./output/ \
  --return_word_box=True

python predict_system.py \
  --image_dir=/Users/zoutao03/codeBase/pdf/PaddleOCR/ppstructure/docs/img/0a4ad205277a55592971b5ebf7970cbb/image-0.jpg \
  --det_model_dir=inference/ch_PP-OCRv3_det_infer \
  --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
  --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
  --table_model_dir=inference/ch_ppstructure_mobile_v2.0_SLANet_infer \
  --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
  --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
  --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
  --vis_font_path=../doc/fonts/chinese_cht.ttf \
  --output=./output/ \
  --return_word_box=True

--线条

python predict_system.py \
  --image_dir=/Users/zoutao03/codeBase/ocr/PaddleOCR/ppstructure/docs/img/0a4ad205277a55592971b5ebf7970cbb/image-3.jpg \
  --det_model_dir=inference/ch_PP-OCRv3_det_infer \
  --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
  --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
  --table_model_dir=inference/ch_ppstructure_mobile_v2.0_SLANet_infer \
  --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
  --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
  --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
  --vis_font_path=../doc/fonts/chinese_cht.ttf \
  --output=./output/ \
  --return_word_box=True \
  --enable_line_detection=True \
  --line_min_length=50 \
  --line_max_thickness=5



python predict_system.py \
    --image_dir=/Users/zoutao03/codeBase/python/paddleDemo/pdf-ocr/00001da520bfd5bf6f7870a9fda70e3c5f4e.jpg \
    --det_model_dir=inference/ch_PP-OCRv3_det_infer \
    --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
    --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
    --table_model_dir=inference/ch_ppstructure_mobile_v2.0_SLANet_infer \
    --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
    --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
    --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
    --vis_font_path=../doc/fonts/chinese_cht.ttf \
    --return_word_box=True

--测评
python predict_system.py \
    --image_dir=/Users/zoutao03/codeBase/python/paddleDemo/pdf-ocr/00001c5792a633b72c3666f322c75204a5fe.jpg \
    --det_model_dir=inference/ch_PP-OCRv3_det_infer \
    --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
    --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \
    --table_model_dir=inference/ch_ppstructure_mobile_v2.0_SLANet_infer \
    --table_char_dict_path=../ppocr/utils/dict/table_structure_dict_ch.txt \
    --layout_model_dir=inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer \
    --layout_dict_path=../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt \
    --vis_font_path=../doc/fonts/chinese_cht.ttf \
    --return_word_box=True


检测
--image_dir="/Users/zoutao03/codeBase/python/paddleDemo/pdf-ocr/00001c5792a633b72c3666f322c75204a5fe.jpg" --det_model_dir="./inference/ch_PP-OCRv2_det_infer/" --cls_model_dir="./inference/cls/" --rec_model_dir="./inference/ch_PP-OCRv2_rec_infer/" --use_angle_cls=true   


--image_dir="/Users/zoutao03/codeBase/python/paddleDemo/pdf-ocr/00001c5792a633b72c3666f322c75204a5fe.jpg" --use_angle_cls=true   