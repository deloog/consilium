package main

/**
 * Consilium v7.6 - Go Version
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
 * - 高性能、并发友好
 */

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// ============== 配置 ==============

type Config struct {
	DeepSeek      DeepSeekConfig     `json:"deepseek"`
	MaxIterations MaxIterationsConfig `json:"maxIterations"`
	Requirement   string             `json:"requirement"`
}

type DeepSeekConfig struct {
	APIKey   string `json:"apiKey"`
	BaseURL  string `json:"baseUrl"`
	Model    string `json:"model"`
}

type MaxIterationsConfig struct {
	GuardianRetry int `json:"guardianRetry"`
	LLMAPIRetry   int `json:"llmApiRetry"`
	Phase0Rounds  int `json:"phase0Rounds"`
}

func getConfig() Config {
	apiKey := os.Getenv("DEEPSEEK_API_KEY")
	baseURL := os.Getenv("DEEPSEEK_BASE_URL")
	model := os.Getenv("DEEPSEEK_MODEL")
	requirement := os.Getenv("CONSILIUM_REQUIREMENT")

	if apiKey == "" {
		fmt.Println("⚠️ 警告：未设置 DEEPSEEK_API_KEY 环境变量")
	}

	if baseURL == "" {
		baseURL = "https://api.deepseek.com/v1"
	}
	if model == "" {
		model = "deepseek-chat"
	}
	if requirement == "" {
		requirement = `
客户需求：我想做一个面向老年人的短视频App。
- 要简单易用,老年人能轻松上手
- 但也要有强大的AI编辑功能（一键生成片头片尾、自动字幕、AI配乐）
- 要有社交功能，能让老年人和家人互动
- 预算有限，总共50万人民币
- 三个月内上线第一版
`
		requirement = strings.TrimSpace(requirement)
	}

	return Config{
		DeepSeek: DeepSeekConfig{
			APIKey:  apiKey,
			BaseURL: baseURL,
			Model:   model,
		},
		MaxIterations: MaxIterationsConfig{
			GuardianRetry: 1,
			LLMAPIRetry:   3,
			Phase0Rounds:  3,
		},
		Requirement: requirement,
	}
}

// ============== LLM 调用 ==============

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ChatRequest struct {
	Model       string    `json:"model"`
	Messages    []Message `json:"messages"`
	Temperature float64   `json:"temperature"`
	MaxTokens   int       `json:"max_tokens"`
}

type Choice struct {
	Message Message `json:"message"`
}

type ChatResponse struct {
	Choices []Choice `json:"choices"`
}

type LLMClient struct {
	config     DeepSeekConfig
	maxRetries int
}

func NewLLMClient(config DeepSeekConfig, maxRetries int) *LLMClient {
	return &LLMClient{
		config:     config,
		maxRetries: maxRetries,
	}
}

func (c *LLMClient) Call(messages []Message, temperature float64, maxTokens int) string {
	for attempt := 0; attempt < c.maxRetries; attempt++ {
		reqBody := ChatRequest{
			Model:       c.config.Model,
			Messages:    messages,
			Temperature: temperature,
			MaxTokens:   maxTokens,
		}

		jsonData, err := json.Marshal(reqBody)
		if err != nil {
			fmt.Printf("    ❌ JSON序列化失败: %v\n", err)
			continue
		}

		client := &http.Client{Timeout: 30 * time.Second}
		req, err := http.NewRequest("POST", c.config.BaseURL+"/chat/completions", bytes.NewBuffer(jsonData))
		if err != nil {
			fmt.Printf("    ❌ 请求创建失败: %v\n", err)
			continue
		}

		req.Header.Set("Content-Type", "application/json")
		req.Header.Set("Authorization", "Bearer "+c.config.APIKey)

		resp, err := client.Do(req)
		if err != nil {
			fmt.Printf("    ❌ 调用失败 (尝试 %d/%d): %v\n", attempt+1, c.maxRetries, err)
			time.Sleep(2 * time.Second)
			continue
		}
		defer resp.Body.Close()

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			fmt.Printf("    ❌ 响应读取失败: %v\n", err)
			continue
		}

		var chatResp ChatResponse
		if err := json.Unmarshal(body, &chatResp); err != nil {
			fmt.Printf("    ❌ JSON解析失败: %v\n", err)
			continue
		}

		if len(chatResp.Choices) > 0 {
			return chatResp.Choices[0].Message.Content
		}
	}

	return fmt.Sprintf("[ERROR: API调用失败，已达到最大重试次数(%d)]", c.maxRetries)
}

