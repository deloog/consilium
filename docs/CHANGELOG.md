# 修复变更日志

## 版本：Fix v1.0 (2026-02-08)

---

## 📝 修改文件清单

### 1. [Pipeline mode.py](Pipeline mode.py) - 流水线模式

#### 改动1：增强 `call_llm()` 函数（第69-95行）

**修改前**：
```python
def call_llm(system_prompt, user_message):
    """调用GLM4.7"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[...],
        temperature=0.7,
        max_tokens=2000,  # ⚠️ 固定2000，不足
    )
    return response.choices[0].message.content  # ⚠️ 无错误处理
```

**修改后**：
```python
def call_llm(system_prompt, user_message, max_tokens=4000):  # ✅ 可配置，默认4000
    """调用GLM4.7，增加错误处理和可配置的token限制"""
    try:  # ✅ 添加异常捕获
        response = client.chat.completions.create(...)
        content = response.choices[0].message.content

        # ✅ 检查空返回
        if not content or content.strip() == "":
            print(f"⚠️ 警告：LLM返回了空内容")
            print(f"  - finish_reason: {response.choices[0].finish_reason}")
            return "[ERROR: LLM返回空内容...]"

        return content
    except Exception as e:  # ✅ 捕获API错误
        print(f"❌ API调用失败: {e}")
        return "[ERROR: API调用失败...]"
```

**改进效果**：
- ✅ Token限制从2000提升到4000（提升100%）
- ✅ 支持动态配置max_tokens
- ✅ 空返回时有明确提示
- ✅ API错误时不会程序崩溃

---

#### 改动2：差异化角色配置（第93-106行）

**修改前**：
```python
output = call_llm(role["system_prompt"], user_msg)
# 所有角色都用相同的2000 tokens
```

**修改后**：
```python
# 为技术负责人提供更多token空间
token_limit = 5000 if role["name"] == "技术负责人" else 4000
output = call_llm(role["system_prompt"], user_msg, max_tokens=token_limit)
```

**改进效果**：
- ✅ 技术负责人获得5000 tokens（提升150%）
- ✅ 其他角色4000 tokens（提升100%）
- ✅ 根据角色职责分配资源

---

### 2. [Social mode.py](Social mode.py) - 社交讨论模式

#### 改动1：增强 `call_llm()` 函数（第102-125行）

**修改前**：
```python
def call_llm(messages, temperature=0.8):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=500,  # ❌ 致命：仅500 tokens
    )
    return response.choices[0].message.content  # ❌ 无错误处理
```

**修改后**：
```python
def call_llm(messages, temperature=0.8, max_tokens=1500):  # ✅ 默认1500
    try:
        response = client.chat.completions.create(...)
        content = response.choices[0].message.content

        # ✅ 详细的诊断信息
        if not content or content.strip() == "":
            print(f"⚠️ 警告：LLM返回空内容")
            print(f"  - finish_reason: {response.choices[0].finish_reason}")
            print(f"  - 输入消息数: {len(messages)}")
            total_input_length = sum(len(str(m.get('content', ''))) for m in messages)
            print(f"  - 输入总长度约: {total_input_length} 字符")
            return "[ERROR: LLM返回空内容...]"

        return content
    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return "[ERROR: API调用失败...]"
```

**改进效果**：
- ✅ Token限制从500提升到1500（提升200%）
- ✅ 更详细的诊断信息（消息数、输入长度）
- ✅ 完整的错误处理

---

#### 改动2：新增历史压缩机制（第128-151行）

**新增函数**：
```python
def compress_history(discussion_history, keep_recent=8):
    """
    压缩讨论历史，保留最近的发言，避免上下文过长

    策略：
    1. 保留第一条需求说明
    2. 保留最近N条发言
    3. 中间部分用摘要替代
    """
    if len(discussion_history) <= keep_recent + 1:
        return discussion_history

    # 保留第一条（需求）+ 最近N条
    compressed = [discussion_history[0]]

    # 中间部分做简单摘要
    middle_messages = discussion_history[1:-keep_recent]
    if middle_messages:
        middle_summary = f"[前期讨论摘要：共{len(middle_messages)}条发言已省略...]"
        compressed.append({"role": "assistant", "content": middle_summary})

    # 添加最近的发言
    compressed.extend(discussion_history[-keep_recent:])

    return compressed
```

**改进效果**：
- ✅ 防止上下文无限增长
- ✅ 保持讨论连贯性（最近12条）
- ✅ 控制输入token在合理范围
- ✅ 第5轮讨论不会因上下文过长而失败

---

#### 改动3：应用历史压缩（第168-184行）

**修改前**：
```python
messages = [
    {"role": "system", "content": agent["system_prompt"]},
    *discussion_history,  # ❌ 传递完整历史，第5轮时超长
    {"role": "user", "content": f"现在轮到你发言..."},
]

response = call_llm(messages)  # ❌ 只有500 tokens输出空间
```

