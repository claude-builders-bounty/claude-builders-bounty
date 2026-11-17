/**
 * useChatStream — 流式聊天 Hook
 *
 * 职责：
 * 1. 订阅 preload 暴露的 chat:stream 分片，拼接到 zustand store 的 streamBuffer
 * 2. 提供 sendStreamMessage 发送消息并进入流式模式
 * 3. 流结束后重置流式标志与缓冲
 * 4. 不可变性：所有状态变更通过 zustand store actions 完成
 */

import { useCallback, useEffect } from "react";
import type { ChatMessage, PetAnimation, PetMood } from "@shared/ipc";

import { useChat, usePetApi } from "@/hooks/usePetApi";

/** useChatStream 返回类型 */
export interface UseChatStreamReturn {
  /** 当前流式缓冲（未落库的助手回复片段） */
  streamBuffer: string;
  /** 是否正在流式接收中 */
  isStreaming: boolean;
  /** 消息历史 */
  messages: ChatMessage[];
  /** 发送消息并进入流式模式 */
  sendStreamMessage: (content: string) => Promise<void>;
  /** 手动终止当前流式 */
  stopStream: () => void;
  /** 发送普通（非流式）消息 */
  sendMessage: (content: string) => Promise<void>;
  /** 加载历史消息 */
  fetchChatHistory: () => Promise<void>;
  /** 清空历史 */
  clearChatHistory: () => Promise<void>;
}

/** 流式聊天 Hook */
export function useChatStream(): UseChatStreamReturn {
  const {
    messages,
    isStreaming,
    streamBuffer,
    sendMessage: storeSendMessage,
    fetchChatHistory,
    clearChatHistory,
    appendStreamChunk,
    setStreaming,
  } = useChat();

  const { on } = usePetApi();

  // 订阅 chat:stream 分片，拼接到 streamBuffer
  useEffect(() => {
    const unsubscribe = on<{
      content: string;
      done?: boolean;
      animation?: PetAnimation;
      mood?: PetMood;
    }>("chat:stream", (chunk) => {
      if (chunk.done) {
        setStreaming(false);
        appendStreamChunk("");
        return;
      }
      appendStreamChunk(chunk.content ?? "");
    });
    return () => unsubscribe();
  }, [appendStreamChunk, setStreaming, on]);

  const sendStreamMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) {
        console.warn("[useChatStream] 发送内容为空，已忽略");
        return;
      }

      setStreaming(true);
      appendStreamChunk("");

      try {
        await storeSendMessage(content);
      } catch (err) {
        console.error("[useChatStream] 发送消息失败:", err);
        setStreaming(false);
        appendStreamChunk("");
        return;
      }
      // 非流式路径：storeSendMessage 已把完整回复写入 messages，重置流式标志
      setStreaming(false);
      appendStreamChunk("");
    },
    [storeSendMessage, setStreaming, appendStreamChunk]
  );

  const stopStream = useCallback(() => {
    setStreaming(false);
    appendStreamChunk("");
  }, [setStreaming, appendStreamChunk]);

  return {
    streamBuffer,
    isStreaming,
    messages,
    sendStreamMessage,
    stopStream,
    sendMessage: storeSendMessage,
    fetchChatHistory,
    clearChatHistory,
  };
}
