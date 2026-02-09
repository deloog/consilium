# -*- coding: utf-8 -*-
"""
混合模式 v7.6 - 基于v7.5 + 迭代次数硬限制

v7.6优化：
1. 继承v7.5的所有机制（细节检查、创新引导、六重控制）
2. 新增：迭代次数硬限制（控制点12）
   - 价值守护者重试：最多1次
   - LLM API调用：最多3次重试
   - 防止极端情况下的死循环

基于方案A：只添加迭代限制，不增加其他复杂机制
预期：稳定性提升，防止极端情况，对得分无直接影响

注意：此文件为开源版本，API密钥需要通过环境变量设置
示例：export DEEPSEEK_API_KEY="your-api-key-here"
"""

import os
import sys
import time
from openai import OpenAI

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# API配置 - 从环境变量读取，开源版本不包含硬编码密钥
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

if not DEEPSEEK_API_KEY:
    print("⚠️ 警告：未设置 DEEPSEEK_API_KEY 环境变量")
    print("请设置：export DEEPSEEK_API_KEY='your-api-key-here' (Linux/Mac)")
    print("或：set DEEPSEEK_API_KEY=your-api-key-here (Windows)")
    print("程序将继续运行，但LLM调用将失败\n")

ds_client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

# ============ v7.6新增：迭代次数硬限制配置 ============
MAX_ITERATIONS = {
    "guardian_retry": 1,      # 价值守护者重试最多1次
    "llm_api_retry": 3,       # LLM API调用最多3次重试
    "phase0_rounds": 3,       # 阶段0固定3轮讨论
}

# 全局计数器
iteration_counters = {
    "guardian_retry_count": 0,
}

# 客户需求 - 可以通过环境变量覆盖
DEFAULT_REQUIREMENT = """
客户需求：我想做一个面向老年人的短视频App。
- 要简单易用,老年人能轻松上手
- 但也要有强大的AI编辑功能（一键生成片头片尾、自动字幕、AI配乐）
- 要有社交功能，能让老年人和家人互动
- 预算有限，总共50万人民币
- 三个月内上线第一版
"""

REQUIREMENT = os.getenv("CONCILIUM_REQUIREMENT", DEFAULT_REQUIREMENT.strip())

# ============ v7.5新增：细节完整性检查清单 ============
DETAIL_CHECKLIST = {
    "产品经理": """
【PRD必须包含】
1. 用户画像：年龄段、技术水平、使用场景
2. 功能优先级：P0/P1/P2分级
3. 竞品分析：至少2个竞品的优劣势
4. 风险预案：至少列出3个主要风险及应对
""",

    "技术负责人": """
【技术方案必须包含】
1. 技术栈选型：前端/后端/数据库及理由
2. 核心API设计：至少列出3个关键接口
3. 第三方服务：具体服务商名称和集成方案
4. 部署架构：简要说明服务器部署方案
"""
}

# ============ v7.5新增：创新引导（优化版） ============
INNOVATION_GUIDANCE = """
【创新平衡原则】
- 核心功能必须保留（不能简单砍掉）
- 在预算约束下寻找创新解决方案
- 优先用技术手段（开源/API）替代功能删减
- 适度简化但不丧失核心价值
"""

# ============ 消极话术列表（继承v7.0） ============
NEGATIVE_PHRASES = [
    "砍掉", "删除", "去掉", "省略", "砍",
    "后续迭代", "下一版本", "先不做", "以后再",
    "建议简化", "建议放弃", "不建议做", "不做",
    "成本太高", "时间不够", "做不到", "无法实现",
    "不切实际", "太复杂", "风险太大",
]

# ============ 阶段0：角色定义（继承v7.0） ============
PHASE0_ROLES = {
    "产品经理·李明": """你是产品经理李明，负责理解客户需求，平衡各方意见，做出决策。
你的职责是确保核心需求被满足，而不是轻易妥协。
要求：每次发言150字内，语气坚定。""",

    "用户代表·张阿姨": """你是60岁的张阿姨，代表老年用户。
你会表达老年人的真实感受和需求。
要求：每次发言120字内，口语化表达。""",

    "技术负责人·老王": """你是技术负责人老王，评估技术可行性，提出技术方案。
你的职责是找到实现方法，而不是简单说"做不到"。
要求：每次发言150字内，提供具体技术方案。""",

    "成本核算专家·刘总": """你是成本专家刘总，核算成本，提供多种方案。
你的职责是优化成本，而不是简单砍功能。
要求：每次发言150字内，必须提供方案A/B/C三种选择。""",
}

