# 故障排查指南 (Troubleshooting Guide)

## 问题1: PP-OCRv5 报错 `IndexError: list index out of range`

### 问题描述
运行 PP-OCRv5 模型时出现以下错误：
```
File "/ppocr/postprocess/rec_postprocess.py", line 157, in <listcomp>
    self.character[text_id] for text_id in text_index[batch_idx][selection]
IndexError: list index out of range
```

### 根本原因
**字典文件不匹配！** 不同版本的 PP-OCR 模型使用不同的字典文件：

| 模型版本 | 字典文件 | 字符数量 |
|---------|---------|---------|
| PP-OCRv3 及更早版本 | `ppocr/utils/ppocr_keys_v1.txt` | 6,623 |
| **PP-OCRv5** | `ppocr/utils/dict/ppocrv5_dict.txt` | **18,383** |

PP-OCRv5 模型输出的字符索引范围是 0-18382，但如果使用旧字典 `ppocr_keys_v1.txt`（只有 6623 个字符），当模型输出索引 > 6622 时就会越界。

### 解决方案

✅ **使用正确的字典文件：**

```bash
# PP-OCRv5 (新版本)
python predict_system.py \
  --det_model_dir=inference/new-version/PP-OCRv5_server_det_infer \
  --rec_model_dir=inference/new-version/PP-OCRv5_server_rec_infer \
  --rec_char_dict_path=../ppocr/utils/dict/ppocrv5_dict.txt \  # ✅ 使用 ppocrv5_dict.txt
  ...

# PP-OCRv3 (旧版本)
python predict_system.py \
  --det_model_dir=inference/ch_PP-OCRv3_det_infer \
  --rec_model_dir=inference/ch_PP-OCRv3_rec_infer \
  --rec_char_dict_path=../ppocr/utils/ppocr_keys_v1.txt \  # ✅ 使用 ppocr_keys_v1.txt
  ...
```

---

## 问题2: pip install 导致 numpy 版本冲突

### 问题描述
执行 `pip install -r requirements.txt` 后出现 numpy 版本冲突：
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
faiss-cpu 1.8.0.post1 requires numpy<2.0,>=1.0, but you have numpy 2.0.2 which is incompatible.
paddlex 3.0.0rc1 requires numpy==1.24.4, but you have numpy 2.0.2 which is incompatible.
```

### 根本原因
`requirements.txt` 中 `numpy` 没有版本限制，pip 会自动安装最新版 numpy 2.0.2，导致与其他依赖包不兼容。

### 解决方案

✅ **已更新 `requirements.txt`，固定兼容版本：**

```txt
numpy<2.0,>=1.19.0          # 限制 numpy < 2.0
albumentations<2.0.0         # 限制 albumentations < 2.0
albucore<0.0.20             # 限制 albucore < 0.0.20
```

**重新安装依赖（关闭VPN后更快）：**

```bash
conda activate paddlex_env
cd /Users/zoutao03/codeBase/ocr/PaddleOCR
pip install "numpy==1.24.4" "albumentations<2.0.0" "albucore<0.0.20" --force-reinstall
```

---

## 快速参考

### 模型与字典对应关系

| 模型系列 | 识别模型目录 | 字典文件 |
|---------|------------|---------|
| PP-OCRv3 | `ch_PP-OCRv3_rec_infer` | `ppocr/utils/ppocr_keys_v1.txt` |
| PP-OCRv4 | `ch_PP-OCRv4_rec_infer` | `ppocr/utils/ppocr_keys_v1.txt` |
| PP-OCRv5 | `PP-OCRv5_server_rec_infer` 或 `PP-OCRv5_mobile_rec_infer` | `ppocr/utils/dict/ppocrv5_dict.txt` |

### 检查字典文件
```bash
# 查看字典文件字符数
wc -l ppocr/utils/ppocr_keys_v1.txt      # 应该显示 6623
wc -l ppocr/utils/dict/ppocrv5_dict.txt  # 应该显示 18383
```

### 验证环境
```bash
conda activate paddlex_env
python -c "import numpy; print('numpy:', numpy.__version__)"  # 应该是 1.24.4
python -c "import paddle; print('paddle:', paddle.__version__)"
```

---

## 相关配置文件
- PP-OCRv5 配置: `configs/rec/PP-OCRv5/PP-OCRv5_server_rec.yml` (第18行定义字典路径)
- 依赖配置: `requirements.txt`
- 运行示例: `ppstructure/RunCode.md`