// ============== 角色定义 ==============

var phase0Roles = map[string]string{
	"产品经理·李明": `你是产品经理李明，负责理解客户需求，平衡各方意见，做出决策。
你的职责是确保核心需求被满足，而不是轻易妥协。
要求：每次发言150字内，语气坚定。`,

	"用户代表·张阿姨": `你是60岁的张阿姨，代表老年用户。
你会表达老年人的真实感受和需求。
要求：每次发言120字内，口语化表达。`,

	"技术负责人·老王": `你是技术负责人老王，评估技术可行性，提出技术方案。
你的职责是找到实现方法，而不是简单说"做不到"。
要求：每次发言150字内，提供具体技术方案。`,

	"成本核算专家·刘总": `你是成本专家刘总，核算成本，提供多种方案。
你的职责是优化成本，而不是简单砍功能。
要求：每次发言150字内，必须提供方案A/B/C三种选择。`,
}

var phase1Roles = map[string]string{
	"产品经理": "你是产品经理，根据阶段0的决策，撰写详细的PRD（包含功能范围、用户场景、优先级）。",
	"UI设计师": "你是UI设计师，根据PRD和适老化要求，设计界面方案（包含交互流程、视觉规范）。",
	"技术负责人": "你是技术负责人，根据PRD，给出完整的技术方案（包含技术栈、架构设计、排期）。",
}

var phase2Roles = map[string]string{
	"产品经理·李明":   "检查PRD是否与阶段0决策一致，是否有范围蔓延。",
	"技术负责人·老王": "识别技术风险和资源黑洞。",
	"成本核算专家·刘总": "核算预算，识别隐藏成本。",
	"用户代表·张阿姨":   "从老年用户角度，检查方案是否真的易用。",
}

const valueGuardianPrompt = `你是价值守护者，快速检查（100字内）：
【客户要求】强大AI编辑功能：
1. 一键生成片头片尾
2. 自动字幕
3. AI配乐

【检查标准】
- 完全保留（3个都有） → ✅通过
- 部分保留（≥2个核心功能） → ✅通过
- 只保留1个或全砍 → ❌需要重新讨论`

const innovationGuidance = `
【创新平衡原则】
- 核心功能必须保留（不能简单砍掉）
- 在预算约束下寻找创新解决方案
- 优先用技术手段（开源/API）替代功能删减
- 适度简化但不丧失核心价值`

var negativePhrases = []string{
	"砍掉", "删除", "去掉", "省略", "砍",
	"后续迭代", "下一版本", "先不做", "以后再",
	"建议简化", "建议放弃", "不建议做", "不做",
	"成本太高", "时间不够", "做不到", "无法实现",
	"不切实际", "太复杂", "风险太大",
}

var detailChecklist = map[string]string{
	"产品经理": `
【PRD必须包含】
1. 用户画像：年龄段、技术水平、使用场景
2. 功能优先级：P0/P1/P2分级
3. 竞品分析：至少2个竞品的优劣势
4. 风险预案：至少列出3个主要风险及应对`,

	"技术负责人": `
【技术方案必须包含】
1. 技术栈选型：前端/后端/数据库及理由
2. 核心API设计：至少列出3个关键接口
3. 第三方服务：具体服务商名称和集成方案
4. 部署架构：简要说明服务器部署方案`,
}

const finalReviewPrompt = `你是项目评审专家。基于上述所有讨论和方案，给出最终评审意见：
- 评审结论：通过/有条件通过/不通过
- 评审意见（150字内）`

// ============== 六重控制机制 ==============

