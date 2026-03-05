# Consilium | 智议决策引擎

<p align="center">
  <img src="docs/assets/consilium-logo.png" alt="Consilium Logo" width="200">
</p>

<p align="center">
  <strong>给 AI Agent 加上"深思熟虑"的能力</strong><br>
  <em>Multi-Agent Collaborative Decision Engine for Safe AI Operations</em>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/deloog/consilium/stargazers"><img src="https://img.shields.io/github/stars/deloog/consilium" alt="GitHub stars"></a>
  <a href="https://github.com/deloog/consilium/issues"><img src="https://img.shields.io/github/issues/deloog/consilium" alt="GitHub issues"></a>
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/TypeScript-5.0+-blue.svg" alt="TypeScript">
  <img src="https://img.shields.io/badge/Go-1.21+-00ADD8.svg" alt="Go">
  <img src="https://img.shields.io/badge/Rust-1.70+-orange.svg" alt="Rust">
</p>

---

## 🎯 为什么需要 Consilium？

> **"AI Agent 失控，向用户发送了 500 条垃圾消息"** —— 这不是科幻，这是真实发生的安全事故。

当前的 AI Agent（如 OpenClaw、AutoGPT）虽然强大，但存在致命缺陷：

| 问题 | 后果 |
|------|------|
| ⚠️ **决策过于激进** | 误删重要文件、发送不当消息 |
| ⚠️ **缺乏深思熟虑** | 未经充分分析就执行复杂任务 |
| ⚠️ **安全审查缺失** | 敏感操作无预警，造成不可逆损失 |
| ⚠️ **需求理解偏差** | 生成的代码/技能不符合用户真实意图 |

**Consilium 就是为解决这些问题而生。**

---

## ✨ 核心特性

### 🔒 六重流程控制
防止 AI 决策过度保守或激进，确保每一个决策都经过充分论证。

### 👥 多方审议机制
模拟真实团队协作：
- **产品经理 (PM)** — 确保需求准确理解
- **技术负责人** — 评估方案可行性
- **成本专家** — 分析资源消耗
- **用户代表** — 从终端用户视角审视

### 🛡️ 价值守护者审查
安全审查层，防止危险操作：
- 是否会泄露隐私数据？
- 是否会执行不可逆操作？
- 用户是否真正理解操作后果？

### 🌍 多语言支持
- Python、TypeScript、Go、Rust 四种实现
- 统一的设计理念，各语言原生体验

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/deloog/consilium.git
cd consilium
```

### 2. 配置 API 密钥

```bash
# 推荐使用 DeepSeek（性价比高）
export DEEPSEEK_API_KEY="your-api-key"

# 或使用 OpenAI
export OPENAI_API_KEY="your-api-key"
```

### 3. 运行示例

**Python 版本：**
```bash
python src/python/consilium_v7_6.py
```

**TypeScript 版本：**
```bash
cd src/typescript
npm install
npm run build
npm start
```

**Go 版本：**
```bash
cd src/go
go run consilium_v7_6.go
```

**Rust 版本：**
```bash
cd src/rust
cargo run
```

---

## 💡 应用场景

### 1. OpenClaw AI Agent 安全增强 ⭐⭐⭐⭐⭐

**痛点**：OpenClaw 作为自主 AI Agent，缺乏深思熟虑机制，容易失控。

**解决方案**：将 Consilium 作为决策中间件：

```javascript
// OpenClaw 集成 Consilium 示例
const { ConsiliumEngine } = require('consilium');

// 在处理敏感任务前，先经过 Consilium 审议
const decision = await ConsiliumEngine.run({
  requirement: "自动回复所有邮件",
  context: { userPreferences, safetyLevel: "high" }
});

// 根据审议结果执行（可能修改了用户原始需求）
executeSafely(decision.approvedActions);
```

**效果**：从"直接执行"变成"先审议后执行"，避免 AI 失控。

### 2. 技能自动生成质量控制 ⭐⭐⭐⭐⭐

当用户要求 AI 生成新技能（如"自动整理照片"）：

| 传统方式 | 使用 Consilium |
|---------|---------------|
| AI 直接生成代码 | 多方讨论功能范围 |
| 需求理解可能偏差 | PM 角色确保需求准确 |
| 技术方案可能不可行 | 技术负责人评估可行性 |
| 安全风险未审查 | 价值守护者检查安全性 |

### 3. 企业级决策审查 ⭐⭐⭐⭐

- **敏感操作审批**：删除数据、发送邮件、访问隐私信息
- **复杂任务协调**：多部门协作需求的决策分析
- **合规性检查**：确保决策符合企业安全规范

---

## 📊 架构图

```
┌─────────────┐
│   用户需求   │
└──────┬──────┘
       ▼
┌─────────────────────────┐
│    Consilium 决策引擎    │
│  ┌───────────────────┐  │
│  │ 阶段0: 多方审议   │  │ ← PM/技术/成本/用户讨论
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ 阶段1-5: 详细分析 │  │ ← PRD/技术方案/成本分析
│  └───────────────────┘  │
│  ┌───────────────────┐  │
│  │ 价值守护者检查    │  │ ← 安全检查
│  └───────────────────┘  │
└──────────┬──────────────┘
           ▼
    ┌──────────────┐
    │  决策清单输出 │ ← 明确可执行、需确认、需砍掉的功能
    └──────┬───────┘
           ▼
    ┌──────────────┐
    │  AI Agent    │ ← 安全执行
    │  (OpenClaw)  │
    └──────────────┘
