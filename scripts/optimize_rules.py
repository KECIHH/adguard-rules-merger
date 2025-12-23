#!/usr/bin/env python3
"""
优化规则脚本：从合并后的完整规则中，生成一个精简版本。
"""

import os
import random
from datetime import datetime

def read_rules(filepath):
    """读取规则文件，返回规则列表和文件头"""
    rules = []
    header_lines = []
    in_header = True
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                
                # 捕获文件头（注释和空行）
                if in_header and (line.startswith('!') or line == ''):
                    header_lines.append(line)
                else:
                    in_header = False
                    # 只保留非空、非注释的有效规则
                    if line and not line.startswith('!'):
                        rules.append(line)
        
        print(f"从 {filepath} 读取了 {len(rules)} 条有效规则")
        return header_lines, rules
    except Exception as e:
        print(f"读取规则文件失败: {e}")
        return [], []

def optimize_by_specificity(rules, target_count):
    """
    优化策略1：按规则特异性排序（通常更短、更具体的规则更有效）
    返回最前面的 target_count 条规则。
    """
    # 按规则长度排序，优先保留更短（通常更具体）的规则
    sorted_rules = sorted(rules, key=lambda x: len(x))
    return sorted_rules[:target_count]

def optimize_random_sample(rules, target_count):
    """
    优化策略2：随机抽样，可以保证规则类型的多样性。
    """
    if target_count >= len(rules):
        return rules
    return random.sample(rules, target_count)

def optimize_by_source_priority(rules, target_count):
    """
    优化策略3：混合策略（示例）
    1. 先保留所有来自特定高优先级格式的规则（例如 ||domain.com^）
    2. 如果数量不够，再补充其他规则
    """
    priority_rules = []
    other_rules = []
    
    for rule in rules:
        # 示例：将经典的域名拦截规则视为高优先级
        if rule.startswith('||') and rule.endswith('^'):
            priority_rules.append(rule)
        else:
            other_rules.append(rule)
    
    print(f"  高优先级规则（||...^）: {len(priority_rules)} 条")
    print(f"  其他规则: {len(other_rules)} 条")
    
    # 优先保留高优先级规则
    if len(priority_rules) >= target_count:
        return priority_rules[:target_count]
    else:
        # 高优先级的不够，用其他的补足
        result = priority_rules
        remain = target_count - len(priority_rules)
        result.extend(other_rules[:remain])
        return result

def save_rules(header_lines, rules, filename, description):
    """保存规则到文件"""
    try:
        os.makedirs('rules', exist_ok=True)
        
        with open(f'rules/{filename}', 'w', encoding='utf-8') as f:
            # 更新文件头信息
            for line in header_lines:
                if 'Title:' in line:
                    f.write(f"! Title: {description}\n")
                elif 'Description:' in line:
                    f.write(f"! Description: 精简优化的AdGuard规则（由完整版生成）\n")
                elif 'Rule count:' in line:
                    f.write(f"! Rule count: {len(rules)}\n")
                elif 'Last modified:' in line:
                    f.write(f"! Last modified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                else:
                    f.write(f"{line}\n")
            
            # 写入优化后的规则
            for rule in rules:
                f.write(f"{rule}\n")
        
        print(f"✅ 已保存精简规则到 rules/{filename}")
        print(f"   规则数量: {len(rules)} 条")
        return True
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 开始生成精简规则 ===")
    
    # 配置参数
    input_file = 'rules/merged_all.txt'  # 输入：完整规则
    output_file = 'merged_lite.txt'      # 输出：精简规则文件名
    target_rule_count = 150000           # 目标规则数（约一半）
    
    # 1. 读取完整规则
    print(f"正在读取完整规则文件: {input_file}")
    header, all_rules = read_rules(input_file)
    
    if not all_rules:
        print("错误：没有读取到规则，请确保完整规则文件已生成。")
        return
    
    # 2. 选择优化策略
    print(f"\n完整规则数: {len(all_rules)} 条")
    print(f"目标精简数: {target_rule_count} 条")
    
    print("\n请选择优化策略:")
    print("  1. 按规则特异性排序（保留更短、更具体的规则）")
    print("  2. 随机抽样（保持规则类型多样性）")
    print("  3. 按规则来源/格式优先级（推荐）")
    
    # 这里固定使用策略3，你可以根据注释修改
    choice = 3
    
    if choice == 1:
        print("\n执行策略: 按规则特异性排序")
        optimized_rules = optimize_by_specificity(all_rules, target_rule_count)
    elif choice == 2:
        print("\n执行策略: 随机抽样")
        optimized_rules = optimize_random_sample(all_rules, target_rule_count)
    else:
        print("\n执行策略: 按规则格式优先级")
        optimized_rules = optimize_by_source_priority(all_rules, target_rule_count)
    
    # 3. 保存精简规则
    print(f"\n正在保存精简规则...")
    save_rules(header, optimized_rules, output_file, "AdGuard规则精简版")
    
    # 4. （可选）也可以专门为DNS生成一个更精简的版本
    # 例如：只保留 `||domain.com^` 格式的规则
    dns_rules = [rule for rule in optimized_rules if rule.startswith('||') and rule.endswith('^')]
    dns_output_file = 'merged_dns_lite.txt'
    if dns_rules:
        print(f"\n生成纯DNS精简版（{len(dns_rules)} 条）...")
        # 稍微修改文件头描述
        dns_header = [line.replace('精简优化的AdGuard规则', 'DNS过滤规则精简版') for line in header]
        save_rules(dns_header, dns_rules, dns_output_file, "DNS规则精简版")
    
    print("\n=== 精简规则生成完成 ===")

if __name__ == "__main__":
    main()