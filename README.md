# Clash Config Tool

一个用于自动生成 Clash 配置文件的小工具，支持主用节点、备用节点的分组管理和规则生成，适合大规模节点整理与策略配置。

---

## ✅ 功能简介

- 自动读取 `main_servers/` 和 `fallback_servers/` 目录下的节点配置；
- 自动生成规则分组（`proxy-groups`）和规则（`rules`）；
- 支持 `select`、`url-test`、`fallback` 多种策略；
- 输出统一格式的 Clash YAML 配置文件（带时间戳）；
- 支持 flow-style YAML 输出，兼容 Clash Meta / Mihomo。

---

## 🛠 安装依赖

```bash
pip install pyyaml
···

## 📂 目录结构说明
```
clash_config_tools/
│
├── main_servers/         # 主用节点 YAML 文件（必须包含 proxies 字段）
├── fallback_servers/     # 备用节点 YAML 文件
├── rules/                # 自定义规则组（可选修改）
├── output/               # 自动生成的配置输出（自动创建）
└── main.py               # 主程序入口
```

---

## 📥 节点文件使用说明

将你的节点 YAML 文件分别放入以下两个目录：
	•	main_servers/: 主用节点列表
	•	fallback_servers/: 备用节点列表（将自动组成 fallback 策略组）

## ⚠️ 注意事项
	•	请将文件命名为可读性强的名称（如 HK.yaml, JP高速.yaml）；
	•	如希望控制节点排序，建议使用数字倒序作为前缀，例如：
	•	9_hk.yaml（优先）
	•	8_us.yaml
	•	1_bak.yaml（最低）

系统将自动读取所有 YAML 文件并合并节点。

## 🧠 规则与分组说明
	•	所有规则组文件位于 rules/，可根据实际需求自定义修改；
	•	每个规则文件包含以下字段：
	•	group_name: 生成的策略组名称
	•	key_word: 关键词匹配（节点名中包含任一关键词即被加入该组）
	•	rules: Clash 路由规则列表
	•	type: 策略组类型（支持 select, url-test）

## 🚀 运行方法
```python main.py```

程序执行后将生成配置文件至 output/ 目录，文件名格式为：
```output_YYYYMMDD_HHMMSS.yaml```

⸻

📌 示例输出结构

生成的配置文件包含以下字段：
	•	proxies: 所有加载的节点（主 + 备）
	•	proxy-groups: 规则分组，含主策略组、备用组、规则定义组等
	•	rules: Clash 路由规则（支持 DOMAIN-SUFFIX, GEOIP, MATCH 等）

⸻

✅ 使用建议
	•	主策略组自动命名为 🚀 节点选择；
	•	备用节点策略组命名为 🛟备用节点；
	•	默认测速 URL 为 http://www.qq.com/，测速间隔为 2 小时；
	•	可根据需求调整 URL_TEST_CONFIG。
