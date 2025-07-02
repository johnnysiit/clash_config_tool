# Clash Config Tool

一个用于自动生成 Clash 配置文件的高级工具，支持主用节点、备用节点的分组管理和智能规则生成，适合大规模节点整理与策略配置。

---

## ✅ 功能简介

- 自动读取 `main_servers/` 和 `fallback_servers/` 目录下的节点配置；
- 智能过滤无效节点（自动排除账户信息、官网链接等）；
- 自动生成规则分组（`proxy-groups`）和规则（`rules`）；
- 支持 `select`、`url-test`、`fallback`、`load-balance` 多种策略；
- 支持负载均衡策略配置（`sticky-sessions`、`consistent-hashing`）；
- 内置 DNS 配置，支持 DoH 和 fake-ip 模式；
- 输出统一格式的 Clash YAML 配置文件（带时间戳）；
- 支持 flow-style YAML 输出，完全兼容 Clash Meta / Mihomo；
- 自动生成多个配置文件（不同测速间隔和负载均衡策略）。

---

## 🛠 安装依赖

```bash
pip install pyyaml
```

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

# 📥 使用说明

## 1. 准备节点文件
将你的节点 YAML 文件分别放入以下两个目录：
- main_servers/: 主用节点列表
- fallback_servers/: 备用节点列表（将自动组成 fallback 策略组）

### ⚠️ 注意事项
- 请将文件命名为可读性强的名称（如 HK.yaml, JP高速.yaml）；
- 如希望控制节点排序，建议使用数字顺序作为前缀，例如：
    - 1_hk.yaml（优先）
    - 2_us.yaml
    - 3_bak.yaml（最低）

系统将自动读取所有 YAML 文件并合并节点。

## 2. 规则与分组说明 (默认不需要做任何操作)
 - 所有规则组文件位于 rules/，可根据实际需求自定义修改；
 - 每个规则文件包含以下字段：
    - `group_name`: 生成的策略组名称
    - `key_word`: 关键词匹配（节点名中包含任一关键词即被加入该组）
    - `rules`: Clash 路由规则列表
    - `type`: 策略组类型（支持 `select`, `url-test`, `load-balance`）
    - `fallback_enabled`: 是否启用备用节点组（可选）
    - `fallback_group`: 指定备用策略组（可选）

### 🔧 策略组类型说明
- `select`: 手动选择节点
- `url-test`: 自动选择延迟最低的节点
- `load-balance`: 负载均衡（支持 `sticky-sessions` 和 `consistent-hashing` 策略）
- `fallback`: 自动故障转移（当主节点不可用时切换到备用节点）

## 3. 🚀 运行Python
```bash
python main.py
```

### 🔄 自动生成配置
程序将自动生成两个配置文件：
- `output_Int300_sticky-sessions_YYYYMMDD_HHMMSS.yaml` - 5分钟测速间隔，粘性会话负载均衡
- `output_Int2000_consistent-hashing_YYYYMMDD_HHMMSS.yaml` - 33分钟测速间隔，一致性哈希负载均衡

## 4. 输出结果
运行后，程序将自动生成配置文件到 output/ 目录，文件名格式为：
```
output_Int{间隔}_{负载均衡策略}_YYYYMMDD_HHMMSS.yaml
```

### 📌 示例输出结构

生成的配置文件包含以下字段：
 - `proxies`: 所有加载的节点（主 + 备），自动过滤无效节点
 - `proxy-groups`: 规则分组，含主策略组、备用组、规则定义组等
 - `rules`: Clash 路由规则（支持 `DOMAIN-SUFFIX`, `GEOIP`, `MATCH` 等）
 - `dns`: DNS 配置（支持 DoH、fake-ip 等）

### 🎯 智能节点过滤
程序会自动过滤以下类型的无效节点：
- 包含"帐户"、"账户"、"余"、"官网"、"域名"、"下次"等关键词的节点

---

## 📋 配置文件说明

### DNS 配置
- 启用 fake-ip 模式，提高解析速度
- 默认 DNS: 223.5.5.5, 119.29.29.29
- DoH 服务器: doh.pub, dns.alidns.com
- 备用 DNS: Cloudflare, DNS.SB 等国外服务器

### 负载均衡策略
- `sticky-sessions`: 粘性会话，同一来源IP会使用相同节点
- `consistent-hashing`: 一致性哈希，基于请求URL分配节点

---

## ✅ 使用建议

### 🎯 策略组配置
 - 主策略组自动命名为 🚀 节点选择
 - 备用节点策略组命名为 🛟备用节点
 - 支持负载均衡组（LB 后缀）和备用组（fallback）的组合使用

### ⚡ 性能优化
 - 默认测速 URL: http://www.qq.com（国内访问速度快）
 - 测速超时: 1000ms
 - 两种测速间隔配置：
   - 300秒（5分钟）：适合网络环境较差时
   - 2000秒（33分钟）：适合稳定网络环境

### 🔧 自定义配置
 - 可修改 `main.py` 中的 `DNS` 配置
 - 可调整 `health_check` 参数（URL、间隔、超时）
 - 可修改负载均衡策略和测速间隔

### 📁 目录管理
 - `main_servers/`: 主要节点，用于日常使用
 - `fallback_servers/`: 备用节点，用于故障转移
 - `rules/`: 规则配置，支持地区分流和应用分流
 - `output/`: 自动生成的配置文件，按时间戳命名

---

## 🔬 高级用法

### 规则文件示例

#### 地区分流规则 (rules/2_hk.yaml)
```yaml
group_name: '🇭🇰 香港'
type: 'load-balance'
fallback_enabled: true
key_word:
  - HK
  - 香港
rules:
  - GEOIP,HK
```

#### AI服务分流规则 (rules/3_ai.yaml)
```yaml
group_name: '🇸🇬 东亚'
type: 'load-balance'
fallback_enabled: true
key_word:
  - SG
  - JP
  - KR
  - TW
rules:
  - DOMAIN-SUFFIX,claude.ai
  - DOMAIN-SUFFIX,chatgpt.com
  - DOMAIN,gemini.google.com
```

### 自定义配置参数

如需修改默认配置，可编辑 `main.py` 文件：

```python
# 修改测速间隔和负载均衡策略
processor = ConfigProcessor(interval=600, lb_strategy='round-robin')

# 修改DNS配置
DNS = {
    'enable': True,
    'enhanced-mode': 'fake-ip',
    'nameserver': ['your-dns-server'],
    # ... 其他配置
}
```

---

## 🚨 故障排除

### 常见问题

1. **节点文件格式错误**
   - 确保YAML文件包含 `proxies` 字段
   - 检查YAML语法是否正确

2. **生成的配置无节点**
   - 检查 `main_servers/` 和 `fallback_servers/` 目录是否包含有效文件
   - 确认节点名称不包含过滤关键词

3. **规则不生效**
   - 检查 `rules/` 目录下的YAML文件格式
   - 确认 `group_name` 和 `key_word` 配置正确

### 日志输出
程序运行时会显示：
- 加载的节点数量
- 生成的策略组信息
- 输出文件路径

---

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

---

*最后更新: 2025年7月2日*
