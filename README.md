# 🚀 AdGuard 规则自动生成仓库

这是一个用于 **自动生成 AdGuard 规则** 的仓库。
通过 GitHub Actions 定时运行脚本，自动抓取、合并并优化规则，
并提供 **固定订阅地址**，可直接用于 AdGuard Home / AdGuard 客户端。

---

## 📌 推荐订阅地址（固定不变）

**精简版（Lite，推荐）**  
适合路由器或低性能设备，规则更精简  
https://github.com/KECIHH/adguard-rules-merger/blob/rules/latest/lite/merged_lite.txt

**完整版（Full）**  
规则更全面，拦截更彻底  
https://github.com/KECIHH/adguard-rules-merger/blob/rules/latest/full/merged_all.txt

---

## ✨ 本仓库做了什么？

- 自动下载多个规则源
- 合并并去重规则
- 生成精简版（Lite）和完整版（Full）
- 每天自动更新规则
- 保留最近 30 天历史版本
- 提供永久不变的订阅链接（latest）

---

## 📁 文件说明

- merged_lite.txt：精简版规则  
- merged_all.txt：完整版规则  
- latest/：固定订阅目录  
- archive/：历史归档（自动保留 30 天）

---

## ⚠️ 使用说明

- 普通用户建议优先使用 Lite 版本
- 如遇误拦截，请自行添加白名单
- 本仓库仅做规则整合，不保证所有网站 100% 可访问

---

## 📜 说明

规则版权归原作者所有，本仓库仅用于学习和个人使用。
