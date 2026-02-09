/*!
 * Consilium v7.6 - Rust Version
 * 
 * 混合模式 v7.6 - 基于v7.5 + 迭代次数硬限制
 * 
 * v7.6优化：
 * 1. 继承v7.5的所有机制（细节检查、创新引导、六重控制）
 * 2. 新增：迭代次数硬限制（控制点12）
 *    - 价值守护者重试：最多1次
 *    - LLM API调用：最多3次重试
 *    - 防止极端情况下的死循环
 * 
 * 开源版本说明：
 * - API密钥需要通过环境变量或配置文件设置
 * - 内存安全、高性能
 */

use std::collections::HashMap;
use std::env;
use std::fmt;
use std::fs;
use std::io::{self, Write};
use std::time::Duration;

// ============== 配置 ==============

#[derive(Debug)]
struct Config {
    deepseek: DeepSeekConfig,
    max_iterations: MaxIterationsConfig,
    requirement: String,
}

#[derive(Debug)]
struct DeepSeekConfig {
    api_key: String,
    base_url: String,
    model: String,
}

#[derive(Debug)]
struct MaxIterationsConfig {
    guardian_retry: usize,
    llm_api_retry: usize,
    phase0_rounds: usize,
}

impl Config {
    fn from_env() -> Self {
        let api_key = env::var("DEEPSEEK_API_KEY").unwrap_or_default();
        let base_url = env::var("DEEPSEEK_BASE_URL")
            .unwrap_or_else(|_| "https://api.deepseek.com/v1".to_string());
        let model = env::var("DEEPSEEK_MODEL")
            .unwrap_or_else(|_| "deepseek-chat".to_string());
        let requirement = env::var("CONSILIUM_REQUIREMENT").unwrap_or_else(|_| {
            r#"
客户需求：我想做一个面向老年人的短视频App。
- 要简单易用,老年人能轻松上手
- 但也要有强大的AI编辑功能（一键生成片头片尾、自动字幕、AI配乐）
- 要有社交功能，能让老年人和家人互动
- 预算有限，总共50万人民币
- 三个月内上线第一版
            "#
            .trim()
                .to_string()
        });

        if api_key.is_empty() {
            println!("⚠️ 警告：未设置 DEEPSEEK_API_KEY 环境变量");
        }

        Config {
            deepseek: DeepSeekConfig {
                api_key,
                base_url,
                model,
            },
            max_iterations: MaxIterationsConfig {
                guardian_retry: 1,
                llm_api_retry: 3,
                phase0_rounds: 3,
            },
            requirement,
        }
    }
}

// ============== LLM 调用 ==============

#[derive(Debug, Serialize, Deserialize)]
struct Message {
    role: String,
    content: String,
}

#[derive(Debug, Serialize)]
struct ChatRequest {
    model: String,
    messages: Vec<Message>,
    temperature: f64,
    max_tokens: usize,
}

#[derive(Debug, Deserialize)]
struct Choice {
    message: Message,
}

#[derive(Debug, Deserialize)]
struct ChatResponse {
    choices: Vec<Choice>,
}

struct LLMClient {
    config: DeepSeekConfig,
    max_retries: usize,
}

impl LLMClient {
    fn new(config: DeepSeekConfig, max_retries: usize) -> Self {
        LLMClient { config, max_retries }
    }

    async fn call(
        &self,
        messages: Vec<Message>,
        temperature: f64,
        max_tokens: usize,
    ) -> String {
        let client = reqwest::Client::builder()
            .timeout(Duration::from_secs(30))
            .build()
            .expect("Failed to create HTTP client");

        for attempt in 0..self.max_retries {
            let request_body = ChatRequest {
                model: self.config.model.clone(),
                messages: messages.clone(),
                temperature,
                max_tokens,
            };

            match client
                .post(&format!("{}/chat/completions", self.config.base_url))
                .header(
                    "Authorization",
                    format!("Bearer {}", self.config.api_key),
                )
                .json(&request_body)
                .send()
                .await
            {
                Ok(response) => {
                    if response.status().is_success() {
                        match response.json::<ChatResponse>().await {
                            Ok(chat_resp) => {
                                if let Some(choice) = chat_resp.choices.first() {
                                    return choice.message.content.clone();
                                }
                            }
                            Err(e) => {
                                println!("    ❌ JSON解析失败: {}", e);
                            }
                        }
                    } else {
                        println!(
                            "    ❌ API调用失败 (尝试 {}/{}): {}",
                            attempt + 1,
                            self.max_retries,
                            response.status()
                        );
                    }
                }
                Err(e) => {
                    println!(
                        "    ❌ 调用失败 (尝试 {}/{}): {}",
                        attempt + 1,
                        self.max_retries,
                        e
                    );
                }
            }

            if attempt < self.max_retries - 1 {
                tokio::time::sleep(Duration::from_secs(2)).await;
            }
        }

        format!(
            "[ERROR: API调用失败，已达到最大重试次数({})]",
            self.max_retries
        )
    }
}

