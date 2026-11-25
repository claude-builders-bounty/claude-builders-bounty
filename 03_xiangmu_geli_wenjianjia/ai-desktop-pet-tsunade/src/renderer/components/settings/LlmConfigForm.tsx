/**
 * LlmConfigForm — LLM 配置表单
 *
 * 职责：
 * 1. 渲染 LLM 提供商、API Key、Base URL、模型名、温度、最大 Token、系统提示词等字段
 * 2. 受控表单，变更时通过 setLlmConfig 同步到 zustand + preload API
 * 3. 提供“保存”按钮，点击后将全部字段一次性写入
 * 4. 不可变性：表单状态通过 useState 管理，提交时构造新对象，不修改入参
 */

import { useCallback, useState } from "react";
import type { LlmConfig, LlmProvider } from "@shared/ipc";

import { useSettings } from "@/hooks/usePetApi";

/** LlmConfigForm 属性 */
export interface LlmConfigFormProps {
  /** 初始配置（可选，未提供时使用空配置） */
  config?: LlmConfig | null;
  /** 保存回调，传入新的 LlmConfig */
  onSave: (config: LlmConfig) => void;
  /** 是否加载中（加载中禁用表单） */
  loading?: boolean;
}

/** LLM 提供商选项 */
const PROVIDER_OPTIONS: { value: LlmProvider; label: string }[] = [
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
  { value: "ollama", label: "Ollama（本地）" },
];

/** 默认 LLM 配置 */
const DEFAULT_LLM_CONFIG: LlmConfig = {
  provider: "openai",
  apiKey: "",
  baseUrl: "https://api.openai.com/v1",
  model: "gpt-4o-mini",
  temperature: 0.8,
  maxTokens: 1000,
  systemPrompt: "",
};

/** LLM 配置表单 */
export function LlmConfigForm({
  config: initialConfig,
  onSave,
  loading = false,
}: LlmConfigFormProps) {
  const { setLlmConfig } = useSettings();

  const [form, setForm] = useState<LlmConfig>(() => ({
    ...DEFAULT_LLM_CONFIG,
    ...initialConfig,
  }));

  const handleInputChange = useCallback(
    (field: keyof LlmConfig) => (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.currentTarget.value }));
    },
    []
  );

  const handleSelectChange = useCallback(
    (field: keyof LlmConfig) => (value: string) => {
      setForm((prev) => ({ ...prev, [field]: value as LlmConfig[keyof LlmConfig] }));
    },
    []
  );

  const handleNumberChange = useCallback(
    (field: "temperature" | "maxTokens") => (
      e: React.ChangeEvent<HTMLInputElement>
    ) => {
      setForm((prev) => ({ ...prev, [field]: Number(e.currentTarget.value) }));
    },
    []
  );

  const handleTextareaChange = useCallback(
    (field: keyof LlmConfig) => (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.currentTarget.value }));
    },
    []
  );

  const handleSave = useCallback(() => {
    onSave(form);
    void setLlmConfig(form);
  }, [form, onSave, setLlmConfig]);

  return (
    <div className="space-y-4">
      <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
        <h3 className="text-sm font-semibold text-slate-100 mb-3">LLM 提供商配置</h3>

        {/* 提供商 */}
        <div className="mb-3">
          <label className="block text-xs text-slate-400 mb-1">提供商</label>
          <select
            value={form.provider}
            onChange={(e) =>
              handleSelectChange("provider")(e.currentTarget.value)
            }
            disabled={loading}
            className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {PROVIDER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* API Key */}
        <div className="mb-3">
          <label className="block text-xs text-slate-400 mb-1">API Key</label>
          <input
            type="password"
            value={form.apiKey}
            onChange={handleInputChange("apiKey")}
            disabled={loading}
            placeholder="sk-..."
            className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Base URL */}
        <div className="mb-3">
          <label className="block text-xs text-slate-400 mb-1">Base URL</label>
          <input
            type="url"
            value={form.baseUrl}
            onChange={handleInputChange("baseUrl")}
            disabled={loading}
            placeholder="https://api.openai.com/v1"
            className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* 模型名 */}
        <div className="mb-3">
          <label className="block text-xs text-slate-400 mb-1">模型名称</label>
          <input
            type="text"
            value={form.model}
            onChange={handleInputChange("model")}
            disabled={loading}
            placeholder="gpt-4o-mini"
            className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* 温度 */}
        <div className="mb-3">
          <label className="block text-xs text-slate-400 mb-1">
            温度（Temperature）
          </label>
          <input
            type="number"
            min="0"
            max="2"
            step="0.1"
            value={form.temperature}
            onChange={handleNumberChange("temperature")}
            disabled={loading}
            className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* 最大 Token */}
        <div className="mb-3">
          <label className="block text-xs text-slate-400 mb-1">最大 Token</label>
          <input
            type="number"
            min="1"
            step="1"
            value={form.maxTokens}
            onChange={handleNumberChange("maxTokens")}
            disabled={loading}
            className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* 系统提示词 */}
        <div className="mb-3">
          <label className="block text-xs text-slate-400 mb-1">系统提示词</label>
          <textarea
            value={form.systemPrompt}
            onChange={handleTextareaChange("systemPrompt")}
            disabled={loading}
            rows={3}
            placeholder="设定助手的人设与行为规范…"
            className="w-full px-3 py-2 rounded bg-slate-900 border border-slate-600 text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
          />
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleSave}
          disabled={loading}
          className="px-5 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          保存配置
        </button>
      </div>
    </div>
  );
}

LlmConfigForm.displayName = "LlmConfigForm";