```

---

## 🛠️ 项目结构

```
consilium/
├── src/
│   ├── python/           # Python 实现 (推荐初学者)
│   │   └── consilium_v7_6.py
│   ├── typescript/       # TypeScript 实现 (推荐 OpenClaw 集成)
│   │   ├── consilium_v7_6.ts
│   │   └── package.json
│   ├── go/              # Go 实现 (推荐高性能场景)
│   │   └── consilium_v7_6.go
│   └── rust/            # Rust 实现 (推荐系统级应用)
│       └── consilium_v7_6.rs
├── docs/
│   ├── Consilium_v7.6_OpenClaw_Analysis.md  # OpenClaw 集成分析
│   └── API.md                                # API 文档
├── examples/            # 使用示例
│   ├── openclaw-integration/   # OpenClaw 集成示例
│   └── safety-check/           # 安全检查示例
└── tests/               # 测试用例
```

---

## 🔧 环境变量

| 变量 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 是* | - |
| `OPENAI_API_KEY` | OpenAI API 密钥 | 是* | - |
| `DEEPSEEK_BASE_URL` | API 基础地址 | 否 | https://api.deepseek.com |
| `DEEPSEEK_MODEL` | 模型名称 | 否 | deepseek-chat |
| `CONSILIUM_REQUIREMENT` | 默认需求描述 | 否 | - |

*至少提供一个 API Key

---

## 🌟 效果对比

### 场景：用户说"帮我自动回复所有邮件"

**❌ 传统 AI Agent：**
```
AI: "好的，我会回复所有邮件"
结果：
- 回复了垃圾邮件
- 误回复了老板的严肃邮件
- 泄露了隐私信息
```

**✅ 使用 Consilium 的 AI Agent：**
```
【多方审议】
PM: "用户核心需求是减少邮件处理时间"
技术: "可以按规则过滤：仅回复订阅邮件"
成本: "API 调用成本：每天约 50 次"
用户代表: "我担心误回复重要邮件"

【价值守护者检查】
⚠️ 高风险：自动回复可能泄露信息
⚠️ 建议：重要邮件需人工确认

【最终决策】
✅ 自动回复仅限：订阅类邮件
✅ VIP 发件人的邮件永不自动处理
✅ 每日生成操作摘要供用户审查
```

---

## 📖 文档

- [OpenClaw 集成分析](docs/Consilium_v7.6_OpenClaw_Analysis.md) - 详细的技术价值分析
- [API 文档](docs/API.md) - 完整接口说明
- [贡献指南](CONTRIBUTING.md) - 如何参与项目

---

## 🤝 与 OpenClaw 集成

Consilium 可作为 OpenClaw 的安全中间件使用：

```bash
# 安装 Consilium 插件
npm install consilium-openclaw-plugin

# 在 OpenClaw 配置中启用
# ~/.openclaw/config.json
{
  "plugins": {
    "consilium": {
      "enabled": true,
      "safetyLevel": "high"
    }
  }
}
```

详细集成指南：[OpenClaw Integration Guide](docs/openclaw-integration.md)

---

## 🗺️ 路线图

- [x] v7.6 核心功能
- [x] 多语言实现 (Python/TypeScript/Go/Rust)
- [x] OpenClaw 集成分析
- [ ] OpenClaw 官方插件 (进行中)
- [ ] Web UI 可视化界面
- [ ] 企业版 (审计日志、多用户、权限管理)
- [ ] VS Code 插件

---

## 💼 商业合作

Consilium 采用 MIT 开源协议，同时提供企业版支持：

| 功能 | 开源版 | 企业版 |
|------|--------|--------|
| 核心决策引擎 | ✅ | ✅ |
| 多语言支持 | ✅ | ✅ |
| 基础安全审查 | ✅ | ✅ |
| 审计日志 | ❌ | ✅ |
| 多用户/权限管理 | ❌ | ✅ |
| 私有化部署支持 | ❌ | ✅ |
| SLA 技术支持 | ❌ | ✅ |

**联系**：如有商业合作意向，请通过 GitHub Issues 联系我们。

---

## 🤝 贡献

欢迎贡献代码、提交 Issue、改进文档！

```bash
# 1. Fork 仓库
# 2. 创建分支
git checkout -b feature/your-feature

# 3. 提交更改
git commit -m "Add some feature"

# 4. 推送分支
git push origin feature/your-feature

# 5. 创建 Pull Request
```

---

## 📄 许可证

[MIT License](LICENSE) © 2024 Consilium Contributors

---

## 🙏 致谢

感谢所有为 Consilium 贡献代码、提出建议的社区成员！

特别感谢：
- [DeepSeek](https://deepseek.com/) 提供高性能 LLM API
- [OpenClaw](https://openclaw.ai/) 社区的支持与反馈

---

<p align="center">
  <strong>让 AI 决策更安全、更可靠</strong><br>
  <a href="https://github.com/deloog/consilium">⭐ Star 支持我们</a>
</p>
