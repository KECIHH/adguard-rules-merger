#!/usr/bin/env python3
"""
优化规则脚本（智能精简增强版）：为低性能设备生成安全、高效的规则。
改进点：
1. 支持命令行参数，可灵活调整目标规则数等。
2. 增强了文件读取时的错误处理。
用法示例（在GitHub Actions中会自动使用默认参数）：
  python scripts/optimize_rules.py --target 80000
  python scripts/optimize_rules.py --input rules/merged_all.txt --output my_lite.txt --target 150000
"""

import os
import re
import sys
import argparse
from datetime import datetime

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='为低性能设备生成智能精简的AdGuard规则。')
    parser.add_argument('--input', default='rules/merged_all.txt',
                        help='输入的完整规则文件路径 (默认: rules/merged_all.txt)')
    parser.add_argument('--output', default='merged_lite.txt',
                        help='输出的精简规则文件名 (默认: merged_lite.txt)')
    parser.add_argument('--target', type=int, default=150000,
                        help='目标规则数量 (默认: 150000)')
    parser.add_argument('--dns_output', default='merged_dns_lite.txt',
                        help='输出的纯DNS精简版文件名 (默认: merged_dns_lite.txt)')
    return parser.parse_args()

def read_rules(filepath):
    """读取规则文件，返回规则列表和文件头（增强错误处理）"""
    rules = []
    header_lines = []
    in_header = True

    # 检查文件是否存在
    if not os.path.exists(filepath):
        print(f"❌ 错误：输入文件 '{filepath}' 不存在。")
        print("   请确保上游的 merge_rules.py 脚本已成功运行并生成了完整规则文件。")
        sys.exit(1)  # 退出并通知工作流失败

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if in_header and (line.startswith('!') or line == ''):
                    header_lines.append(line)
                else:
                    in_header = False
                    if line and not line.startswith('!'):
                        rules.append(line)
        print(f"✅ 从 {filepath} 读取了 {len(rules)} 条有效规则")
        return header_lines, rules
    except UnicodeDecodeError:
        print(f"❌ 错误：文件 '{filepath}' 编码问题，无法用UTF-8读取。")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 读取文件时发生未知错误: {e}")
        sys.exit(1)

def optimize_smart_lite(rules, target_count):
    """智能精简核心策略（与原脚本逻辑完全一致）"""
    allowlist_rules = []
    hosts_rules = []
    efficient_block_rules = []
    other_rules = []

    print("正在执行智能分类与过滤...")
    for rule in rules:
        if rule.startswith('/') and rule.endswith('/'):
            continue
        if '##' in rule or '#@#' in rule or '#?#' in rule:
            continue
        if rule.startswith('@@'):
            allowlist_rules.append(rule)
            continue
        if rule.startswith('||') and rule.endswith('^'):
            efficient_block_rules.append(rule)
            continue
        parts = rule.split()
        if len(parts) >= 2:
            first_part = parts[0]
            if (re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', first_part) or
                re.match(r'^[0-9a-fA-F:]+$', first_part)):
                hosts_rules.append(rule)
                continue
        other_rules.append(rule)

    print(f"  分类完成:")
    print(f"  ✅ 白名单规则: {len(allowlist_rules)} 条")
    print(f"  ✅ Hosts格式规则: {len(hosts_rules)} 条")
    print(f"  ✅ 高效DNS拦截规则: {len(efficient_block_rules)} 条")
    print(f"  ⚠️  其他规则: {len(other_rules)} 条")

    final_rules = []
    final_rules.extend(allowlist_rules)
    final_rules.extend(hosts_rules)
    essential_count = len(final_rules)
    print(f"\n  已保留 {essential_count} 条核心规则 (白名单+Hosts)。")

    remaining_quota = target_count - essential_count
    if remaining_quota <= 0:
        print(f"  注意：核心规则数({essential_count})已超过目标({target_count})，将只保留核心规则。")
        return final_rules[:target_count]

    if efficient_block_rules:
        take = min(remaining_quota, len(efficient_block_rules))
        final_rules.extend(efficient_block_rules[:take])
        remaining_quota -= take
        print(f"  加入 {take} 条高效DNS拦截规则。")

    if remaining_quota > 0 and other_rules:
        take = min(remaining_quota, len(other_rules))
        final_rules.extend(other_rules[:take])
        print(f"  加入 {take} 条其他规则。")

    print(f"\n  最终精简规则数: {len(final_rules)} 条 (目标: {target_count} 条)")
    return final_rules

def save_rules(header_lines, rules, filename, description):
    """保存规则到文件"""
    try:
        os.makedirs('rules', exist_ok=True)
        with open(f'rules/{filename}', 'w', encoding='utf-8') as f:
            for line in header_lines:
                if 'Title:' in line:
                    f.write(f"! Title: {description}\n")
                elif 'Description:' in line:
                    f.write(f"! Description: 智能精简版 - 专为低性能设备优化，保留白名单，剔除正则/元素隐藏规则\n")
                elif 'Rule count:' in line:
                    f.write(f"! Rule count: {len(rules)}\n")
                elif 'Last modified:' in line:
                    f.write(f"! Last modified: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                else:
                    f.write(f"{line}\n")
            for rule in rules:
                f.write(f"{rule}\n")
        print(f"✅ 已保存精简规则到 rules/{filename} ({len(rules)} 条)")
        return True
    except Exception as e:
        print(f"❌ 保存文件 '{filename}' 失败: {e}")
        return False

def main():
    """主函数"""
    print("=== 开始生成智能精简规则 (为低性能设备优化) ===")

    args = parse_arguments()
    print(f"  输入文件: {args.input}")
    print(f"  输出文件: {args.output}")
    print(f"  目标规则数: {args.target}")

    header, all_rules = read_rules(args.input)
    if not all_rules:
        print("错误：没有读取到任何有效规则。")
        sys.exit(1)

    print(f"\n完整规则数: {len(all_rules)} 条")
    print("执行策略: 智能精简 (保留白名单/去除正则&元素隐藏/优先高效规则)")

    optimized_rules = optimize_smart_lite(all_rules, args.target)

    print(f"\n正在保存通用精简规则...")
    save_rules(header, optimized_rules, args.output, "AdGuard规则智能精简版")

    # 生成纯DNS精简版（可选）
    print(f"\n正在生成‘纯DNS精简版’...")
    pure_dns_rules = []
    for rule in optimized_rules:
        if (rule.startswith('@@') or
            (rule.startswith('||') and rule.endswith('^')) or
            (len(rule.split()) >= 2 and rule.split()[0].count('.') == 3)):
            pure_dns_rules.append(rule)

    if len(pure_dns_rules) < len(optimized_rules) * 0.9:
        print(f"  纯DNS版进一步精简了 {len(optimized_rules) - len(pure_dns_rules)} 条规则。")
        dns_header = [line.replace('智能精简版', '纯DNS智能精简版') if 'Title:' in line else line for line in header]
        save_rules(dns_header, pure_dns_rules, args.dns_output, "AdGuard纯DNS规则精简版")
    else:
        print("  纯DNS版规则数量变化不大，不单独保存。")

    print("\n=== 智能精简规则生成完成 ===")
    print("提示：可在GitHub Actions的`Generate lite rules`步骤中修改`--target`参数调整规模。")

if __name__ == "__main__":
    main()