# ============ 价值守护者（继承v7.0） ============
VALUE_GUARDIAN_PROMPT = """你是价值守护者，快速检查（100字内）：
【客户要求】强大AI编辑功能：
1. 一键生成片头片尾
2. 自动字幕
3. AI配乐

【检查标准】
- 完全保留（3个都有） → ✅通过
- 部分保留（≥2个核心功能） → ✅通过
- 只保留1个或全砍 → ❌需要重新讨论
"""

# ============ 阶段1、2角色（继承v7.0） ============
PHASE1_ROLES = {
    "产品经理": "你是产品经理，根据阶段0的决策，撰写详细的PRD（包含功能范围、用户场景、优先级）。",
    "UI设计师": "你是UI设计师，根据PRD和适老化要求，设计界面方案（包含交互流程、视觉规范）。",
    "技术负责人": "你是技术负责人，根据PRD，给出完整的技术方案（包含技术栈、架构设计、排期）。",
}

PHASE2_ROLES = {
    "产品经理·李明": "检查PRD是否与阶段0决策一致，是否有范围蔓延。",
    "技术负责人·老王": "识别技术风险和资源黑洞。",
    "成本核算专家·刘总": "核算预算，识别隐藏成本。",
    "用户代表·张阿姨": "从老年用户角度，检查方案是否真的易用。",
}

FINAL_REVIEW_PROMPT = """你是项目评审专家。基于上述所有讨论和方案，给出最终评审意见：
- 评审结论：通过/有条件通过/不通过
- 评审意见（150字内）
"""