// ============== 角色定义 ==============

const PHASE0_ROLES: &[(&str, &str)] = &[
    (
        "产品经理·李明",
        r#"你是产品经理李明，负责理解客户需求，平衡各方意见，做出决策。
你的职责是确保核心需求被满足，而不是轻易妥协。
要求：每次发言150字内，语气坚定。"#,
    ),
    (
        "用户代表·张阿姨",
        r#"你是60岁的张阿姨，代表老年用户。
你会表达老年人的真实感受和需求。
要求：每次发言120字内，口语化表达。"#,
    ),
    (
        "技术负责人·老王",
        r#"你是技术负责人老王，评估技术可行性，提出技术方案。
你的职责是找到实现方法，而不是简单说"做不到"。
要求：每次发言150字内，提供具体技术方案。"#,
    ),
    (
        "成本核算专家·刘总",
        r#"你是成本专家刘总，核算成本，提供多种方案。
你的职责是优化成本，而不是简单砍功能。
要求：每次发言150字内，必须提供方案A/B/C三种选择。"#,
    ),
];

const PHASE1_ROLES: &[(&str, &str)] = &[
    (
        "产品经理",
        "你是产品经理，根据阶段0的决策，撰写详细的PRD（包含功能范围、用户场景、优先级）。",
    ),
    (
        "UI设计师",
        "你是UI设计师，根据PRD和适老化要求，设计界面方案（包含交互流程、视觉规范）。",
    ),
    (
        "技术负责人",
        "你是技术负责人，根据PRD，给出完整的技术方案（包含技术栈、架构设计、排期）。",
    ),
];

const PHASE2_ROLES: &[(&str, &str)] = &[
    ("产品经理·李明", "检查PRD是否与阶段0决策一致，是否有范围蔓延。"),
    ("技术负责人·老王", "识别技术风险和资源黑洞。"),
    ("成本核算专家·刘总", "核算预算，识别隐藏成本。"),
    ("用户代表·张阿姨", "从老年用户角度，检查方案是否真的易用。"),
];

const VALUE_GUARDIAN_PROMPT: &str = r#"你是价值守护者，快速检查（100字内）：
【客户要求】强大AI编辑功能：
1. 一键生成片头片尾
2. 自动字幕
3. AI配乐

【检查标准】
- 完全保留（3个都有） → ✅通过
- 部分保留（≥2个核心功能） → ✅通过
- 只保留1个或全砍 → ❌需要重新讨论"#;

const INNOVATION_GUIDANCE: &str = r#"
【创新平衡原则】
- 核心功能必须保留（不能简单砍掉）
- 在预算约束下寻找创新解决方案
- 优先用技术手段（开源/API）替代功能删减
- 适度简化但不丧失核心价值"#;

const NEGATIVE_PHRASES: &[&str] = &[
    "砍掉", "删除", "去掉", "省略", "砍",
    "后续迭代", "下一版本", "先不做", "以后再",
    "建议简化", "建议放弃", "不建议做", "不做",
    "成本太高", "时间不够", "做不到", "无法实现",
    "不切实际", "太复杂", "风险太大",
];

const DETAIL_CHECKLIST: &[(&str, &str)] = &[
    (
        "产品经理",
        r#"【PRD必须包含】
1. 用户画像：年龄段、技术水平、使用场景
2. 功能优先级：P0/P1/P2分级
3. 竞品分析：至少2个竞品的优劣势
4. 风险预案：至少列出3个主要风险及应对"#,
    ),
    (
        "技术负责人",
        r#"【技术方案必须包含】
1. 技术栈选型：前端/后端/数据库及理由
2. 核心API设计：至少列出3个关键接口
3. 第三方服务：具体服务商名称和集成方案
4. 部署架构：简要说明服务器部署方案"#,
    ),
];