**修改后**：
```python
# 压缩历史，避免上下文过长
compressed_history = compress_history(discussion_history, keep_recent=12)

messages = [
    {"role": "system", "content": agent["system_prompt"]},
    *compressed_history,  # ✅ 使用压缩后的历史
    {"role": "user", "content": f"现在轮到你发言..."},
]

# 为个人发言提供足够的token
response = call_llm(messages, max_tokens=1000)  # ✅ 1000 tokens
```

**改进效果**：
- ✅ 输入上下文可控（不超过需求+12条发言）
- ✅ 输出空间充足（1000 tokens）
- ✅ 每个角色都能完整表达观点

---

#### 改动4：优化总结阶段（第186-198行）

**修改前**：
```python
summary_messages = [
    {"role": "system", "content": SUMMARIZER_PROMPT},
    *discussion_history,
    {"role": "user", "content": "请总结..."},
]

summary = call_llm(summary_messages, temperature=0.3)  # ❌ 只有500 tokens
```

**修改后**：
```python
summary_messages = [
    {"role": "system", "content": SUMMARIZER_PROMPT},
    *discussion_history,  # ✅ 总结时使用完整历史（不压缩）
    {"role": "user", "content": "请总结..."},
]

# 总结需要更多token来完整表达
summary = call_llm(summary_messages, temperature=0.3, max_tokens=3000)  # ✅ 3000 tokens
```

**改进效果**：
- ✅ 总结输出空间从500提升到3000（提升500%）
- ✅ 能生成完整的会议纪要
- ✅ 包含共识、分歧、新想法、建议方案等完整内容

---

## 📊 改进数据对比

### Token配置对比

| 场景 | 修复前 | 修复后 | 提升幅度 |
|------|--------|--------|----------|
| **流水线 - 默认** | 2000 | 4000 | +100% |
| **流水线 - 技术负责人** | 2000 | 5000 | +150% |
| **社交 - 个人发言** | 500 | 1000 | +100% |
| **社交 - 最终总结** | 500 | 3000 | +500% |

### 上下文管理对比

| 模式 | 修复前 | 修复后 |
|------|--------|--------|
| **流水线** | 无限制传递 | 无限制传递（但token充足） |
| **社交 - 第1轮** | 需求 + 4条发言 | 需求 + 4条发言 |
| **社交 - 第5轮** | 需求 + 20条发言（~3000+ tokens输入） | 需求 + 摘要 + 最近12条（~2000 tokens输入） |

---

## 🎯 关键技术决策

### 决策1：为什么不统一使用最大token？
**考虑**：
- API调用成本与token数成正比
- 不同场景需要不同长度的回复
- 个人发言150字足够，总结需要更长

**结论**：差异化配置，平衡成本和效果

---

### 决策2：为什么压缩历史时保留12条？
**考虑**：
- 4个角色 × 3轮 = 12条 能保留完整的近期讨论
- 过少（如6条）会导致讨论不连贯
- 过多（如20条）会导致上下文仍然过长

**结论**：12条是经验值，可根据实际情况调整为8-16

---

### 决策3：为什么总结阶段不压缩历史？
**考虑**：
- 总结需要看到完整的讨论过程
- 总结只执行1次，不存在累积问题
- 压缩会导致总结遗漏重要信息

**结论**：总结时使用完整历史，但提供充足的输出token（3000）

---

### 决策4：为什么不用LLM生成历史摘要？
**考虑**：
- 用LLM生成摘要会增加API调用次数和成本
- 简单的"省略中间部分"策略已经足够有效
- 滑动窗口保留最近发言，符合人类对话习惯

**结论**：当前采用简单策略，如需更智能可后续优化

---

## 🧪 测试与验证

### 自动测试
运行 `test_fix.py` 自动检查：
```bash
python test_fix.py
```

### 手动验证清单
- [ ] pipeline_result.txt 技术负责人有完整输出（包含技术选型、架构、排期、预算）
- [ ] social_result.txt 所有角色发言都非空（至少50字以上）
- [ ] social_result.txt 会议总结完整（包含共识、分歧、建议）
- [ ] 运行过程中没有 `[ERROR: ...]` 标记
- [ ] 控制台显示了token使用诊断信息

---

## 🔮 未来优化方向

### 优化1：智能历史摘要
用LLM生成前期讨论的结构化摘要，而非简单省略

### 优化2：动态token分配
根据实时输入长度动态调整max_tokens

### 优化3：分阶段讨论
在第3轮后生成中期总结，清空历史重新开始

### 优化4：Token使用监控
记录每次API调用的token使用情况，生成统计报告

### 优化5：角色记忆系统
为每个角色维护独立的"记忆向量"，提取关键立场

---

## 📚 相关文档

- [README_FIX.md](README_FIX.md) - 详细修复说明
- [test_fix.py](test_fix.py) - 自动测试脚本

---

## 🙏 致谢

问题由 MINMAX 初步诊断，修复方案由 Claude Code 实现。

修复完成时间：2026-02-08
