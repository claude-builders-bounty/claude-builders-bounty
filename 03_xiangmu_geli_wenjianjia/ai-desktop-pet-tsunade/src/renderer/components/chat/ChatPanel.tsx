/**
 * ChatPanel — 聊天面板
 *
 * 职责：
 * 1. 渲染消息列表，滚动到底部自动跟随
 * 2. 集成 ChatInput 与 useChatStream，支持流式对话
 * 3. 流式中显示助手气泡（占位），流式结束后替换为完整内容
 * 4. 不可变性：所有状态通过 useChatStream / zustand 管理
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { useChatStream } from "@/hooks/useChatStream";

/** ChatPanel 属性 */
export interface ChatPanelProps {
  /** 是否可见 */
  visible: boolean;
  /** 关闭回调 */
  onClose: () => void;
}

/** 聊天面板 */
export function ChatPanel({ visible, onClose }: ChatPanelProps) {
  const {
    messages,
    isStreaming,
    streamBuffer,
    sendStreamMessage,
    fetchChatHistory,
    clearChatHistory,
  } = useChatStream();

  const endRef = useRef<HTMLDivElement>(null);
  const [userDraft, setUserDraft] = useState("");

  // 面板显示时拉取历史
  useEffect(() => {
    if (visible) {
      void fetchChatHistory();
    }
  }, [visible, fetchChatHistory]);

  // 消息更新时滚动到底部
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamBuffer, isStreaming]);

  const handleSend = useCallback(
    (content: string) => {
      void sendStreamMessage(content);
    },
    [sendStreamMessage]
  );

  if (!visible) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex flex-col bg-slate-950/95 backdrop-blur-sm">
      {/* 标题栏 */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-slate-900/80">
        <h2 className="text-sm font-semibold text-slate-100">与纲手对话</h2>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => void clearChatHistory()}
            className="px-2 py-1 text-xs text-slate-400 hover:text-white transition"
            disabled={isStreaming}
          >
            清空
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-xs text-slate-400 hover:text-white transition"
          >
            关闭
          </button>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-reverse scrollbar-hide">
        {messages.map((msg) => {
          const isLastAssistantStreaming =
            msg.role === "assistant" && isStreaming && streamBuffer;
          return (
            <ChatBubble
              key={msg.id}
              message={msg}
              isStreaming={
                isLastAssistantStreaming && !msg.content ? true : false
              }
            />
          );
        })}
        {isStreaming && streamBuffer && (
          <ChatBubble
            key="streaming-placeholder"
            message={{
              id: "streaming",
              role: "assistant",
              content: streamBuffer,
              timestamp: Date.now(),
            }}
            isStreaming
          />
        )}
        <div ref={endRef} />
      </div>

      {/* 输入区 */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/90 backdrop-blur-md">
        <ChatInput
          value={userDraft}
          onChange={setUserDraft}
          onSend={handleSend}
          disabled={isStreaming}
          placeholder={isStreaming ? "纲手正在回复…" : "跟纲手说句话吧…"}
        />
      </div>
    </div>
  );
}

ChatPanel.displayName = "ChatPanel";
