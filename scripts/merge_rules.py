#!/usr/bin/env python3
"""
规则合并 v4.2 (优化版)
优化：纯 set 去重、内存优化、更好的排序
"""

import time
from pathlib import Path
from collections import defaultdict

TEMP_DIR = Path("temp")
OUTPUT_DIR = Path("rules")
OUTPUT_DIR.mkdir(exist_ok=True)

class RuleProcessor:
    def __init__(self):
        self.rules = set()  # 直接使用 set，Python 的哈希优化足够好
        self.stats = {
            'total_lines': 0,
            'comment_lines': 0,
            'duplicates': 0,
            'invalid_lines': 0,
        }
        self.category_counts = defaultdict(int)
    
    def get_rule_category(self, rule):
        """快速规则分类"""
        if rule.startswith('@@'):
            return 'allow'
        elif rule.startswith('/') and rule.endswith('/'):
            return 'regex'
        elif rule.startswith('||') and rule.endswith('^'):
            return 'domain'
        elif rule.startswith(('0.0.0.0 ', '127.0.0.1 ', '::1 ')):
            return 'hosts'
        else:
            return 'other'
    
    def normalize_rule(self, line):
        """标准化规则"""
        # 移除行内注释
        if '!' in line:
            line = line.split('!', 1)[0]
        
        line = line.strip()
        if not line:
            return None
        
        # 处理 $ 选项
        if '$' in line:
            parts = line.split('$', 1)
            main = parts[0].strip()
            options = parts[1].strip()
            # 标准化选项顺序（按字母排序，保证一致性）
            if ',' in options:
                opts = sorted([opt.strip() for opt in options.split(',')])
                options = ','.join(opts)
            return f"{main}${options}"
        
        return line
    
    def process_file(self, file_path):
        """处理单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    self.stats['total_lines'] += 1
                    
                    line = line.rstrip('\n')
                    if not line:
                        continue
                    
                    if line.startswith('!'):
                        self.stats['comment_lines'] += 1
                        continue
                    
                    rule = self.normalize_rule(line)
                    if not rule:
                        self.stats['invalid_lines'] += 1
                        continue
                    
                    if rule in self.rules:
                        self.stats['duplicates'] += 1
                    else:
                        self.rules.add(rule)
                        category = self.get_rule_category(rule)
                        self.category_counts[category] += 1
                        
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    for line in f:
                        self.stats['total_lines'] += 1
                        
                        line = line.rstrip('\n')
                        if not line or line.startswith('!'):
                            continue
                        
                        rule = self.normalize_rule(line)
                        if rule and rule not in self.rules:
                            self.rules.add(rule)
                            category = self.get_rule_category(rule)
                            self.category_counts[category] += 1
            except:
                self.stats['invalid_lines'] += 1
                print(f"无法解码文件: {file_path.name}")
    
    def sort_key(self, rule):
        """排序键函数"""
        category = self.get_rule_category(rule)
        
        # 优先级顺序：allow > regex > domain > hosts > other
        priority = {
            'allow': 0,
            'regex': 1,
            'domain': 2,
            'hosts': 3,
            'other': 4,
        }.get(category, 5)
        
        # 对于允许规则，按原样排序
        if category == 'allow':
            return (priority, rule)
        
        # 其他规则按长度和内容排序
        return (priority, len(rule), rule)
    
    def save_rules(self, output_path):
        """保存合并后的规则"""
        print(f"正在排序 {len(self.rules):,} 条规则...")
        
        sorted_rules = sorted(self.rules, key=self.sort_key)
        
        print(f"正在写入文件...")
        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            # 文件头
            f.write(f"! 规则合并文件\n")
            f.write(f"! 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"! 总规则数: {len(sorted_rules):,}\n")
            f.write("!\n")
            
            # 按分类写入
            current_category = None
            for rule in sorted_rules:
                category = self.get_rule_category(rule)
                if category != current_category:
                    f.write(f"\n! === {category.upper()} 规则 ({self.category_counts[category]:,}) ===\n")
                    current_category = category
                f.write(f"{rule}\n")
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("合并统计:")
        print("-"*60)
        print(f"处理总行数: {self.stats['total_lines']:,}")
        print(f"注释行数: {self.stats['comment_lines']:,}")
        print(f"重复规则: {self.stats['duplicates']:,}")
        print(f"无效行数: {self.stats['invalid_lines']:,}")
        print(f"唯一规则: {len(self.rules):,}")
        print("\n规则分类:")
        print("-"*60)
        total = sum(self.category_counts.values())
        for category in ['allow', 'regex', 'domain', 'hosts', 'other']:
            count = self.category_counts[category]
            if count > 0:
                percentage = count / total * 100
                print(f"  {category:10}: {count:>8,} ({percentage:5.1f}%)")
        print("="*60)

def main():
    """主函数"""
    start_time = time.time()
    
    if not TEMP_DIR.exists():
        print(f"错误: 临时目录不存在: {TEMP_DIR}")
        return
    
    # 获取所有规则文件
    rule_files = list(TEMP_DIR.glob("*.txt"))
    if not rule_files:
        print("错误: 没有找到规则文件")
        return
    
    print(f"找到 {len(rule_files)} 个规则文件")
    
    # 处理文件
    processor = RuleProcessor()
    
    for i, file_path in enumerate(rule_files, 1):
        print(f"[{i:3}/{len(rule_files)}] 处理: {file_path.name:<30}", end='\r')
        processor.process_file(file_path)
    
    print()  # 换行
    processor.print_stats()
    
    # 保存结果
    output_file = OUTPUT_DIR / "merged_all.txt"
    processor.save_rules(output_file)
    print(f"规则已保存到: {output_file}")
    
    # 保存统计
    stats_file = OUTPUT_DIR / "merge_stats.txt"
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write(f"合并时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"源文件数: {len(rule_files)}\n")
        f.write(f"最终规则数: {len(processor.rules):,}\n")
        for category, count in processor.category_counts.items():
            f.write(f"{category}: {count}\n")
    
    elapsed = time.time() - start_time
    print(f"\n总耗时: {elapsed:.1f}秒")

if __name__ == "__main__":
    main()