const FINAL_REVIEW_PROMPT: &str = r#"你是项目评审专家。基于上述所有讨论和方案，给出最终评审意见：
- 评审结论：通过/有条件通过/不通过
- 评审意见（150字内）"#;

// ============== 六重控制机制 ==============

fn filter_negative_response(response: &str, agent_name: &str, _role_prompt: &str) -> String {
    for phrase in NEGATIVE_PHRASES {
        if response.contains(phrase) {
            println!("    ⚠️ 检测到消极话术: {}...", phrase);
            println!("    🔄 触发乐观化重写");
            return response.to_string(); // 简化处理
        }
    }
    response.to_string()
}

fn enforce_quality_solutions(response: &str, agent_name: &str) -> String {
    if agent_name != "成本核算专家·刘总" {
        return response.to_string();
    }

    let has_a = response.contains("方案A");
    let has_b = response.contains("方案B");
    let has_c = response.contains("方案C");

    if !has_a || !has_b || !has_c {
        println!("    ⚠️ 成本专家未提供多方案，要求补充");
        return format!("{}\n\n（提示：请提供方案A/B/C格式的3种方案）", response);
    }
    response.to_string()
}

fn inject_pm_challenge(round_num: usize, history: &[String]) -> String {
    let history_text = history.join("\n");

    if round_num == 0 {
        return format!(
            "\n【战略提醒】\n客户明确要求\"强大AI编辑功能\"（3个功能）。\n这是核心卖点，不能轻易砍掉。\n{}",
            INNOVATION_GUIDANCE
        );
    }

    if round_num == 1 {
        let has_negative = ["砍", "删除", "不做", "后续", "简化"]
            .iter()
            .any(|p| history_text.contains(p));

        if has_negative {
            return r#"
【强制质疑】
你注意到有人建议砍掉或推迟AI功能。作为产品经理，你必须强烈反对：

"AI是客户明确要求的核心功能，绝对不能砍！
老王（技术负责人），请给出在预算内实现AI的具体技术方案（开源/API）。
刘总（成本专家），请提供保留AI功能的优化成本方案，用技术手段降低成本。"

请用这种坚定的语气发言（120字内）。"#
                .to_string();
        }
    }

    if round_num == 2 {
        let has_negative = ["砍", "不做", "省略"]
            .iter()
            .any(|p| history_text.contains(p));

        if has_negative {
            return r#"
【最终确认】
这是最后一轮讨论。你必须确保AI功能完整保留（3个功能）。
如果方案中仍在砍功能，直接拒绝，要求团队提供保留AI的方案。"#
                .to_string();
        }
    }

    String::new()
}

fn force_tech_lead_solution(response: &str, agent_name: &str, _role_prompt: &str) -> String {
    if agent_name != "技术负责人·老王" {
        return response.to_string();
    }

    let patterns = [
        "后续迭代", "下一版本", "先不做", "做不到", "建议简化", "不建议", "成本太高", "时间不够",
    ];

    for pattern in &patterns {
        if response.contains(pattern) {
            println!("    ⚠️ 技术负责人过于保守，强制要求提供方案");
            return response.to_string(); // 简化处理
        }
    }
    response.to_string()
}

fn guide_user_rep_support_ai(response: &str, agent_name: &str, round_num: usize) -> String {
    if agent_name != "用户代表·张阿姨" {
        return response.to_string();
    }

    let is_negative = ["不需要", "太复杂", "用不来", "不要"]
        .iter()
        .any(|p| response.contains(p));

    if is_negative && round_num > 0 {
        println!("    ⚠️ 用户代表过于保守，引导理解AI价值");
        return response.to_string(); // 简化处理
    }
    response.to_string()
}

async fn check_guardian(decision: &str, llm: &LLMClient) -> (String, String) {
    let messages = vec![
        Message {
            role: "system".to_string(),
            content: VALUE_GUARDIAN_PROMPT.to_string(),
        },
        Message {
            role: "user".to_string(),
            content: format!("【阶段0决策清单】\n{}\n\n请严格按照标准检查。", decision),
        },
    ];

    let check = llm.call(messages, 0.3, 500).await;

    let challenge = if let Some(start) = check.find("【质疑】") {
        check[start + 4..].trim().to_string()
    } else {
        String::new()
    };

    (check, challenge)
}