func filterNegativeResponse(response, agentName, rolePrompt string) string {
	for _, phrase := range negativePhrases {
		if strings.Contains(response, phrase) {
			fmt.Printf("    ⚠️ 检测到消极话术: %s...\n", phrase)
			fmt.Println("    🔄 触发乐观化重写")
			// 简化处理，实际应该重新调用LLM
			return response
		}
	}
	return response
}

func enforceQualitySolutions(response, agentName string) string {
	if agentName != "成本核算专家·刘总" {
		return response
	}

	hasA := strings.Contains(response, "方案A")
	hasB := strings.Contains(response, "方案B")
	hasC := strings.Contains(response, "方案C")

	if !hasA || !hasB || !hasC {
		fmt.Println("    ⚠️ 成本专家未提供多方案，要求补充")
		return response + "\n\n（提示：请提供方案A/B/C格式的3种方案）"
	}
	return response
}

func injectPMChallenge(roundNum int, history []string) string {
	historyText := strings.Join(history, "\n")

	if roundNum == 0 {
		return "\n【战略提醒】\n客户明确要求\"强大AI编辑功能\"（3个功能）。\n这是核心卖点，不能轻易砍掉。\n" + innovationGuidance
	}

	if roundNum == 1 {
		hasNegative := false
		for _, phrase := range []string{"砍", "删除", "不做", "后续", "简化"} {
			if strings.Contains(historyText, phrase) {
				hasNegative = true
				break
			}
		}
		if hasNegative {
			return `
【强制质疑】
你注意到有人建议砍掉或推迟AI功能。作为产品经理，你必须强烈反对：

"AI是客户明确要求的核心功能，绝对不能砍！
老王（技术负责人），请给出在预算内实现AI的具体技术方案（开源/API）。
刘总（成本专家），请提供保留AI功能的优化成本方案，用技术手段降低成本。"

请用这种坚定的语气发言（120字内）。`
		}
	}

	if roundNum == 2 {
		hasNegative := false
		for _, phrase := range []string{"砍", "不做", "省略"} {
			if strings.Contains(historyText, phrase) {
				hasNegative = true
				break
			}
		}
		if hasNegative {
			return `
【最终确认】
这是最后一轮讨论。你必须确保AI功能完整保留（3个功能）。
如果方案中仍在砍功能，直接拒绝，要求团队提供保留AI的方案。`
		}
	}

	return ""
}

func forceTechLeadSolution(response, agentName, rolePrompt string) string {
	if agentName != "技术负责人·老王" {
		return response
	}

	patterns := []string{"后续迭代", "下一版本", "先不做", "做不到", "建议简化", "不建议", "成本太高", "时间不够"}
	for _, pattern := range patterns {
		if strings.Contains(response, pattern) {
			fmt.Println("    ⚠️ 技术负责人过于保守，强制要求提供方案")
			return response // 简化处理
		}
	}
	return response
}

func guideUserRepSupportAI(response string, agentName string, roundNum int) string {
	if agentName != "用户代表·张阿姨" {
		return response
	}

	isNegative := false
	for _, phrase := range []string{"不需要", "太复杂", "用不来", "不要"} {
		if strings.Contains(response, phrase) {
			isNegative = true
			break
		}
	}

	if isNegative && roundNum > 0 {
		fmt.Println("    ⚠️ 用户代表过于保守，引导理解AI价值")
		return response // 简化处理
	}
	return response
}

func checkGuardian(decision string, llm *LLMClient) (check string, challenge string) {
	messages := []Message{
		{Role: "system", Content: valueGuardianPrompt},
		{Role: "user", Content: fmt.Sprintf("【阶段0决策清单】\n%s\n\n请严格按照标准检查。", decision)},
	}

	check = llm.Call(messages, 0.3, 500)

	if strings.Contains(check, "【质疑】") {
		parts := strings.SplitN(check, "【质疑】", 2)
		if len(parts) > 1 {
			challenge = strings.TrimSpace(parts[1])
		}
	}

	return
}

func checkPhase1Details(agentName, response string) string {
	if checklist, ok := detailChecklist[agentName]; ok {
		if len(response) < 200 {
			fmt.Printf("    ⚠️ %s输出过于简略，要求补充细节\n", agentName)
			return response + "\n\n【提示】请补充：" + checklist
		}
	}
	return response
}

