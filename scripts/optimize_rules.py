#!/usr/bin/env python3
"""
规则精简 v4.2 (GitHub Actions 优化版)
优化：确定性算法、Git友好、性能优化
"""

import time
from pathlib import Path

TARGET_RULES = 150000
MIN_RULES = 100000
MAX_RULES = 200000

# 重要关键词（提高保留优先级）
IMPORTANT_KEYWORDS = {
    'doubleclick', 'google-analytics', 'facebook', 'tracking',
    'adsystem', 'adservice', 'adserver', 'analytics',
    'cookie', 'beacon', 'pixel', 'metrics', 'telemetry',
    'spyware', 'malware', 'phishing', 'malicious',
}

# 通用域名（降低优先级）
COMMON_DOMAINS = {
    'google', 'youtube', 'facebook', 'twitter', 'instagram',
    'amazon', 'microsoft', 'apple', 'cloudflare', 'akamai',
}

class RuleOptimizer:
    def __init__(self):
        self.allow_rules = []   # 允许规则（全部保留）
        self.block_rules = []   # 阻止规则（需要筛选）
        self.stats = {
            'total': 0,
            'allow': 0,
            'block': 0,
            'selected': 0,
        }
    
    def load_rules(self, input_file):
        """加载规则文件"""
        print(f"加载规则文件: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('!'):
                    continue
                
                self.stats['total'] += 1
                
                if line.startswith('@@'):
                    self.allow_rules.append(line)
                    self.stats['allow'] += 1
                else:
                    self.block_rules.append(line)
                    self.stats['block'] += 1
        
        print(f"加载完成: 总共 {self.stats['total']:,} 条规则")
        print(f"  允许规则: {self.stats['allow']:,}")
        print(f"  阻止规则: {self.stats['block']:,}")
    
    def calculate_rule_score(self, rule):
        """
        计算规则评分（分数越低越重要）
        注意：这是确定性的，不包含随机性
        """
        score = 0
        rule_lower = rule.lower()
        
        # 基础评分
        if rule.startswith('||') and rule.endswith('^'):
            score -= 50  # 域名规则优先
        
        # 重要关键词检查（累积加分，不全用break）
        important_hits = 0
        for keyword in IMPORTANT_KEYWORDS:
            if keyword in rule_lower:
                important_hits += 1
        
        if important_hits > 0:
            score -= 30 * min(important_hits, 3)  # 最多减90分
        
        # 通用域名检查
        common_hits = 0
        for domain in COMMON_DOMAINS:
            if domain in rule_lower:
                common_hits += 1
        
        if common_hits > 0:
            score += 20 * min(common_hits, 2)  # 最多加40分
        
        # 规则长度
        rule_len = len(rule)
        if rule_len < 20:
            score -= 10  # 短规则优先
        elif rule_len > 100:
            score += 15  # 过长规则降低优先级
        
        # 规则复杂度
        if '*' in rule:
            score += 5  # 通配符规则降低优先级
        
        if '$' in rule:
            if 'third-party' in rule:
                score -= 5  # 第三方规则优先
            if 'important' in rule:
                score -= 20  # 重要标记规则优先
        
        # 正则表达式规则
        if rule.startswith('/') and rule.endswith('/'):
            score += 10  # 正则规则降低优先级
        
        return score
    
    def is_rule_effective(self, rule):
        """检查规则是否有效（不过于宽泛）"""
        # 过滤过于宽泛的规则
        if rule.count('*') > 3:
            return False
        
        # 移除通配符和特殊字符后检查
        clean = rule.replace('*', '').replace('.', '').replace('^', '').replace('/', '').strip()
        if len(clean) < 3:
            return False
        
        # 过滤特定无效模式
        invalid_patterns = ['*.*', '*', '.*', '/*/']
        for pattern in invalid_patterns:
            if pattern == rule:
                return False
        
        return True
    
    def select_top_rules(self, rules, target_count):
        """选择最优规则（确定性算法）"""
        if len(rules) <= target_count:
            return sorted(rules)  # 保持确定性排序
        
        # 评分并排序
        scored = []
        for rule in rules:
            if not self.is_rule_effective(rule):
                continue
            
            score = self.calculate_rule_score(rule)
            # 使用 (score, rule) 元组，确保相同分数时按字母序排序
            scored.append((score, rule))
        
        # 按分数升序（分数越低越重要），然后按字母序
        scored.sort(key=lambda x: (x[0], x[1]))
        
        # 选择前 target_count 个
        selected = [rule for _, rule in scored[:target_count]]
        
        # 按字母序排序，确保 Git Diff 最小化
        selected.sort()
        return selected
    
    def optimize(self):
        """执行优化"""
        print("\n开始优化规则...")
        
        # 1. 保留所有允许规则
        selected_allow = sorted(self.allow_rules)  # 确定性排序
        
        # 2. 计算需要选择的阻止规则数量
        max_block_rules = MAX_RULES - len(selected_allow)
        target_block_rules = min(
            max(TARGET_RULES - len(selected_allow), MIN_RULES - len(selected_allow)),
            max_block_rules,
            len(self.block_rules)  # 不能超过实际数量
        )
        
        print(f"目标规则数: {TARGET_RULES:,}")
        print(f"需要选择的阻止规则: {target_block_rules:,}")
        
        # 3. 选择最优的阻止规则
        selected_block = self.select_top_rules(self.block_rules, target_block_rules)
        
        # 4. 合并规则
        final_rules = selected_allow + selected_block
        self.stats['selected'] = len(final_rules)
        
        return final_rules, len(selected_block)
    
    def save_rules(self, rules, output_file):
        """保存优化后的规则"""
        print(f"\n保存优化规则到: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8', newline='\n') as f:
            # 文件头
            f.write("! 优化规则文件\n")
            f.write(f"! 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"! 原始规则: {self.stats['total']:,}\n")
            f.write(f"! 优化后规则: {self.stats['selected']:,}\n")
            f.write(f"! 精简比例: {1 - self.stats['selected']/self.stats['total']:.1%}\n")
            f.write("!\n\n")
            
            # 允许规则
            if self.stats['allow'] > 0:
                f.write("! === 允许规则 ===\n")
                for rule in rules:
                    if rule.startswith('@@'):
                        f.write(f"{rule}\n")
                f.write("\n")
            
            # 阻止规则
            f.write("! === 阻止规则 ===\n")
            for rule in rules:
                if not rule.startswith('@@'):
                    f.write(f"{rule}\n")
        
        print(f"保存完成: {len(rules):,} 条规则")
    
    def print_stats(self, selected_block_count):
        """打印统计信息"""
        print("\n" + "="*60)
        print("优化统计:")
        print("-"*60)
        print(f"原始总规则: {self.stats['total']:,}")
        print(f"  允许规则: {self.stats['allow']:,} (保留全部)")
        print(f"  阻止规则: {self.stats['block']:,}")
        print(f"  选择的阻止规则: {selected_block_count:,}")
        print(f"最终规则数: {self.stats['selected']:,}")
        
        if self.stats['total'] > 0:
            ratio = 1 - self.stats['selected'] / self.stats['total']
            print(f"精简比例: {ratio:.1%}")
        print("="*60)

def main():
    """主函数"""
    start_time = time.time()
    
    # 文件路径
    input_file = Path("rules/merged_all.txt")
    output_file = Path("rules/merged_lite.txt")
    
    if not input_file.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        return
    
    # 优化规则
    optimizer = RuleOptimizer()
    optimizer.load_rules(input_file)
    
    final_rules, selected_block_count = optimizer.optimize()
    optimizer.save_rules(final_rules, output_file)
    optimizer.print_stats(selected_block_count)
    
    # 保存详细统计
    stats_file = Path("rules/optimization_stats.txt")
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write(f"优化时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"目标规则数: {TARGET_RULES}\n")
        f.write(f"原始规则数: {optimizer.stats['total']}\n")
        f.write(f"最终规则数: {optimizer.stats['selected']}\n")
        f.write(f"精简比例: {1 - optimizer.stats['selected']/optimizer.stats['total']:.1%}\n")
    
    elapsed = time.time() - start_time
    print(f"\n总耗时: {elapsed:.1f}秒")

if __name__ == "__main__":
    main()