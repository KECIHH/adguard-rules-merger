# AdGuard Home 规则合并器

自动合并多个AdGuard Home规则，去除重复规则，并定期更新。

## 功能特点

- ✅ 自动抓取多个规则源
- ✅ 智能去重，移除重复规则
- ✅ 自动分类（DNS规则/元素隐藏规则）
- ✅ 每天自动更新
- ✅ 支持手动触发更新

## 使用方法

### 在AdGuard Home中使用

1. 打开AdGuard Home管理界面
2. 进入"过滤器" -> "DNS封锁列表"
3. 点击"添加阻止列表"
4. 输入以下URL：
https://raw.githubusercontent.com/KECIHH/adguard-rules-merger/main/rules/merged_all.txt
5. 点击"保存"

### 规则分类

- **merged_all.txt** - 所有规则的合并版本
- **merged_dns.txt** - 仅DNS过滤规则
- **merged_dns_lite.txt** - 精简DNS过滤规则
- **mmerged_lite.txt** - 精简过滤规则

## 自定义规则源

编辑 `sources/sources.txt` 文件，每行添加一个规则URL：

```txt
# 基础规则
https://example.com/rule1.txt

# 隐私保护规则
https://example.com/rule2.txt