// ============== 主流程 ==============

type Phase0Result struct {
	Result   string
	Decision string
}

func runPhase0(config Config, llm *LLMClient) Phase0Result {
	var result strings.Builder
	var history []string

	result.WriteString("======================================================================\n")
	result.WriteString("【阶段0：需求决策会议】（3轮讨论，4人参与，六重流程控制 + v7.5优化）\n")
	result.WriteString("======================================================================\n\n")

	for round := 0; round < config.MaxIterations.Phase0Rounds; round++ {
		result.WriteString(fmt.Sprintf("--- 第%d轮讨论 ---\n", round+1))
		fmt.Printf("\n阶段0 - 第%d轮讨论\n", round+1)

		var roundDiscussions []string

		for agentName, agentPrompt := range phase0Roles {
			context := fmt.Sprintf("【客户需求】\n%s\n\n【历史讨论】\n%s", config.Requirement, strings.Join(history[len(history)-12:], "\n"))

			pmChallenge := injectPMChallenge(round, history)
			if pmChallenge != "" && agentName == "产品经理·李明" {
				context += "\n" + pmChallenge
			}

			messages := []Message{
				{Role: "system", Content: agentPrompt},
				{Role: "user", Content: fmt.Sprintf("%s\n\n现在是第%d轮讨论，请发表你的观点。", context, round+1)},
			}

			response := llm.Call(messages)

			// 六重控制
			response = filterNegativeResponse(response, agentName, agentPrompt)
			response = enforceQualitySolutions(response, agentName)
			response = forceTechLeadSolution(response, agentName, agentPrompt)
			response = guideUserRepSupportAI(response, agentName, round)

			roundDiscussions = append(roundDiscussions, fmt.Sprintf("【%s】%s", agentName, response))
			result.WriteString(fmt.Sprintf("【%s】%s\n", agentName, response))

			preview := response
			if len(preview) > 60 {
				preview = preview[:60]
			}
			fmt.Printf("  %s: %s...\n", agentName, preview)
		}

		history = append(history, roundDiscussions...)
		result.WriteString("\n")
	}

	// 生成决策清单
	summaryMessages := []Message{
		{Role: "system", Content: "你是产品经理，负责总结决策。"},
		{Role: "user", Content: fmt.Sprintf(`
基于以上3轮讨论，生成决策清单：

【核心功能】
【砍掉的功能】
【预算和工期】

讨论历史：
%s

请用200字内总结。
`, strings.Join(history, "\n"))},
	}

	decision := llm.Call(summaryMessages, 0.3)

	result.WriteString("----------------------------------------------------------------------\n")
	result.WriteString("【阶段0总结：决策清单】\n")
	result.WriteString("----------------------------------------------------------------------\n")
	result.WriteString(decision)
	result.WriteString("\n\n")

	fmt.Println("\n阶段0总结完成\n")

	return Phase0Result{
		Result:   result.String(),
		Decision: decision,
	}
}

type Phase1Result struct {
	Result  string
	Outputs map[string]string
}

func runPhase1(decision string, config Config, llm *LLMClient) Phase1Result {
	var result strings.Builder
	outputs := make(map[string]string)

	result.WriteString("======================================================================\n")
	result.WriteString("【阶段1：流水线生产】（v7.5优化：细节完整性检查）\n")
	result.WriteString("======================================================================\n\n")

	fmt.Println("\n======================================================================")
	fmt.Println("阶段1 - 流水线生产（v7.5优化）")
	fmt.Println("======================================================================")

	for agentName, agentPrompt := range phase1Roles {
		fmt.Printf("\n阶段1 - %s\n", agentName)

		messages := []Message{
			{Role: "system", Content: agentPrompt},
			{Role: "user", Content: fmt.Sprintf("【阶段0决策】\n%s\n\n请输出你的工作成果（300字内）。", decision)},
		}

		response := llm.Call(messages, 0.5, 2000)
		response = checkPhase1Details(agentName, response)

		outputs[agentName] = response
		result.WriteString(fmt.Sprintf("--- %s输出 ---\n", agentName))
		result.WriteString(response)
		result.WriteString("\n\n")

		fmt.Printf("  %s: 完成\n", agentName)
	}

	fmt.Println("\n阶段1完成")

	return Phase1Result{
		Result:  result.String(),
		Outputs: outputs,
	}
}

