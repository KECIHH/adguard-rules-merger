#!/usr/bin/env python3
"""
合并和去重规则的脚本
"""

import os
import re
from datetime import datetime

def load_rules_from_file(filename):
    """从文件加载规则"""
    rules = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('!'):
                    # 简单的清理
                    line = line.split('#')[0].strip()  # 移除行内注释
                    if line:
                        rules.append(line)
        return rules
    except Exception as e:
        print(f"读取文件失败 {filename}: {e}")
        return []

def remove_duplicates(rules):
    """去除重复规则"""
    unique_rules = []
    seen = set()
    
    for rule in rules:
        if rule not in seen:
            seen.add(rule)
            unique_rules.append(rule)
    
    print(f"去重前: {len(rules)} 条规则")
    print(f"去重后: {len(unique_rules)} 条规则")
    print(f"移除重复: {len(rules) - len(unique_rules)} 条")
    
    return unique_rules

def categorize_rules(rules):
    """分类规则"""
    dns_rules = []  # DNS过滤规则
    element_rules = []  # 元素隐藏规则
    other_rules = []  # 其他规则
    
    for rule in rules:
        # DNS过滤规则（常见格式）
        if rule.startswith('||') or rule.endswith('^'):
            dns_rules.append(rule)
        # 元素隐藏规则
        elif '##' in rule or '#@#' in rule:
            element_rules.append(rule)
        # 其他规则
        else:
            other_rules.append(rule)
    
    return dns_rules, element_rules, other_rules

def save_rules(rules, filename, description=""):
    """保存规则到文件"""
    try:
        # 确保目录存在
        os.makedirs('rules', exist_ok=True)
        
        with open(f'rules/{filename}', 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write(f"! Title: {description}\n")
            f.write(f"! Description: 合并去重的AdGuard规则\n")
            f.write(f"! Version: {datetime.now().strftime('%Y%m%d')}\n")
            f.write(f"! Last modified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"! Rule count: {len(rules)}\n")
            f.write(f"! Homepage: https://github.com/KECIHH/adguard-rules-merger\n")
            f.write("!===================================================\n\n")
            
            # 写入规则
            for rule in sorted(rules):
                f.write(f"{rule}\n")
        
        print(f"已保存到 rules/{filename}")
        return True
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 开始合并规则 ===")
    
    # 检查临时文件
    if not os.path.exists('temp'):
        print("错误：请先运行 fetch_rules.py")
        return
    
    # 收集所有规则
    all_rules = []
    temp_files = [f for f in os.listdir('temp') if f.startswith('rule_')]
    
    for filename in temp_files:
        filepath = os.path.join('temp', filename)
        rules = load_rules_from_file(filepath)
        all_rules.extend(rules)
        print(f"从 {filename} 加载了 {len(rules)} 条规则")
    
    if not all_rules:
        print("没有找到任何规则")
        return
    
    # 去重
    print("\n=== 去重处理 ===")
    unique_rules = remove_duplicates(all_rules)
    
    # 分类
    print("\n=== 规则分类 ===")
    dns_rules, element_rules, other_rules = categorize_rules(unique_rules)
    
    print(f"DNS过滤规则: {len(dns_rules)} 条")
    print(f"元素隐藏规则: {len(element_rules)} 条")
    print(f"其他规则: {len(other_rules)} 条")
    
    # 保存合并的规则
    print("\n=== 保存规则 ===")
    if dns_rules:
        save_rules(dns_rules, "merged_dns.txt", "合并的DNS过滤规则")
    
    if element_rules:
        save_rules(element_rules, "merged_element.txt", "合并的元素隐藏规则")
    
    # 保存全部规则
    save_rules(unique_rules, "merged_all.txt", "全部合并规则")
    
    print("\n=== 完成 ===")
    print(f"总共生成 {len(unique_rules)} 条唯一规则")

if __name__ == "__main__":
    main()