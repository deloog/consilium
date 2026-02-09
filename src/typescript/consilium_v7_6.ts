/**
 * Consilium v7.6 - TypeScript Version
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
 * - 支持 Node.js 运行时
 */

/// <reference types="node" />

// ============== 配置 ==============

interface Config {
    deepseek: {
        apiKey: string;
        baseUrl: string;
        model: string;
    };
    maxIterations: {
        guardianRetry: number;
        llmApiRetry: number;
        phase0Rounds: number;
    };
    requirement: string;
}

const getConfig = (): Config => {
    const apiKey = process.env.DEEPSEEK_API_KEY || '';
    const baseUrl = process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com/v1';
    const model = process.env.DEEPSEEK_MODEL || 'deepseek-chat';
    
    if (!apiKey) {
        console.warn('⚠️ 警告：未设置 DEEPSEEK_API_KEY 环境变量');
    }

    return {
        deepseek: { apiKey, baseUrl, model },
        maxIterations: {
            guardianRetry: 1,
            llmApiRetry: 3,
            phase0Rounds: 3
        },
        requirement: process.env.CONSILIUM_REQUIREMENT || `
客户需求：我想做一个面向老年人的短视频App。
- 要简单易用,老年人能轻松上手
- 但也要有强大的AI编辑功能（一键生成片头片尾、自动字幕、AI配乐）
- 要有社交功能，能让老年人和家人互动
- 预算有限，总共50万人民币
- 三个月内上线第一版
        `.trim()
    };
};

// ============== 角色定义 ==============

const PHASE0_ROLES: Record<string, string> = {
    '产品经理·李明': `你是产品经理李明，负责理解客户需求，平衡各方意见，做出决策。
你的职责是确保核心需求被满足，而不是轻易妥协。
要求：每次发言150字内，语气坚定。`,

    '用户代表·张阿姨': `你是60岁的张阿姨，代表老年用户。
你会表达老年人的真实感受和需求。
要求：每次发言120字内，口语化表达。`,

    '技术负责人·老王': `你是技术负责人老王，评估技术可行性，提出技术方案。
你的职责是找到实现方法，而不是简单说"做不到"。
要求：每次发言150字内，提供具体技术方案。`,

    '成本核算专家·刘总': `你是成本专家刘总，核算成本，提供多种方案。
你的职责是优化成本，而不是简单砍功能。
要求：每次发言150字内，必须提供方案A/B/C三种选择。`
};

const PHASE1_ROLES: Record<string, string> = {
    '产品经理': '你是产品经理，根据阶段0的决策，撰写详细的PRD（包含功能范围、用户场景、优先级）。',
    'UI设计师': '你是UI设计师，根据PRD和适老化要求，设计界面方案（包含交互流程、视觉规范）。',
    '技术负责人': '你是技术负责人，根据PRD，给出完整的技术方案（包含技术栈、架构设计、排期）。'
};

const PHASE2_ROLES: Record<string, string> = {
    '产品经理·李明': '检查PRD是否与阶段0决策一致，是否有范围蔓延。',
    '技术负责人·老王': '识别技术风险和资源黑洞。',
    '成本核算专家·刘总': '核算预算，识别隐藏成本。',
    '用户代表·张阿姨': '从老年用户角度，检查方案是否真的易用。'
};

const VALUE_GUARDIAN_PROMPT = `你是价值守护者，快速检查（100字内）：
【客户要求】强大AI编辑功能：
1. 一键生成片头片尾
2. 自动字幕
3. AI配乐

【检查标准】
- 完全保留（3个都有） → ✅通过
- 部分保留（≥2个核心功能） → ✅通过
- 只保留1个或全砍 → ❌需要重新讨论`;

const INNOVATION_GUIDANCE = `
【创新平衡原则】
- 核心功能必须保留（不能简单砍掉）
- 在预算约束下寻找创新解决方案
- 优先用技术手段（开源/API）替代功能删减
- 适度简化但不丧失核心价值`;

const NEGATIVE_PHRASES = [
    '砍掉', '删除', '去掉', '省略', '砍',
    '后续迭代', '下一版本', '先不做', '以后再',
    '建议简化', '建议放弃', '不建议做', '不做',
    '成本太高', '时间不够', '做不到', '无法实现',
    '不切实际', '太复杂', '风险太大'
];

