
AdGuard Home 规则更新工具

自动从多个来源抓取、合并和优化 AdGuard Home 规则，生成精简高效的过滤规则。
使用方法
1. 准备规则源

编辑 sources/sources.txt 文件，每行添加一个规则源 URL：

# 示例规则源
https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt
https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
https://easylist-downloads.adblockplus.org/easylistchina.txt
https://raw.githubusercontent.com/cjx82630/cjxlist/master/cjx-annoyance.txt

2. 安装依赖

pip install requests

3. 运行更新脚本

按顺序执行三个脚本：

# 1. 抓取所有规则
python3 scripts/fetch_rules.py

# 2. 合并并去重
python3 scripts/merge_rules.py

# 3. 优化精简
python3 scripts/optimize_rules.py

4. 获取结果

处理完成后，在 rules/ 目录下会生成：

    merged_lite.txt - 精简版规则（推荐使用）
    merged_all.txt - 完整版规则

文件说明

.
├── sources/sources.txt      # 规则源列表
├── scripts/
│   ├── fetch_rules.py       # 抓取规则
│   ├── merge_rules.py       # 合并去重
│   └── optimize_rules.py    # 优化精简
├── rules/                   # 输出目录
│   ├── merged_all.txt       # 完整规则
│   └── merged_lite.txt      # 精简规则
└── temp/                    # 临时文件（自动生成）

注意事项

    确保网络畅通，能访问规则源
    精简规则约15万条，适合大多数用户
    完整规则可能超过50万条，请根据需要选择
    临时目录会自动清理

许可证

MIT License