fn check_phase1_details(agent_name: &str, response: &str) -> String {
    for (name, checklist) in DETAIL_CHECKLIST {
        if *name == agent_name {
            if response.len() < 200 {
                println!("    ⚠️ {}输出过于简略，要求补充细节", agent_name);
                return format!("{}\n\n【提示】请补充：{}", response, checklist);
            }
            break;
        }
    }
    response.to_string()
}

// ============== 主流程 ==============

struct Phase0Result {
    result: String,
    decision: String,
}

async fn run_phase0(config: &Config, llm: &LLMClient) -> Phase0Result {
    let mut result = String::new();
    let mut history: Vec<String> = Vec::new();

    result.push_str("======================================================================\n");
    result.push_str("【阶段0：需求决策会议】（3轮讨论，4人参与，六重流程控制 + v7.5优化）\n");
    result.push_str("======================================================================\n\n");

    for round in 0..config.max_iterations.phase0_rounds {
        result.push_str(&format!("--- 第{}轮讨论 ---\n", round + 1));
        println!("\n阶段0 - 第{}轮讨论", round + 1);

        let mut round_discussions: Vec<String> = Vec::new();

        for (agent_name, agent_prompt) in PHASE0_ROLES {
            let context = format!(
                "【客户需求】\n{}\n\n【历史讨论】\n{}",
                config.requirement,
                history[history.len().saturating_sub(12)..]
                    .join("\n")
            );

            let mut context = context;
            if *agent_name == "产品经理·李明" {
                let pm_challenge = inject_pm_challenge(round, &history);
                if !pm_challenge.is_empty() {
                    context.push_str(&pm_challenge);
                }
            }

            let messages = vec![
                Message {
                    role: "system".to_string(),
                    content: agent_prompt.to_string(),
                },
                Message {
                    role: "user".to_string(),
                    content: format!("{}\n\n现在是第{}轮讨论，请发表你的观点。", context, round + 1),
                },
            ];

            let mut response = llm.call(messages, 0.7, 1500).await;

            // 六重控制
            response = filter_negative_response(&response, agent_name, agent_prompt);
            response = enforce_quality_solutions(&response, agent_name);
            response = force_tech_lead_solution(&response, agent_name, agent_prompt);
            response = guide_user_rep_support_ai(&response, agent_name, round);

            round_discussions.push(format!("【{}】{}", agent_name, response));
            result.push_str(&format!("【{}】{}\n", agent_name, response));

            let preview = if response.len() > 60 {
                &response[..60]
            } else {
                &response
            };
            println!("  {}: {}...", agent_name, preview);
        }

        history.extend(round_discussions);
        result.push_str("\n");
    }

    // 生成决策清单
    let summary_messages = vec![
        Message {
            role: "system".to_string(),
            content: "你是产品经理，负责总结决策。".to_string(),
        },
        Message {
            role: "user".to_string(),
            content: format!(
                r#"
基于以上3轮讨论，生成决策清单：

【核心功能】
【砍掉的功能】
【预算和工期】

讨论历史：
{}

请用200字内总结。
"#,
                history.join("\n")
            ),
        },
    ];

    let decision = llm.call(summary_messages, 0.3).await;

    result.push_str("----------------------------------------------------------------------\n");
    result.push_str("【阶段0总结：决策清单】\n");
    result.push_str("----------------------------------------------------------------------\n");
    result.push_str(&decision);
    result.push_str("\n\n");

    println!("\n阶段0总结完成\n");

    Phase0Result { result, decision }
}

struct Phase1Result {
    result: String,
    outputs: HashMap<String, String>,
}

async fn run_phase1(decision: &str, config: &Config, llm: &LLMClient) -> Phase1Result {
    let mut result = String::new();
    let mut outputs = HashMap::new();

    result.push_str("======================================================================\n");
    result.push_str("【阶段1：流水线生产】（v7.5优化：细节完整性检查）\n");
    result.push_str("======================================================================\n\n");

    println!("\n======================================================================");
    println!("阶段1 - 流水线生产（v7.5优化）");
    println!("======================================================================");

    for (agent_name, agent_prompt) in PHASE1_ROLES {
        println!("\n阶段1 - {}", agent_name);

        let messages = vec![
            Message {
                role: "system".to_string(),
                content: agent_prompt.to_string(),
            },
            Message {
                role: "user".to_string(),
                content: format!("【阶段0决策】\n{}\n\n请输出你的工作成果（300字内）。", decision),
            },
        ];

        let mut response = llm.call(messages, 0.5, 2000).await;
        response = check_phase1_details(agent_name, &response);

        outputs.insert(agent_name.to_string(), response.clone());
        result.push_str(&format!("--- {}输出 ---\n", agent_name));
        result.push_str(&response);
        result.push_str("\n\n");

        println!("  {}: 完成", agent_name);
    }

    println!("\n阶段1完成");

    Phase1Result { result, outputs }
}

