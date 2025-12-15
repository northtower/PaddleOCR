#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量对比 PP-OCRv3 vs PP-OCRv5 的脚本
支持单张图片测试和批量测试
"""
import json
import os
import sys
import subprocess
import time
import argparse
from datetime import datetime
from pathlib import Path

class ModelComparer:
    """模型对比器"""
    
    def __init__(self, old_models, new_models, output_base="./batch_compare_output"):
        """
        初始化对比器
        
        Args:
            old_models: 旧模型配置字典
            new_models: 新模型配置字典
            output_base: 输出基础目录
        """
        self.old_models = old_models
        self.new_models = new_models
        self.output_base = output_base
        
        # 创建输出目录
        os.makedirs(output_base, exist_ok=True)
    
    def run_predict(self, image_path, models_config, output_dir):
        """
        运行单张图片的预测
        
        Args:
            image_path: 图片路径
            models_config: 模型配置
            output_dir: 输出目录
        
        Returns:
            (success, elapsed_time, result_file)
        """
        cmd = [
            "python", "predict_system.py",
            f"--image_dir={image_path}",
            f"--det_model_dir={models_config['det']}",
            f"--rec_model_dir={models_config['rec']}",
            f"--table_model_dir={models_config['table']}",
            f"--layout_model_dir={models_config['layout']}",
            f"--layout_dict_path={models_config['layout_dict']}",
            f"--vis_font_path={models_config['font']}",
            f"--output={output_dir}/",
            "--return_word_box=True",
            "--enable_line_detection=True",
            "--line_min_length=50",
            "--line_max_thickness=5"
        ]
        
        # 如果是新模型，不指定 rec_char_dict_path（自动加载）
        if 'rec_dict' in models_config:
            cmd.append(f"--rec_char_dict_path={models_config['rec_dict']}")
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                # 查找结果文件
                image_name = Path(image_path).stem
                result_file = self._find_result_file(output_dir, image_name)
                return True, elapsed, result_file
            else:
                print(f"❌ 预测失败: {result.stderr[:200]}")
                return False, elapsed, None
                
        except subprocess.TimeoutExpired:
            print(f"❌ 预测超时 (>300s)")
            return False, 300, None
        except Exception as e:
            print(f"❌ 预测异常: {str(e)}")
            return False, 0, None
    
    def _find_result_file(self, output_dir, image_name):
        """查找结果文件"""
        structure_dir = os.path.join(output_dir, "structure")
        if not os.path.exists(structure_dir):
            return None
        
        # 查找包含 image_name 的目录
        for item in os.listdir(structure_dir):
            item_path = os.path.join(structure_dir, item)
            if os.path.isdir(item_path):
                res_file = os.path.join(item_path, "res_0.txt")
                if os.path.exists(res_file):
                    return res_file
        
        return None
    
    def load_results(self, result_file):
        """加载OCR结果"""
        if not result_file or not os.path.exists(result_file):
            return []
        
        results = []
        with open(result_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
        return results
    
    def analyze_results(self, results):
        """分析OCR结果"""
        text_items = [r for r in results if r.get('type') == 'text']
        
        if not text_items:
            return {
                'text_regions': 0,
                'text_lines': 0,
                'avg_confidence': 0.0,
                'high_conf_lines': 0  # 置信度 > 0.95 的行数
            }
        
        total_lines = 0
        total_confidence = 0.0
        high_conf_count = 0
        
        for item in text_items:
            res_list = item.get('res', [])
            total_lines += len(res_list)
            
            for res in res_list:
                conf = res.get('confidence', 0.0)
                total_confidence += conf
                if conf > 0.95:
                    high_conf_count += 1
        
        avg_conf = total_confidence / total_lines if total_lines > 0 else 0.0
        
        return {
            'text_regions': len(text_items),
            'text_lines': total_lines,
            'avg_confidence': avg_conf,
            'high_conf_lines': high_conf_count
        }
    
    def compare_single_image(self, image_path):
        """
        对比单张图片
        
        Args:
            image_path: 图片路径
        
        Returns:
            comparison_result: 对比结果字典
        """
        image_name = os.path.basename(image_path)
        print(f"\n{'='*80}")
        print(f"📸 测试图片: {image_name}")
        print(f"{'='*80}")
        
        # 创建输出目录
        test_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        old_output = os.path.join(self.output_base, f"{test_id}_old", os.path.splitext(image_name)[0])
        new_output = os.path.join(self.output_base, f"{test_id}_new", os.path.splitext(image_name)[0])
        
        # 测试旧模型
        print(f"\n🔄 测试 PP-OCRv3 (旧模型)...")
        old_success, old_time, old_result_file = self.run_predict(image_path, self.old_models, old_output)
        
        if old_success:
            print(f"✅ PP-OCRv3 完成 (耗时: {old_time:.2f}s)")
        else:
            print(f"❌ PP-OCRv3 失败")
        
        # 测试新模型
        print(f"\n🔄 测试 PP-OCRv5 (新模型)...")
        new_success, new_time, new_result_file = self.run_predict(image_path, self.new_models, new_output)
        
        if new_success:
            print(f"✅ PP-OCRv5 完成 (耗时: {new_time:.2f}s)")
        else:
            print(f"❌ PP-OCRv5 失败")
        
        # 分析结果
        old_results = self.load_results(old_result_file) if old_success else []
        new_results = self.load_results(new_result_file) if new_success else []
        
        old_analysis = self.analyze_results(old_results)
        new_analysis = self.analyze_results(new_results)
        
        # 生成对比报告
        comparison = {
            'image': image_name,
            'image_path': image_path,
            'old_model': {
                'success': old_success,
                'time': old_time,
                'result_file': old_result_file,
                'analysis': old_analysis
            },
            'new_model': {
                'success': new_success,
                'time': new_time,
                'result_file': new_result_file,
                'analysis': new_analysis
            }
        }
        
        # 打印对比结果
        self._print_comparison(comparison)
        
        return comparison
    
    def _print_comparison(self, comp):
        """打印单张图片的对比结果"""
        print(f"\n{'─'*80}")
        print(f"📊 对比结果")
        print(f"{'─'*80}")
        
        if comp['old_model']['success'] and comp['new_model']['success']:
            old_ana = comp['old_model']['analysis']
            new_ana = comp['new_model']['analysis']
            
            print(f"\n{'指标':<25} {'PP-OCRv3':<20} {'PP-OCRv5':<20} {'变化':<15}")
            print(f"{'-'*80}")
            
            # 处理时间
            time_diff = comp['new_model']['time'] - comp['old_model']['time']
            time_pct = (time_diff / comp['old_model']['time'] * 100) if comp['old_model']['time'] > 0 else 0
            print(f"{'处理时间(秒)':<25} {comp['old_model']['time']:<20.2f} {comp['new_model']['time']:<20.2f} {time_diff:+.2f} ({time_pct:+.1f}%)")
            
            # 文本行数
            lines_diff = new_ana['text_lines'] - old_ana['text_lines']
            lines_pct = (lines_diff / old_ana['text_lines'] * 100) if old_ana['text_lines'] > 0 else 0
            print(f"{'识别文本行数':<25} {old_ana['text_lines']:<20} {new_ana['text_lines']:<20} {lines_diff:+d} ({lines_pct:+.1f}%)")
            
            # 平均置信度
            conf_diff = new_ana['avg_confidence'] - old_ana['avg_confidence']
            conf_pct = (conf_diff / old_ana['avg_confidence'] * 100) if old_ana['avg_confidence'] > 0 else 0
            print(f"{'平均置信度':<25} {old_ana['avg_confidence']:<20.4f} {new_ana['avg_confidence']:<20.4f} {conf_diff:+.4f} ({conf_pct:+.2f}%)")
            
            # 高置信度行数
            hconf_diff = new_ana['high_conf_lines'] - old_ana['high_conf_lines']
            print(f"{'高置信度行数(>0.95)':<25} {old_ana['high_conf_lines']:<20} {new_ana['high_conf_lines']:<20} {hconf_diff:+d}")
            
            # 判断
            if conf_diff > 0.01:
                print(f"\n✅ PP-OCRv5 在置信度上有明显提升 (+{conf_pct:.2f}%)")
            elif conf_diff > 0:
                print(f"\n✅ PP-OCRv5 在置信度上略有提升 (+{conf_pct:.2f}%)")
            else:
                print(f"\n⚠️  两个模型置信度相近")
        
        elif comp['old_model']['success']:
            print(f"\n⚠️  仅旧模型成功")
        elif comp['new_model']['success']:
            print(f"\n⚠️  仅新模型成功")
        else:
            print(f"\n❌ 两个模型均失败")
    
    def generate_batch_report(self, comparisons, output_file):
        """生成批量测试报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# PP-OCRv3 vs PP-OCRv5 批量对比报告\n\n")
            f.write(f"**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**测试图片数量：** {len(comparisons)}\n\n")
            f.write("---\n\n")
            
            # 统计
            success_both = sum(1 for c in comparisons if c['old_model']['success'] and c['new_model']['success'])
            success_old_only = sum(1 for c in comparisons if c['old_model']['success'] and not c['new_model']['success'])
            success_new_only = sum(1 for c in comparisons if not c['old_model']['success'] and c['new_model']['success'])
            fail_both = sum(1 for c in comparisons if not c['old_model']['success'] and not c['new_model']['success'])
            
            f.write("## 测试概览\n\n")
            f.write(f"- ✅ 两个模型均成功: {success_both}\n")
            f.write(f"- ⚠️  仅旧模型成功: {success_old_only}\n")
            f.write(f"- ⚠️  仅新模型成功: {success_new_only}\n")
            f.write(f"- ❌ 两个模型均失败: {fail_both}\n\n")
            
            # 详细对比
            f.write("## 详细对比结果\n\n")
            f.write("| 图片 | 旧模型耗时 | 新模型耗时 | 旧模型行数 | 新模型行数 | 旧模型置信度 | 新模型置信度 | 置信度提升 |\n")
            f.write("|------|-----------|-----------|-----------|-----------|-------------|-------------|----------|\n")
            
            for comp in comparisons:
                if comp['old_model']['success'] and comp['new_model']['success']:
                    old_ana = comp['old_model']['analysis']
                    new_ana = comp['new_model']['analysis']
                    conf_diff = new_ana['avg_confidence'] - old_ana['avg_confidence']
                    conf_pct = (conf_diff / old_ana['avg_confidence'] * 100) if old_ana['avg_confidence'] > 0 else 0
                    
                    f.write(f"| {comp['image']} | {comp['old_model']['time']:.2f}s | {comp['new_model']['time']:.2f}s | ")
                    f.write(f"{old_ana['text_lines']} | {new_ana['text_lines']} | ")
                    f.write(f"{old_ana['avg_confidence']:.4f} | {new_ana['avg_confidence']:.4f} | ")
                    f.write(f"{conf_pct:+.2f}% |\n")
                else:
                    status = "失败"
                    if comp['old_model']['success']:
                        status = "仅旧模型成功"
                    elif comp['new_model']['success']:
                        status = "仅新模型成功"
                    f.write(f"| {comp['image']} | - | - | - | - | - | - | {status} |\n")
            
            # 平均统计
            if success_both > 0:
                valid_comps = [c for c in comparisons if c['old_model']['success'] and c['new_model']['success']]
                
                avg_old_time = sum(c['old_model']['time'] for c in valid_comps) / len(valid_comps)
                avg_new_time = sum(c['new_model']['time'] for c in valid_comps) / len(valid_comps)
                
                avg_old_conf = sum(c['old_model']['analysis']['avg_confidence'] for c in valid_comps) / len(valid_comps)
                avg_new_conf = sum(c['new_model']['analysis']['avg_confidence'] for c in valid_comps) / len(valid_comps)
                
                conf_improvement = ((avg_new_conf - avg_old_conf) / avg_old_conf * 100) if avg_old_conf > 0 else 0
                
                f.write("\n## 平均统计\n\n")
                f.write(f"- **平均处理时间 (旧)**: {avg_old_time:.2f}s\n")
                f.write(f"- **平均处理时间 (新)**: {avg_new_time:.2f}s\n")
                f.write(f"- **平均置信度 (旧)**: {avg_old_conf:.4f}\n")
                f.write(f"- **平均置信度 (新)**: {avg_new_conf:.4f}\n")
                f.write(f"- **置信度提升**: {conf_improvement:+.2f}%\n\n")
                
                # 结论
                f.write("## 结论\n\n")
                if conf_improvement > 3:
                    f.write(f"✅ **PP-OCRv5 在识别准确性上有显著提升**，平均置信度提升 {conf_improvement:.2f}%\n\n")
                elif conf_improvement > 1:
                    f.write(f"✅ **PP-OCRv5 在识别准确性上有所提升**，平均置信度提升 {conf_improvement:.2f}%\n\n")
                else:
                    f.write(f"⚠️  **两个模型表现相近**，平均置信度差异为 {conf_improvement:.2f}%\n\n")
                
                f.write(f"**推荐**: {'升级到 PP-OCRv5' if conf_improvement > 1 else '根据实际需求选择'}\n")
        
        print(f"\n📄 批量测试报告已生成: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='批量对比 PP-OCRv3 vs PP-OCRv5')
    parser.add_argument('--image', type=str, help='单张图片路径（测试用）')
    parser.add_argument('--image_dir', type=str, help='图片目录（批量测试）')
    parser.add_argument('--output', type=str, default='./batch_compare_output', help='输出目录')
    
    args = parser.parse_args()
    
    # 配置旧模型
    old_models = {
        'det': 'inference/ch_PP-OCRv3_det_infer',
        'rec': 'inference/ch_PP-OCRv3_rec_infer',
        'rec_dict': '../ppocr/utils/ppocr_keys_v1.txt',
        'table': 'inference/ch_ppstructure_mobile_v2.0_SLANet_infer',
        'layout': 'inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer',
        'layout_dict': '../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt',
        'font': '../doc/fonts/chinese_cht.ttf'
    }
    
    # 配置新模型（不指定 rec_dict，让其自动加载）
    new_models = {
        'det': 'inference/new-version/PP-OCRv5_server_det_infer',
        'rec': 'inference/new-version/PP-OCRv5_server_rec_infer',
        'table': 'inference/new-version/SLANeXt_wired_infer',
        'layout': 'inference/picodet_lcnet_x1_0_fgd_layout_cdla_infer',
        'layout_dict': '../ppocr/utils/dict/layout_dict/layout_cdla_dict.txt',
        'font': '../doc/fonts/chinese_cht.ttf'
    }
    
    # 创建对比器
    comparer = ModelComparer(old_models, new_models, args.output)
    
    if args.image:
        # 单张图片测试
        print(f"\n🎯 单张图片测试模式")
        if not os.path.exists(args.image):
            print(f"❌ 图片不存在: {args.image}")
            return
        
        comparison = comparer.compare_single_image(args.image)
        
        # 生成单图报告
        report_file = os.path.join(args.output, f"report_{os.path.basename(args.image).split('.')[0]}.md")
        comparer.generate_batch_report([comparison], report_file)
        
    elif args.image_dir:
        # 批量测试
        print(f"\n🎯 批量测试模式")
        if not os.path.exists(args.image_dir):
            print(f"❌ 目录不存在: {args.image_dir}")
            return
        
        # 获取所有图片
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
            image_files.extend(Path(args.image_dir).rglob(ext))
        
        if not image_files:
            print(f"❌ 目录中没有找到图片: {args.image_dir}")
            return
        
        print(f"📂 找到 {len(image_files)} 张图片")
        
        # 批量测试
        comparisons = []
        for idx, image_file in enumerate(image_files, 1):
            print(f"\n{'='*80}")
            print(f"进度: {idx}/{len(image_files)}")
            comparison = comparer.compare_single_image(str(image_file))
            comparisons.append(comparison)
        
        # 生成批量报告
        report_file = os.path.join(args.output, f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        comparer.generate_batch_report(comparisons, report_file)
        
    else:
        parser.print_help()
        print("\n示例:")
        print("  # 单张图片测试")
        print("  python batch_compare.py --image docs/img/0a4ad205277a55592971b5ebf7970cbb/image-3.jpg")
        print("\n  # 批量测试")
        print("  python batch_compare.py --image_dir docs/img/")


if __name__ == '__main__':
    main()

