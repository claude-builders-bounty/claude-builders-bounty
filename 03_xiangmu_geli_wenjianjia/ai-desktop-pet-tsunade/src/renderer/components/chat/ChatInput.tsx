/**
 * ChatInput — 聊天输入框
 *
 * 职责：
 * 1. 单行文本输入，回车发送（Shift+回车换行）
 * 2. 可绑定 disabled 状态（流式中禁止重复发送）
 * 3. 通过 onSend 回调将内容交给上层
 * 4. 不可变性：内部受控值由 props 控制，不修改入参
 */

import { useState } from "react";

/** ChatInput 属性 */
export interface ChatInputProps {
  /** 当前输入值（受控） */
  value: string;
  /** 输入值变更回调 */
  onChange: (value: string) => void;
  /** 发送回调 */
  onSend: (content: string) => void;
  /** 是否禁用输入（流式中为 true） */
  disabled?: boolean;
  /** 占位符文本 */
  placeholder?: string;
}

/** 聊天输入框 */
export function ChatInput({
  value,
  onChange,
  onSend,
  disabled = false,
  placeholder = "跟纲手说句话吧…",
}: ChatInputProps) {
  const [localValue, setLocalValue] = useState(value);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const next = e.currentTarget.value;
    setLocalValue(next);
    onChange(next);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>): void => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const trimmed = localValue.trim();
      if (trimmed && !disabled) {
        onSend(trimmed);
        setLocalValue("");
        onChange("");
      }
    }
  };

  return (
    <div className="flex items-end gap-2 pt-2">
      <textarea
        value={localValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        rows={1}
        className="flex-1 min-h-[36px] max-h-[120px] px-4 py-2.5 rounded-xl bg-slate-800/60 border border-slate-700 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition resize-none scrollbar-hide"
        spellCheck={false}
        autoComplete="off"
      />
      <button
        type="button"
        onClick={() => {
          const trimmed = localValue.trim();
          if (trimmed && !disabled) {
            onSend(trimmed);
            setLocalValue("");
            onChange("");
          }
        }}
        disabled={disabled || !localValue.trim()}
        className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
      >
        发送
      </button>
    </div>
  );
}

ChatInput.displayName = "ChatInput";