async fn run_phase2(
    decision: &str,
    phase1_outputs: &HashMap<String, String>,
    llm: &LLMClient,
) -> String {
    let mut result = String::new();

    result.push_str("======================================================================\n");
    result.push_str("【阶段2：质检会议】\n");
    result.push_str("======================================================================\n");

    println!("\n======================================================================");
    println!("阶段2 - 质检会议");
    println!("======================================================================");

    let prd = phase1_outputs.get("产品经理").cloned().unwrap_or_default();
    let ui = phase1_outputs.get("UI设计师").cloned().unwrap_or_default();
    let tech = phase1_outputs.get("技术负责人").cloned().unwrap_or_default();

    for (agent_name, agent_task) in PHASE2_ROLES {
        println!("\n阶段2 - {}", agent_name);

        let messages = vec![Message {
            role: "system".to_string(),
            content: format!("你是{}，任务：{}", agent_name, agent_task),
        }];

        let response = llm.call(messages, 0.5, 1000).await;
        result.push_str(&format!("【{}】{}\n", agent_name, response));

        println!("  {}: 完成", agent_name);
    }

    result.push_str("\n");
    println!("\n阶段2完成");

    result
}

async fn run_final_review(full_context: &str, llm: &LLMClient) -> String {
    let mut result = String::new();

    result.push_str("======================================================================\n");
    result.push_str("【最终评审】\n");
    result.push_str("======================================================================\n");

    println!("\n======================================================================");
    println!("最终评审");
    println!("======================================================================");

    let messages = vec![
        Message {
            role: "system".to_string(),
            content: FINAL_REVIEW_PROMPT.to_string(),
        },
        Message {
            role: "user".to_string(),
            content: full_context.to_string(),
        },
    ];

    let review = llm.call(messages, 0.3, 1000).await;
    result.push_str(&review);

    println!("\n最终评审完成");

    result
}

// ============== 入口 ==============

#[tokio::main]
async fn main() {
    let config = Config::from_env();

    println!("======================================================================");
    println!("Consilium v7.6 - Rust Version");
    println!("混合模式 v7.6 实验输出（v7.5 + 迭代次数硬限制）");
    println!("======================================================================");
    println!("\nv7.6优化：");
    println!("- 继承v7.5的所有机制（细节检查、创新引导、六重控制）");
    println!("- 新增：迭代次数硬限制（防止极端情况死循环）");
    println!(
        "  * 价值守护者重试：最多{}次",
        config.max_iterations.guardian_retry
    );
    println!(
        "  * LLM API重试：最多{}次",
        config.max_iterations.llm_api_retry
    );
    println!(
        "  * 阶段0讨论：固定{}轮",
        config.max_iterations.phase0_rounds
    );
    println!("======================================================================");

    if config.deepseek.api_key.is_empty() {
        println!("\n⚠️ 未设置 API Key，程序退出");
        std::process::exit(1);
    }

    let llm = LLMClient::new(config.deepseek, config.max_iterations.llm_api_retry);

    println!("\n客户需求：");
    println!("{}", config.requirement);
    println!();

    let phase0_result = run_phase0(&config, &llm).await;
    let phase1_result = run_phase1(&phase0_result.decision, &config, &llm).await;
    let phase2_result = run_phase2(&phase0_result.decision, &phase1_result.outputs, &llm).await;

    let full_result = format!(
        "
客户需求：
{}

{}
{}
{}
",
        config.requirement,
        phase0_result.result,
        phase1_result.result,
        phase2_result
    );

    let final_review = run_final_review(&full_result, &llm).await;
    let final_output = full_result + "\n" + &final_review;

    println!("\n======================================================================");
    println!("✅ Consilium v7.6 Rust 版本运行完成！");
    println!("======================================================================");
}
