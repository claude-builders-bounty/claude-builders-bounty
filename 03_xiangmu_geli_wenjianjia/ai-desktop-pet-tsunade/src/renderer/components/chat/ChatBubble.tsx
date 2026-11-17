/**
 * ChatBubble — 单条聊天气泡
 *
 * 职责：
 * 1. 渲染一条聊天消息（用户 / 助手），按 role 区分左右对齐与配色
 * 2. 支持流式内容（isStreaming 时显示打字光标）
 * 3. 显示时间戳，助手气泡可附带动作/心情标识
 * 4. 不可变性：仅读取 props，不修改入参
 */

import type { ChatMessage, PetMood } from "@shared/ipc";

/** ChatBubble 属性 */
export interface ChatBubbleProps {
  /** 消息内容 */
  message: ChatMessage;
  /** 是否为流式中内容（流式时显示打字光标） */
  isStreaming?: boolean;
}

/** 宠物心情到 emoji 的映射 */
const MOOD_EMOJI: Record<PetMood, string> = {
  happy: "😄",
  angry: "😠",
  drunk: "🥴",
  tired: "😴",
  love: "💕",
  normal: "😐",
};

export function ChatBubble({ message, isStreaming = false }: ChatBubbleProps) {
  const isUser = message.role === "user";
  const time = new Date(message.timestamp).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });

  const moodEmoji = message.mood ? MOOD_EMOJI[message.mood] : undefined;

  return (
    <div
      className={`flex ${
        isUser ? "justify-end" : "justify-start"
      } mb-3 animate-fade-in`}
    >
      <div
        className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? "bg-indigo-600 text-white rounded-tr-none"
            : "bg-slate-800 text-slate-200 rounded-tl-none"
        }`}
      >
        {message.content}{isStreaming && <span className="animate-pulse">…</span>}
      </div>

      {!isUser && moodEmoji && (
        <div className="flex items-center gap-1 ml-1 text-xs text-slate-400">
          {moodEmoji && <span>{moodEmoji}</span>}
        </div>
      )}

      <span
        className={`text-[10px] mt-0.5 ${
          isUser ? "ml-auto text-indigo-400" : "text-slate-500"
        }`}
      >
        {time}
      </span>
    </div>
  );
}

ChatBubble.displayName = "ChatBubble";
