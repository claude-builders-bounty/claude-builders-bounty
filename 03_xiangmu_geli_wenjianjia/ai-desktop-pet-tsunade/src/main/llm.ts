/**
 * LLM 客户端模块
 *
 * 支持 OpenAI、Anthropic（兼容 OpenAI 格式 baseURL）、Ollama 三种提供商。
 * 所有密钥通过环境变量或 electron-store 加密存储，绝不写死在代码中。
 * 提供流式与非流式两种对话方式，并可将用户输入映射为纲手的人设动作/心情。
 */

import { OpenAI } from "openai";
import type { LlmConfig, LlmChatRequest, LlmChatResponse, PetAnimation, PetMood } from "../shared/ipc";

/** LLM 提供商枚举 */
export const LLM_PROVIDER = {
  OPENAI: "openai",
  ANTHROPIC: "anthropic",
  OLLAMA: "ollama",
} as const;

/** LLM 调用错误 */
export class LLMError extends Error {
  public readonly provider: string;
  constructor(message: string, provider: string) {
    super(message);
    this.name = "LLMError";
    this.provider = provider;
  }
}

/** OpenAI 客户端单例缓存（按配置键缓存） */
const clientCache = new Map<string, OpenAI>();

function getClientKey(config: LlmConfig): string {
  return `${config.provider}:${config.baseUrl}:${config.model}`;
}

function createClient(config: LlmConfig): OpenAI {
  const key = getClientKey(config);
  let client = clientCache.get(key);
  if (client) return client;

  // OpenAI SDK 兼容任意 OpenAI 风格 baseURL（Ollama、vLLM、LM Studio、Anthropic 兼容层等）
  client = new OpenAI({
    apiKey: config.apiKey || "dummy",
    baseURL: config.baseUrl,
    // 禁用默认重试，由上层控制
    maxRetries: 2,
  });

  clientCache.set(key, client);
  return client;
}

/** 清除客户端缓存（配置变更时调用） */
export function clearLlmClientCache(): void {
  clientCache.clear();
}

/** 将 LLM 回复映射为纲手动作与心情（基于关键词启发式，保持轻量） */
function inferAnimationAndMood(content: string): {
  animation?: PetAnimation;
  mood?: PetMood;
} {
  const lower = content.toLowerCase();
  const result: { animation?: PetAnimation; mood?: PetMood } = {};

  // 饮酒相关
  if (/酒|喝|饮|sake|drink|酒壶/i.test(lower)) {
    result.animation = "drink";
    result.mood = "happy";
  }
  // 赌博
  else if (/赌|赌博|骰子|赌注|gamble|bet/i.test(lower)) {
    result.animation = "gamble";
    result.mood = "normal";
  }
  // 发火/生气
  else if (/怒|发火|生气|气死|火气|angry|mad/i.test(lower)) {
    result.animation = "angry";
    result.mood = "angry";
  }
  // 治愈/医疗
  else if (/治愈|医疗|查克拉|治疗|手术|heal|medical/i.test(lower)) {
    result.animation = "heal";
    result.mood = "normal";
  }
  // 害羞/脸红
  else if (/害羞|脸红|blush|embarrass/i.test(lower)) {
    result.animation = "blush";
    result.mood = "love";
  }
  // 待机/闲聊默认
  else {
    result.animation = "talk";
    result.mood = "normal";
  }

  return result;
}

/** 发送聊天请求（非流式） */
export async function chatCompletion(
  config: LlmConfig,
  request: LlmChatRequest
): Promise<LlmChatResponse> {
  const client = createClient(config);

  try {
    const messages = request.messages.map((m) => ({
      role: m.role as "system" | "user" | "assistant",
      content: m.content,
    }));

    // Anthropic 官方 SDK 走不同路径；此处统一用 OpenAI 兼容 baseURL
    const response = await client.chat.completions.create({
      model: config.model,
      messages,
      temperature: request.temperature ?? config.temperature,
      max_tokens: request.maxTokens ?? config.maxTokens,
      stream: false,
    });

    const content = response.choices[0]?.message?.content ?? "";
    const inferred = inferAnimationAndMood(content);

    return {
      content,
      animation: inferred.animation,
      mood: inferred.mood,
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    throw new LLMError(`LLM 调用失败: ${message}`, config.provider);
  }
}

/** 发送聊天请求（流式，回调每个文本块） */
export async function chatCompletionStream(
  config: LlmConfig,
  request: LlmChatRequest,
  onChunk: (chunk: string) => void
): Promise<LlmChatResponse> {
  const client = createClient(config);

  try {
    const messages = request.messages.map((m) => ({
      role: m.role as "system" | "user" | "assistant",
      content: m.content,
    }));

    const stream = await client.chat.completions.create({
      model: config.model,
      messages,
      temperature: request.temperature ?? config.temperature,
      max_tokens: request.maxTokens ?? config.maxTokens,
      stream: true,
    });

    let fullContent = "";

    for await (const part of stream) {
      const delta = part.choices[0]?.delta?.content ?? "";
      if (delta) {
        fullContent += delta;
        onChunk(delta);
      }
    }

    const inferred = inferAnimationAndMood(fullContent);

    return {
      content: fullContent,
      animation: inferred.animation,
      mood: inferred.mood,
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    throw new LLMError(`LLM 流式调用失败: ${message}`, config.provider);
  }
}

/** 验证 LLM 配置是否完整 */
export function validateLlmConfig(config: LlmConfig): { valid: boolean; error?: string } {
  if (!config.provider) {
    return { valid: false, error: "缺少 LLM 提供商" };
  }
  if (!config.model) {
    return { valid: false, error: "缺少模型名称" };
  }
  if (config.provider !== "ollama" && !config.apiKey) {
    // Ollama 本地通常不需要 API Key
    return { valid: false, error: "缺少 API Key" };
  }
  if (!config.baseUrl) {
    return { valid: false, error: "缺少基础地址" };
  }
  return { valid: true };
}

export type { PetAnimation, PetMood };