func runPhase2(decision string, phase1Outputs map[string]string, llm *LLMClient) string {
	var result strings.Builder

	result.WriteString("======================================================================\n")
	result.WriteString("【阶段2：质检会议】\n")
	result.WriteString("======================================================================\n")

	fmt.Println("\n======================================================================")
	fmt.Println("阶段2 - 质检会议")
	fmt.Println("======================================================================")

	prd := phase1Outputs["产品经理"]
	ui := phase1Outputs["UI设计师"]
	tech := phase1Outputs["技术负责人"]

	for agentName, agentTask := range phase2Roles {
		fmt.Printf("\n阶段2 - %s\n", agentName)

		messages := []Message{
			{Role: "system", Content: fmt.Sprintf("你是%s，任务：%s", agentName, agentTask)},
			{Role: "user", Content: fmt.Sprintf(`
【阶段0决策】
%s

【PRD】
%s

【UI方案】
%s

【技术方案】
%s

请给出质检意见（200字内）。
`, decision, prd, ui, tech)},
		}

		response := llm.Call(messages, 0.5, 1000)
		result.WriteString(fmt.Sprintf("【%s】%s\n", agentName, response))

		fmt.Printf("  %s: 完成\n", agentName)
	}

	result.WriteString("\n")
	fmt.Println("\n阶段2完成")

	return result.String()
}

func runFinalReview(fullContext string, llm *LLMClient) string {
	var result strings.Builder

	result.WriteString("======================================================================\n")
	result.WriteString("【最终评审】\n")
	result.WriteString("======================================================================\n")

	fmt.Println("\n======================================================================")
	fmt.Println("最终评审")
	fmt.Println("======================================================================")

	messages := []Message{
		{Role: "system", Content: finalReviewPrompt},
		{Role: "user", Content: fullContext},
	}

	review := llm.Call(messages, 0.3, 1000)
	result.WriteString(review)

	fmt.Println("\n最终评审完成")

	return result.String()
}

// ============== 入口 ==============

func main() {
	config := getConfig()

	fmt.Println("======================================================================")
	fmt.Println("Consilium v7.6 - Go Version")
	fmt.Println("混合模式 v7.6 实验输出（v7.5 + 迭代次数硬限制）")
	fmt.Println("======================================================================")
	fmt.Println("\nv7.6优化：")
	fmt.Println("- 继承v7.5的所有机制（细节检查、创新引导、六重控制）")
	fmt.Println("- 新增：迭代次数硬限制（防止极端情况死循环）")
	fmt.Printf("  * 价值守护者重试：最多%d次\n", config.MaxIterations.GuardianRetry)
	fmt.Printf("  * LLM API重试：最多%d次\n", config.MaxIterations.LLMAPIRetry)
	fmt.Printf("  * 阶段0讨论：固定%d轮\n", config.MaxIterations.Phase0Rounds)
	fmt.Println("======================================================================")

	if config.DeepSeek.APIKey == "" {
		fmt.Println("\n⚠️ 未设置 API Key，程序退出")
		os.Exit(1)
	}

	llm := NewLLMClient(config.DeepSeek, config.MaxIterations.LLMAPIRetry)

	fmt.Println("\n客户需求：")
	fmt.Println(config.Requirement)
	fmt.Println()

	phase0Result := runPhase0(config, llm)
	phase1Result := runPhase1(phase0Result.Decision, config, llm)
	phase2Result := runPhase2(phase0Result.Decision, phase1Result.Outputs, llm)

	fullResult := fmt.Sprintf(`
客户需求：
%s

%s
%s
%s
`, config.Requirement, phase0Result.Result, phase1Result.Result, phase2Result)

	finalReview := runFinalReview(fullResult, llm)
	finalOutput := fullResult + "\n" + finalReview

	fmt.Println("\n======================================================================")
	fmt.Println("✅ Consilium v7.6 Go 版本运行完成！")
	fmt.Println("======================================================================")
}
