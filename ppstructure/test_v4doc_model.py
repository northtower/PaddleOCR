from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import os

# 1. 设置路径 (请确保文件真实存在)
# 模型路径: 解压后的文件夹路径
REC_MODEL_DIR = r'./inference/PP-OCRv4_server_rec_doc_infer'
# 字典路径: 必须是 doc 专用字典!
REC_DOC_DICT = r'../ppocr/utils/dict/ppocrv4_doc_dict.txt'
# 检测模型: 继续用 V4 Server Det
DET_MODEL_DIR = r'./inference/ch_PP-OCRv4_det_server_infer'

# 检查文件是否存在，防止报错
if not os.path.exists(REC_DOC_DICT):
    print(f"❌ 错误: 找不到字典文件 {REC_DOC_DICT}，请先下载！")
    exit()

# 2. 初始化 PaddleOCR
# 关键点: 
# - lang='ch' (让系统加载基础配置)
# - rec_model_dir (强制指定 doc 模型)
# - rec_char_dict_path (强制指定 doc 字典)
ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch', 
    det_model_dir=DET_MODEL_DIR,
    rec_model_dir=REC_MODEL_DIR,
    rec_char_dict_path=REC_DOC_DICT,  # <--- 核心修改：必须指定这个字典
    use_gpu=True,
    show_log=True
)

# 3. 预测
img_path = './doc/imgs/image-20.jpg'
result = ocr.ocr(img_path, cls=True)

# 4. 打印结果
if result and result[0]:
    for line in result[0]:
        print(f"文本: {line[1][0]} | 置信度: {line[1][1]:.4f}")

    # 可视化保存
    image = Image.open(img_path).convert('RGB')
    boxes = [line[0] for line in result[0]]
    txts = [line[1][0] for line in result[0]]
    scores = [line[1][1] for line in result[0]]
    im_show = draw_ocr(image, boxes, txts, scores, font_path='./doc/fonts/simsun.ttc')
    Image.fromarray(im_show).save('result_doc_v4.jpg')
    print("✅ 结果已保存为 result_doc_v4.jpg")
else:
    print("未识别到文本")