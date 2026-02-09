# Consilium（智议决策引擎）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Consilium v7.6 是一个多智能体协作决策引擎，通过多方审议机制确保AI决策的质量和安全性。

## 核心特性

- **六重流程控制**：防止AI决策过度保守或激进
- **多方审议机制**：产品经理、技术负责人、成本专家、用户代表共同参与
- **价值守护者审查**：确保核心功能不被过度简化
- **多语言支持**：Python、TypeScript、Go、Rust 四种实现

## 应用场景

- 企业级AI决策系统
- OpenClaw AI Agent 决策增强
- 复杂需求的多方协调
- 敏感操作的自动化审查

## 快速开始

### Python 版本

```bash
export DEEPSEEK_API_KEY="your-api-key"
python src/python/consilium_v7_6.py
```

### TypeScript 版本

```bash
cd src/typescript
npm install
npm run build
npm start
```

### Go 版本

```bash
cd src/go
go run consilium_v7_6.go
```

### Rust 版本

```bash
cd src/rust
cargo run
```

## 项目结构

```
src/
├── python/           # Python 实现
│   └── consilium_v7_6.py
├── typescript/       # TypeScript 实现
│   ├── consilium_v7_6.ts
│   ├── package.json
│   └── tsconfig.json
├── go/              # Go 实现
│   └── consilium_v7_6.go
└── rust/            # Rust 实现
    ├── consilium_v7_6.rs
    └── Cargo.toml

docs/
├── Consilium_v7.6_OpenClaw_Analysis.md
└── ...              # 其他文档
```

## 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 是 |
| `DEEPSEEK_BASE_URL` | API 地址（可选） | 否 |
| `DEEPSEEK_MODEL` | 模型名称（可选） | 否 |
| `CONSILIUM_REQUIREMENT` | 客户需求（可选） | 否 |

## 协议

MIT License