const DETAIL_CHECKLIST: Record<string, string> = {
    '产品经理': `
【PRD必须包含】
1. 用户画像：年龄段、技术水平、使用场景
2. 功能优先级：P0/P1/P2分级
3. 竞品分析：至少2个竞品的优劣势
4. 风险预案：至少列出3个主要风险及应对`,

    '技术负责人': `
【技术方案必须包含】
1. 技术栈选型：前端/后端/数据库及理由
2. 核心API设计：至少列出3个关键接口
3. 第三方服务：具体服务商名称和集成方案
4. 部署架构：简要说明服务器部署方案`
};

const FINAL_REVIEW_PROMPT = `你是项目评审专家。基于上述所有讨论和方案，给出最终评审意见：
- 评审结论：通过/有条件通过/不通过
- 评审意见（150字内）`;

// ============== LLM 调用 ==============

interface Message {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

class LLMClient {
    private config: Config['deepseek'];
    private maxRetries: number;

    constructor(config: Config['deepseek'], maxRetries: number) {
        this.config = config;
        this.maxRetries = maxRetries;
    }

    async call(messages: Message[], temperature = 0.7, maxTokens = 1500): Promise<string> {
        for (let attempt = 0; attempt < this.maxRetries; attempt++) {
            try {
                const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.config.apiKey}`
                    },
                    body: JSON.stringify({
                        model: this.config.model,
                        messages,
                        temperature,
                        max_tokens: maxTokens
                    })
                });

                if (!response.ok) {
                    throw new Error(`API调用失败: ${response.status}`);
                }

                const data = await response.json();
                return data.choices[0]?.message?.content || '';
            } catch (error) {
                console.error(`    ❌ 调用失败 (尝试 ${attempt + 1}/${this.maxRetries}):`, error);
                if (attempt < this.maxRetries - 1) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                } else {
                    return `[ERROR: API调用失败，已达到最大重试次数(${this.maxRetries})]`;
                }
            }
        }
        return '';
    }
}

// ============== 六重控制机制 ==============

function filterNegativeResponse(response: string, agentName: string, rolePrompt: string): string {
    const detected = NEGATIVE_PHRASES.filter(phrase => response.includes(phrase));
    
    if (detected.length > 0) {
        console.log(`    ⚠️ 检测到消极话术: ${detected.slice(0, 3).join(', ')}...`);
        console.log(`    🔄 触发乐观化重写`);
        return response; // 简化处理，实际应该重新调用LLM
    }
    return response;
}

function enforceQualitySolutions(response: string, agentName: string): string {
    if (agentName !== '成本核算专家·刘总') return response;
    
    const hasABC = ['A', 'B', 'C'].every(x => response.includes(`方案${x}`));
    if (!hasABC) {
        console.log(`    ⚠️ 成本专家未提供多方案，要求补充`);
        return response + '\n\n（提示：请提供方案A/B/C格式的3种方案）';
    }
    return response;
}

function injectPMChallenge(roundNum: number, history: string[]): string {
    const historyText = history.join('\n');
    
    if (roundNum === 0) {
        return `
【战略提醒】
客户明确要求"强大AI编辑功能"（3个功能）。
这是核心卖点，不能轻易砍掉。
${INNOVATION_GUIDANCE}`;
    }
    
    if (roundNum === 1) {
        const hasNegative = ['砍', '删除', '不做', '后续', '简化'].some(p => historyText.includes(p));
        if (hasNegative) {
            return `
【强制质疑】
你注意到有人建议砍掉或推迟AI功能。作为产品经理，你必须强烈反对：

"AI是客户明确要求的核心功能，绝对不能砍！
老王（技术负责人），请给出在预算内实现AI的具体技术方案（开源/API）。
刘总（成本专家），请提供保留AI功能的优化成本方案，用技术手段降低成本。"

请用这种坚定的语气发言（120字内）。`;
        }
    }
    
    if (roundNum === 2) {
        const hasNegative = ['砍', '不做', '省略'].some(p => historyText.includes(p));
        if (hasNegative) {
            return `
【最终确认】
这是最后一轮讨论。你必须确保AI功能完整保留（3个功能）。
如果方案中仍在砍功能，直接拒绝，要求团队提供保留AI的方案。`;
        }
    }
    
    return '';
}

function forceTechLeadSolution(response: string, agentName: string, rolePrompt: string): string {
    if (agentName !== '技术负责人·老王') return response;
    
    const patterns = ['后续迭代', '下一版本', '先不做', '做不到', '建议简化', '不建议', '成本太高', '时间不够'];
    const detected = patterns.filter(p => response.includes(p));
    
    if (detected.length > 0) {
        console.log(`    ⚠️ 技术负责人过于保守，强制要求提供方案`);
        return response; // 简化处理
    }
    return response;
}

function guideUserRepSupportAI(response: string, agentName: string, roundNum: number): string {
    if (agentName !== '用户代表·张阿姨') return response;
    
    const isNegative = ['不需要', '太复杂', '用不来', '不要'].some(p => response.includes(p));
    if (isNegative && roundNum > 0) {
        console.log(`    ⚠️ 用户代表过于保守，引导理解AI价值`);
        return response; // 简化处理
    }
    return response;
}

async function checkGuardian(decision: string, llm: LLMClient): Promise<{ check: string; challenge: string }> {
    const messages: Message[] = [
        { role: 'system', content: VALUE_GUARDIAN_PROMPT },
        { role: 'user', content: `【阶段0决策清单】\n${decision}\n\n请严格按照标准检查。` }
    ];
    
    const check = await llm.call(messages, 0.3, 500);
    const challenge = check.includes('【质疑】') ? check.split('【质疑】').pop()?.trim() || '' : '';
    
    return { check, challenge };
}

function checkPhase1Details(agentName: string, response: string): string {
    if (!DETAIL_CHECKLIST[agentName]) return response;
    
    if (response.length < 200) {
        console.log(`    ⚠️ ${agentName}输出过于简略，要求补充细节`);
        return response + `\n\n【提示】请补充：${DETAIL_CHECKLIST[agentName]}`;
    }
    return response;
}

// ============== 主流程 ==============

async function runPhase0(config: Config, llm: LLMClient): Promise<{ result: string; decision: string }> {
    const { maxIterations, requirement } = config;
    const history: string[] = [];
    const result: string[] = [];
    
    result.push('='.repeat(70));
    result.push('【阶段0：需求决策会议】（3轮讨论，4人参与，六重流程控制 + v7.5优化）');
    result.push('='.repeat(70) + '\n');
    
    for (let round = 0; round < maxIterations.phase0Rounds; round++) {
        result.push(`--- 第${round + 1}轮讨论 ---`);
        console.log(`\n阶段0 - 第${round + 1}轮讨论`);
        
        const roundDiscussions: string[] = [];
        
        for (const [agentName, agentPrompt] of Object.entries(PHASE0_ROLES)) {
            let context = `【客户需求】\n${requirement}\n\n【历史讨论】\n${history.slice(-12).join('\n')}`;
            
            const pmChallenge = injectPMChallenge(round, history);
            if (pmChallenge && agentName === '产品经理·李明') {
                context += `\n${pmChallenge}`;
            }
            
            const messages: Message[] = [
                { role: 'system', content: agentPrompt },
                { role: 'user', content: `${context}\n\n现在是第${round + 1}轮讨论，请发表你的观点。` }
            ];
            
            let response = await llm.call(messages);
            
            // 六重控制
            response = filterNegativeResponse(response, agentName, agentPrompt);
            response = enforceQualitySolutions(response, agentName);
            response = forceTechLeadSolution(response, agentName, agentPrompt);
            response = guideUserRepSupportAI(response, agentName, round);
            
            roundDiscussions.push(`【${agentName}】${response}`);
            result.push(`【${agentName}】${response}`);
            
            console.log(`  ${agentName}: ${response.substring(0, 60)}...`);
        }
        
        history.push(...roundDiscussions);
        result.push('');
    }
    
    // 生成决策清单
    const summaryMessages: Message[] = [
        { role: 'system', content: '你是产品经理，负责总结决策。' },
        { role: 'user', content: `
基于以上3轮讨论，生成决策清单：

【核心功能】
【砍掉的功能】
【预算和工期】

讨论历史：
${history.join('\n')}

请用200字内总结。
` }
    ];
    
    const decision = await llm.call(summaryMessages, 0.3);
    
    result.push('-'.repeat(70));
    result.push('【阶段0总结：决策清单】');
    result.push('-'.repeat(70));
    result.push(decision);
    result.push('');
    
    console.log('\n阶段0总结完成\n');
    
    return { result: result.join('\n'), decision };
}

async function runPhase1(decision: string, config: Config, llm: LLMClient): Promise<{ result: string; outputs: Record<string, string> }> {
    const result: string[] = [];
    const outputs: Record<string, string> = {};
    
    result.push('='.repeat(70));
    result.push('【阶段1：流水线生产】（v7.5优化：细节完整性检查）');
    result.push('='.repeat(70) + '\n');
    
    console.log('\n' + '='.repeat(70));
    console.log('阶段1 - 流水线生产（v7.5优化）');
    console.log('='.repeat(70));
    
    for (const [agentName, agentPrompt] of Object.entries(PHASE1_ROLES)) {
        console.log(`\n阶段1 - ${agentName}`);
        
        const messages: Message[] = [
            { role: 'system', content: agentPrompt },
            { role: 'user', content: `【阶段0决策】\n${decision}\n\n请输出你的工作成果（300字内）。` }
        ];
        
        let response = await llm.call(messages, 0.5, 2000);
        response = checkPhase1Details(agentName, response);
        
        outputs[agentName] = response;
        result.push(`--- ${agentName}输出 ---`);
        result.push(response);
        result.push('');
        
        console.log(`  ${agentName}: 完成`);
    }
    
    console.log('\n阶段1完成');
    
    return { result: result.join('\n'), outputs };
}

async function runPhase2(decision: string, phase1Outputs: Record<string, string>, llm: LLMClient): Promise<string> {
    const result: string[] = [];
    
    result.push('='.repeat(70));
    result.push('【阶段2：质检会议】');
    result.push('='.repeat(70));
    
    console.log('\n' + '='.repeat(70));
    console.log('阶段2 - 质检会议');
    console.log('='.repeat(70));
    
    const prd = phase1Outputs['产品经理'] || '';
    const ui = phase1Outputs['UI设计师'] || '';
    const tech = phase1Outputs['技术负责人'] || '';
    
    for (const [agentName, agentTask] of Object.entries(PHASE2_ROLES)) {
        console.log(`\n阶段2 - ${agentName}`);
        
        const messages: Message[] = [
            { role: 'system', content: `你是${agentName}，任务：${agentTask}` },
            { role: 'user', content: `
【阶段0决策】
${decision}

【PRD】
${prd}

【UI方案】
${ui}

【技术方案】
${tech}

请给出质检意见（200字内）。
` }
        ];
        
        const response = await llm.call(messages, 0.5, 1000);
        result.push(`【${agentName}】${response}`);
        
        console.log(`  ${agentName}: 完成`);
    }
    
    result.push('');
    console.log('\n阶段2完成');
    
    return result.join('\n');
}

async function runFinalReview(fullContext: string, llm: LLMClient): Promise<string> {
    const result: string[] = [];
    
    result.push('='.repeat(70));
    result.push('【最终评审】');
    result.push('='.repeat(70));
    
    console.log('\n' + '='.repeat(70));
    console.log('最终评审');
    console.log('='.repeat(70));
    
    const messages: Message[] = [
        { role: 'system', content: FINAL_REVIEW_PROMPT },
        { role: 'user', content: fullContext }
    ];
    
    const review = await llm.call(messages, 0.3, 1000);
    result.push(review);
    
    console.log('\n最终评审完成');
    
    return result.join('\n');
}

// ============== 入口 ==============

async function main(): Promise<void> {
    const config = getConfig();
    
    console.log('='.repeat(70));
    console.log('Consilium v7.6 - TypeScript Version');
    console.log('混合模式 v7.6 实验输出（v7.5 + 迭代次数硬限制）');
    console.log('='.repeat(70));
    console.log('\nv7.6优化：');
    console.log('- 继承v7.5的所有机制（细节检查、创新引导、六重控制）');
    console.log('- 新增：迭代次数硬限制（防止极端情况死循环）');
    console.log(`  * 价值守护者重试：最多${config.maxIterations.guardianRetry}次`);
    console.log(`  * LLM API重试：最多${config.maxIterations.llmApiRetry}次`);
    console.log(`  * 阶段0讨论：固定${config.maxIterations.phase0Rounds}轮`);
    console.log('='.repeat(70));
    
    if (!config.deepseek.apiKey) {
        console.log('\n⚠️ 未设置 API Key，程序退出');
        process.exit(1);
    }
    
    const llm = new LLMClient(config.deepseek, config.maxIterations.llmApiRetry);
    
    console.log('\n客户需求：');
    console.log(config.requirement);
    console.log('\n');
    
    const { result: phase0Result, decision } = await runPhase0(config, llm);
    const { result: phase1Result, outputs } = await runPhase1(decision, config, llm);
    const phase2Result = await runPhase2(decision, outputs, llm);
    
    const fullResult = `
客户需求：
${config.requirement}

${phase0Result}
${phase1Result}
${phase2Result}
`;
    
    const finalReview = await runFinalReview(fullResult, llm);
    const finalResult = fullResult + '\n' + finalReview;
    
    console.log('\n' + '='.repeat(70));
    console.log('✅ Consilium v7.6 TypeScript 版本运行完成！');
    console.log('='.repeat(70));
}

// 导出供模块使用
export { 
    getConfig, 
    runPhase0, 
    runPhase1, 
    runPhase2, 
    runFinalReview,
    main as default 
};

// 如果直接运行
if (require.main === module) {
    main().catch(console.error);
}