def call_llm(messages, temperature=0.7, max_tokens=1500):
    """
    调用DeepSeek LLM

    v7.6优化：使用MAX_ITERATIONS配置的重试次数
    """
    max_retries = MAX_ITERATIONS["llm_api_retry"]

    for attempt in range(max_retries):
        try:
            response = ds_client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            print(f"    ❌ 调用失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                # v7.6：达到最大重试次数，返回错误信息
                error_msg = f"[ERROR: API调用失败，已达到最大重试次数({max_retries})，错误: {str(e)}]"
                print(f"    ⚠️ {error_msg}")
                return error_msg


# ============ 六重控制机制（继承v7.0，略有优化） ============

def filter_negative_response(response, agent_name, role_prompt):
    """控制点1：消极话术拦截"""
    detected_phrases = [phrase for phrase in NEGATIVE_PHRASES if phrase in response]

    if detected_phrases:
        print(f"    ⚠️ 检测到消极话术: {', '.join(detected_phrases[:3])}...")
        print(f"    🔄 触发乐观化重写")

        rewrite_prompt = f"""
你刚才的回复包含消极话术：{', '.join(detected_phrases[:5])}

作为{agent_name}，请重新表达，遵循以下要求：

【强制要求】
1. 禁止使用"砍掉"、"后续迭代"、"做不到"等消极话术
2. 必须提供"如何在预算和时间内实现"的建设性方案
3. 语气积极、建设性

【原回复】
{response}

请重新表达（保持150字内）：
"""

        messages = [
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": rewrite_prompt}
        ]

        new_response = call_llm(messages, temperature=0.5)
        return new_response

    return response


def enforce_quality_solutions(response, agent_name, role_prompt):
    """控制点2：强制高质量多方案"""
    if agent_name != "成本核算专家·刘总":
        return response

    has_abc = all(f"方案{x}" in response for x in ['A', 'B', 'C'])

    if not has_abc:
        print(f"    ⚠️ 成本专家未提供多方案，要求补充")
        return response + "\n\n（提示：请提供方案A/B/C格式的3种方案）"

    negative_count = sum(1 for phrase in ["砍", "不做", "省略"] if phrase in response)

    if negative_count >= 2:
        print(f"    ⚠️ 方案质量不足，要求重新提供")

        rewrite_prompt = f"""
你提供的方案中，有多个在砍掉功能。请重新提供，遵循以下要求：

【强制要求】
- 方案A：全功能实现（3个AI功能都保留）
- 方案B：优化成本实现（3个AI功能都保留，用开源/API）⭐推荐
- 方案C：最小成本实现（至少保留2个核心AI功能）

【禁止】禁止多个方案都在砍功能

【原回复】{response}

请重新提供3个方案（150字内）：
"""

        messages = [
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": rewrite_prompt}
        ]

        new_response = call_llm(messages, temperature=0.5)
        return new_response

    return response


def inject_pm_aggressive_challenge(round_num, history):
    """控制点3：产品经理强制对抗（v7.5优化：加入创新引导）"""
    history_text = "\n".join(history)

    # 第1轮：预防性提醒 + 创新引导
    if round_num == 0:
        return f"""
【战略提醒】
客户明确要求"强大AI编辑功能"（3个功能）。
这是核心卖点，不能轻易砍掉。

{INNOVATION_GUIDANCE}
"""

    # 第2轮：强制对抗
    if round_num == 1:
        has_negative = any(phrase in history_text for phrase in ["砍", "删除", "不做", "后续", "简化"])

        if has_negative:
            return """
【强制质疑】
你注意到有人建议砍掉或推迟AI功能。作为产品经理，你必须强烈反对：

"AI是客户明确要求的核心功能，绝对不能砍！
老王（技术负责人），请给出在预算内实现AI的具体技术方案（开源/API）。
刘总（成本专家），请提供保留AI功能的优化成本方案，用技术手段降低成本。"

请用这种坚定的语气发言（120字内）。
"""

    # 第3轮：最终确认
    if round_num == 2:
        has_negative = any(phrase in history_text for phrase in ["砍", "不做", "省略"])

        if has_negative:
            return """
【最终确认】
这是最后一轮讨论。你必须确保AI功能完整保留（3个功能）。
如果方案中仍在砍功能，直接拒绝，要求团队提供保留AI的方案。
"""

    return ""


def force_tech_lead_solution(response, agent_name, role_prompt):
    """控制点4：技术负责人强制提供方案"""
    if agent_name != "技术负责人·老王":
        return response

    tech_negative_patterns = [
        "后续迭代", "下一版本", "先不做", "做不到",
        "建议简化", "不建议", "成本太高", "时间不够"
    ]

    detected = [pattern for pattern in tech_negative_patterns if pattern in response]

    if detected:
        print(f"    ⚠️ 技术负责人过于保守，强制要求提供方案")

        rewrite_prompt = f"""
你刚才的回复过于保守（包含：{', '.join(detected)}）。

作为技术负责人，你的职责是"找到实现方法"，而不是"说做不到"。

【强制要求】
请提供在预算（50万）和时间（3个月）内实现AI功能的技术方案：
- 自动字幕：开源Whisper模型或云服务API
- AI配乐：第三方API（网易云、QQ音乐）
- 片头片尾：视频模板+简单生成

【禁止】
- 禁止使用"后续迭代"等推脱话术
- 禁止直接说"做不到"

【原回复】{response}

请重新表达，提供具体可行的技术方案（120字内）：
"""

        messages = [
            {"role": "system", "content": role_prompt},
            {"role": "user", "content": rewrite_prompt}
        ]

        new_response = call_llm(messages, temperature=0.5)
        return new_response

    return response


def guide_user_rep_support_ai(response, agent_name, role_prompt, round_num):
    """控制点5：用户代表引导支持AI"""
    if agent_name != "用户代表·张阿姨":
        return response

    is_negative_to_ai = any(phrase in response for phrase in ["不需要", "太复杂", "用不来", "不要"])

    if is_negative_to_ai:
        if round_num == 0:
            return response  # 第1轮允许怀疑

        if round_num >= 1:
            print(f"    ⚠️ 用户代表过于保守，引导理解AI价值")

            guide_prompt = f"""
你刚才表达了对AI功能的担心。但请重新思考：

【AI对老年人的真实价值】
1. 自动字幕：说话自动变文字，方便耳背的老年人
2. AI配乐：一键加背景音乐，不用自己学
3. 片头片尾：一键生成，简化操作

这些功能是"简化"而不是"复杂化"。

【原回复】{response}

请重新表达（80字内，可以提出要求，但不要完全否定）：
"""

            messages = [
                {"role": "system", "content": role_prompt},
                {"role": "user", "content": guide_prompt}
            ]

            new_response = call_llm(messages, temperature=0.6)
            return new_response

    return response


def check_guardian_and_retry(phase0_decision):
    """
    控制点6：价值守护者精确否决

    v7.6优化：无需retry_count参数，使用全局计数器
    """
    messages = [
        {"role": "system", "content": VALUE_GUARDIAN_PROMPT},
        {"role": "user", "content": f"""
【阶段0决策清单】
{phase0_decision}

请严格按照标准检查。
"""}
    ]

    guardian_check = call_llm(messages, temperature=0.3, max_tokens=500)

    guardian_challenge = ""
    if "【质疑】" in guardian_check:
        guardian_challenge = guardian_check.split("【质疑】")[-1].strip()

    return guardian_check, guardian_challenge


# ============ v7.5新增：细节完整性检查 ============
def check_phase1_details(agent_name, response):
    """检查阶段1输出的细节完整性"""
    if agent_name not in DETAIL_CHECKLIST:
        return response

    checklist = DETAIL_CHECKLIST[agent_name]

    # 简单检查：如果输出过短，提示补充细节
    if len(response) < 200:
        print(f"    ⚠️ {agent_name}输出过于简略，要求补充细节")

        supplement_prompt = f"""
你刚才的输出过于简略。请根据以下清单补充细节：

{checklist}

【原输出】
{response}

请补充完整（300字内）：
"""

        # 这里可以选择重新调用LLM补充，或只是提示
        # 为了控制成本，v7.5只做提示，不强制重写
        return response + f"\n\n【提示】请补充：{checklist}"

    return response


# ============ 阶段0：三轮讨论（继承v7.0） ============
def run_phase0():
    """
    阶段0：需求决策会议（六重流程控制）

    v7.6优化：添加价值守护者重试次数限制
    """

    def run_phase0_inner(guardian_challenge=""):
        history = []
        result = []

        result.append("="*70)
        if guardian_challenge:
            result.append("【阶段0：需求决策会议 - 重新讨论】")
            result.append(f"【价值守护者质疑】{guardian_challenge}")
        else:
            result.append("【阶段0：需求决策会议】（3轮讨论，4人参与，六重流程控制 + v7.5优化）")
        result.append("="*70 + "\n")

        # v7.6：使用配置的轮次
        max_rounds = MAX_ITERATIONS["phase0_rounds"]

        for round_num in range(max_rounds):
            result.append(f"--- 第{round_num+1}轮讨论 ---")
            print(f"\n阶段0 - 第{round_num+1}轮讨论")

            round_discussions = []

            for agent_name, agent_prompt in PHASE0_ROLES.items():
                context = f"""
【客户需求】
{REQUIREMENT}

【历史讨论】
{chr(10).join(history[-12:])}
"""

                if agent_name == "产品经理·李明":
                    pm_challenge = inject_pm_aggressive_challenge(round_num, history)
                    if pm_challenge:
                        context += f"\n{pm_challenge}"

                if guardian_challenge and round_num == 0 and agent_name == "产品经理·李明":
                    context += f"\n\n【特别注意】价值守护者的质疑：{guardian_challenge}"

                messages = [
                    {"role": "system", "content": agent_prompt},
                    {"role": "user", "content": f"{context}\n\n现在是第{round_num+1}轮讨论，请发表你的观点。"}
                ]

                response = call_llm(messages)

                # 六重控制
                response = filter_negative_response(response, agent_name, agent_prompt)
                response = enforce_quality_solutions(response, agent_name, agent_prompt)
                response = force_tech_lead_solution(response, agent_name, agent_prompt)
                response = guide_user_rep_support_ai(response, agent_name, agent_prompt, round_num)

                round_discussions.append(f"【{agent_name}】{response}")
                result.append(f"【{agent_name}】{response}")

                print(f"  {agent_name}: {response[:60]}...")

            history.extend(round_discussions)
            result.append("")

        # 生成决策清单
        messages = [
            {"role": "system", "content": "你是产品经理，负责总结决策。"},
            {"role": "user", "content": f"""
基于以上3轮讨论，生成决策清单：

【核心功能】
【砍掉的功能】
【预算和工期】

讨论历史：
{chr(10).join(history)}

请用200字内总结。
"""}
        ]

        decision = call_llm(messages, temperature=0.3)

        result.append("-"*70)
        result.append("【阶段0总结：决策清单】")
        result.append("-"*70)
        result.append(decision)
        result.append("")

        print("\n阶段0总结完成\n")

        return "\n".join(result), decision

    # 主流程
    print("="*70)
    print("🎯 开始阶段0（六重流程控制 + v7.5优化 + v7.6迭代限制）")
    print("="*70)

    phase0_result, decision = run_phase0_inner()

    # 价值守护者检查
    print("\n" + "-"*70)
    print("价值守护者检查")
    print("-"*70)

    guardian_check, guardian_challenge = check_guardian_and_retry(decision)

    phase0_result += "-"*70 + "\n"
    phase0_result += "【价值守护者检查】\n"
    phase0_result += "-"*70 + "\n"
    phase0_result += guardian_check + "\n"

    # v7.6：检查是否需要重试，并验证重试次数
    if "❌需要重新讨论" in guardian_check:
        current_retry = iteration_counters["guardian_retry_count"]
        max_retry = MAX_ITERATIONS["guardian_retry"]

        if current_retry < max_retry:
            print(f"\n⚠️ 价值守护者否决！触发重新讨论（第{current_retry+1}/{max_retry}次重试）\n")
            phase0_result += f"\n⚠️ 价值守护者要求重新讨论！（第{current_retry+1}/{max_retry}次重试）\n"

            iteration_counters["guardian_retry_count"] += 1

            phase0_result_2, decision_2 = run_phase0_inner(guardian_challenge)
            phase0_result += "\n" + phase0_result_2

            print("\n" + "-"*70)
            print("价值守护者二次检查")
            print("-"*70)

            guardian_check_2, _ = check_guardian_and_retry(decision_2)

            phase0_result += "-"*70 + "\n"
            phase0_result += "【价值守护者二次检查】\n"
            phase0_result += "-"*70 + "\n"
            phase0_result += guardian_check_2 + "\n"

            decision = decision_2
        else:
            # v7.6：达到最大重试次数，强制通过
            print(f"\n⚠️ 价值守护者否决，但已达到最大重试次数({max_retry})，强制进入下一阶段\n")
            phase0_result += f"\n⚠️ 已达到价值守护者最大重试次数({max_retry})，强制通过（可能存在风险）\n"

    return phase0_result, decision


# ============ 阶段1：流水线生产（v7.5优化：加入细节检查） ============
def run_phase1(decision):
    """阶段1：流水线生产（v7.5优化版）"""
    result = []
    result.append("="*70)
    result.append("【阶段1：流水线生产】（v7.5优化：细节完整性检查）")
    result.append("="*70 + "\n")

    print("\n" + "="*70)
    print("阶段1 - 流水线生产（v7.5优化）")
    print("="*70)

    outputs = {}

    for agent_name, agent_prompt in PHASE1_ROLES.items():
        print(f"\n阶段1 - {agent_name}")

        messages = [
            {"role": "system", "content": agent_prompt},
            {"role": "user", "content": f"""
【阶段0决策】
{decision}

请输出你的工作成果（300字内）。
"""}
        ]

        response = call_llm(messages, temperature=0.5, max_tokens=2000)

        # v7.5新增：细节检查
        response = check_phase1_details(agent_name, response)

        outputs[agent_name] = response

        result.append(f"--- {agent_name}输出 ---")
        result.append(response)
        result.append("")

        print(f"  {agent_name}: 完成")

    print("\n阶段1完成")

    return "\n".join(result), outputs


# ============ 阶段2、最终评审（继承v7.0） ============
def run_phase2(decision, phase1_outputs):
    """阶段2：质检会议"""
    result = []
    result.append("="*70)
    result.append("【阶段2：质检会议】")
    result.append("="*70)

    print("\n" + "="*70)
    print("阶段2 - 质检会议")
    print("="*70)

    prd = phase1_outputs.get("产品经理", "")
    ui = phase1_outputs.get("UI设计师", "")
    tech = phase1_outputs.get("技术负责人", "")

    for agent_name, agent_task in PHASE2_ROLES.items():
        print(f"\n阶段2 - {agent_name}")

        messages = [
            {"role": "system", "content": f"你是{agent_name}，任务：{agent_task}"},
            {"role": "user", "content": f"""
【阶段0决策】
{decision}

【PRD】
{prd}

【UI方案】
{ui}

【技术方案】
{tech}

请给出质检意见（200字内）。
"""}
        ]

        response = call_llm(messages, temperature=0.5, max_tokens=1000)
        result.append(f"【{agent_name}】{response}")

        print(f"  {agent_name}: 完成")

    result.append("")
    print("\n阶段2完成")

    return "\n".join(result)


def run_final_review(full_context):
    """最终评审"""
    result = []
    result.append("="*70)
    result.append("【最终评审】")
    result.append("="*70)

    print("\n" + "="*70)
    print("最终评审")
    print("="*70)

    messages = [
        {"role": "system", "content": FINAL_REVIEW_PROMPT},
        {"role": "user", "content": full_context}
    ]

    review = call_llm(messages, temperature=0.3, max_tokens=1000)
    result.append(review)

    print("\n最终评审完成")

    return "\n".join(result)


# ============ 主流程 ============
def main():
    print("="*70)
    print("混合模式 v7.6 实验输出（v7.5 + 迭代次数硬限制）")
    print("="*70)
    print("\nv7.6优化：")
    print("- 继承v7.5的所有机制（细节检查、创新引导、六重控制）")
    print("- 新增：迭代次数硬限制（防止极端情况死循环）")
    print(f"  * 价值守护者重试：最多{MAX_ITERATIONS['guardian_retry']}次")
    print(f"  * LLM API重试：最多{MAX_ITERATIONS['llm_api_retry']}次")
    print(f"  * 阶段0讨论：固定{MAX_ITERATIONS['phase0_rounds']}轮")
    print("="*70)
    print("\n客户需求：")
    print(REQUIREMENT)
    print("\n")

    phase0_result, decision = run_phase0()
    phase1_result, phase1_outputs = run_phase1(decision)
    phase2_result = run_phase2(decision, phase1_outputs)

    full_result = f"""
客户需求：
{REQUIREMENT}

{phase0_result}
{phase1_result}
{phase2_result}
"""

    final_review = run_final_review(full_result)
    full_result += "\n" + final_review

    # v7.6：在结果末尾添加迭代统计
    iteration_stats = f"""

{"="*70}
【v7.6 迭代统计】
{"="*70}
价值守护者重试次数: {iteration_counters['guardian_retry_count']}/{MAX_ITERATIONS['guardian_retry']}
阶段0讨论轮次: {MAX_ITERATIONS['phase0_rounds']}轮（固定）
LLM API重试配置: 最多{MAX_ITERATIONS['llm_api_retry']}次
"""
    full_result += iteration_stats

    output_file = "hybrid_v7_6_result.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("混合模式 v7.6 实验输出（v7.5 + 迭代次数硬限制）\n")
        f.write("="*70 + "\n\n")
        f.write(full_result)

    print("\n" + "="*70)
    print(f"✅ 混合模式 v7.6 运行完成！")
    print(f"📄 结果已保存到 {output_file}")
    print("\n【v7.6 迭代统计】")
    print(f"价值守护者重试: {iteration_counters['guardian_retry_count']}/{MAX_ITERATIONS['guardian_retry']}次")
    print(f"阶段0讨论轮次: {MAX_ITERATIONS['phase0_rounds']}轮")
    print("="*70)


if __name__ == "__main__":
    main()
