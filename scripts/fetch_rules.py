#!/usr/bin/env python3
"""
抓取规则文件的脚本
"""

import requests
import os
from datetime import datetime

# 设置请求头，模拟浏览器
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def read_sources():
    """读取规则源列表"""
    sources = []
    try:
        with open('sources/sources.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    sources.append(line)
        print(f"读取到 {len(sources)} 个规则源")
        return sources
    except Exception as e:
        print(f"读取规则源失败: {e}")
        return []

def download_rule(url):
    """下载单个规则文件"""
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 检查请求是否成功
        return response.text
    except Exception as e:
        print(f"下载失败 {url}: {e}")
        return ""

def main():
    """主函数"""
    print("=== 开始抓取规则 ===")
    
    # 创建临时文件夹
    if not os.path.exists('temp'):
        os.makedirs('temp')
    
    # 读取规则源
    sources = read_sources()
    
    # 下载每个规则
    all_rules = []
    for i, url in enumerate(sources):
        content = download_rule(url)
        if content:
            # 保存到临时文件
            filename = f"temp/rule_{i+1}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 统计规则数量
            rule_count = len([line for line in content.split('\n') 
                            if line.strip() and not line.startswith('!')])
            all_rules.append((url, rule_count))
            print(f"  规则数量: {rule_count}")
    
    # 显示统计信息
    print("\n=== 抓取完成 ===")
    total_rules = sum(count for _, count in all_rules)
    print(f"总计抓取 {len(all_rules)} 个规则文件")
    print(f"总规则数: {total_rules}")
    
    # 保存统计信息
    with open('temp/stats.txt', 'w', encoding='utf-8') as f:
        f.write(f"规则抓取统计 - {datetime.now()}\n")
        f.write("=" * 50 + "\n")
        for url, count in all_rules:
            f.write(f"{url}: {count} 条规则\n")
        f.write(f"\n总计: {total_rules} 条规则\n")

if __name__ == "__main__":
    main()