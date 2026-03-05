# Contributing to Consilium

首先，感谢您抽出时间来贡献！❤️

First off, thank you for considering contributing to Consilium! ❤️

## 如何贡献 / How to Contribute

### 报告问题 / Reporting Issues

如果您发现了 bug 或有功能建议：

If you find a bug or have a feature suggestion:

1. 检查是否已有相关 Issue
   Check if there's already an existing issue
2. 如果没有，创建新 Issue 并包含：
   If not, create a new issue with:
   - 问题描述 / Description of the issue
   - 复现步骤 / Steps to reproduce
   - 期望行为 / Expected behavior
   - 截图或代码示例 / Screenshots or code examples

### 提交代码 / Submitting Code

1. **Fork 仓库** / Fork the repository
2. **创建分支** / Create a branch
   ```bash
   git checkout -b feature/your-feature-name
   # 或 / or
   git checkout -b fix/issue-description
   ```
3. **提交更改** / Make your changes
4. **确保代码质量** / Ensure code quality
   - 代码符合项目风格 / Code follows project style
   - 添加必要的注释 / Add necessary comments
   - 更新相关文档 / Update relevant documentation
5. **提交 Commit** / Commit your changes
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```
   Commit 消息格式：
   - `feat:` 新功能 / New feature
   - `fix:` 修复 / Bug fix
   - `docs:` 文档 / Documentation
   - `refactor:` 重构 / Code refactoring
   - `test:` 测试 / Tests
   - `chore:` 其他 / Other changes
6. **推送到 Fork** / Push to your fork
   ```bash
   git push origin feature/your-feature-name
   ```
7. **创建 Pull Request** / Create a Pull Request

### 代码风格 / Code Style

#### Python
- 遵循 PEP 8
- 使用 4 空格缩进
- 函数和变量使用 snake_case

#### TypeScript
- 使用 2 空格缩进
- 类型定义优先
- 使用单引号

#### Go
- 使用 gofmt 格式化
- 遵循 Effective Go

#### Rust
- 使用 rustfmt 格式化
- 遵循 Rust API Guidelines

## 开发环境设置 / Development Setup

### Python
```bash
cd src/python
pip install -r requirements.txt
python consilium_v7_6.py
```

### TypeScript
```bash
cd src/typescript
npm install
npm run build
npm start
```

### Go
```bash
cd src/go
go run consilium_v7_6.go
```

### Rust
```bash
cd src/rust
cargo run
```

## 测试 / Testing

- 添加新功能时，请同时添加测试
- 确保所有测试通过
- 测试覆盖率尽可能高

When adding new features, please also add tests:
- Ensure all tests pass
- Aim for high test coverage

## 文档 / Documentation

- 更新 README 如果需要
- 添加代码注释
- 更新 API 文档

Update documentation when necessary:
- Update README if needed
- Add code comments
- Update API documentation

## 行为准则 / Code of Conduct

### 我们的承诺 / Our Pledge

我们致力于为所有人提供一个友好、安全和受欢迎的环境。

We are committed to providing a friendly, safe, and welcoming environment for all.

### 我们的标准 / Our Standards

积极行为包括：
- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情

Positive behaviors include:
- Using friendly and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

不可接受的行为包括：
- 使用性化语言或图像
- 挑衅、侮辱或贬低性评论
- 公开或私下的骚扰
- 未经明确许可发布他人私人信息

Unacceptable behaviors include:
- Trolling, insulting/derogatory comments
- Public or private harassment
- Publishing others' private information without permission

## 提问 / Questions?

如有问题，欢迎：
- 在 GitHub Discussions 提问
- 发送邮件至项目维护者

Feel free to:
- Ask in GitHub Discussions
- Email project maintainers

## 致谢 / Acknowledgments

感谢所有贡献者！您的帮助让这个项目变得更好。

Thank you to all contributors! Your help makes this project better.

---

**再次感谢您的贡献！**

**Thank you again for your contribution!**
