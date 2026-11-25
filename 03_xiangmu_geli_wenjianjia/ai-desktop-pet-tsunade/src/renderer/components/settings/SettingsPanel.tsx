/**
 * SettingsPanel — 设置面板（容器）
 *
 * 职责：
 * 1. 容器组件，内部包含 GeneralSettings / LlmConfigForm / ReminderManager / MonitorToggle
 * 2. 通过标签页切换各设置子模块
 * 3. 聚合 zustand store 中的 llm / settings 状态
 * 4. 不可变性：标签页状态通过 useState 管理，不修改入参
 */

import { useState } from "react";

import { GeneralSettings } from "./GeneralSettings";
import { LlmConfigForm } from "./LlmConfigForm";
import { ReminderManager } from "./ReminderManager";
import { MonitorToggle } from "./MonitorToggle";
import { useSettings } from "@/hooks/usePetApi";

/** 设置标签页 */
type SettingsTab = "general" | "llm" | "reminder" | "monitor";

/** SettingsPanel 属性 */
export interface SettingsPanelProps {
  /** 是否可见 */
  visible: boolean;
  /** 关闭回调 */
  onClose: () => void;
}

/** 设置面板 */
export function SettingsPanel({ visible, onClose }: SettingsPanelProps) {
  const [tab, setTab] = useState<SettingsTab>("general");
  const { llm, setLlmConfig } = useSettings();

  const tabs: { key: SettingsTab; label: string }[] = [
    { key: "general", label: "常规" },
    { key: "llm", label: "LLM 配置" },
    { key: "reminder", label: "定时提醒" },
    { key: "monitor", label: "系统监控" },
  ];

  if (!visible) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-40 flex flex-col bg-slate-950/95 backdrop-blur-sm">
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-slate-900/80">
        <h2 className="text-sm font-semibold text-slate-100">设置</h2>
        <button
          type="button"
          onClick={onClose}
          className="px-3 py-1.5 text-xs text-slate-400 hover:text-white transition"
        >
          关闭
        </button>
      </div>

      {/* 标签页 */}
      <div className="flex border-b border-slate-800 bg-slate-900/80">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={`px-4 py-3 text-xs font-medium border-b-2 transition ${
              tab === t.key
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                : "border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
        {tab === "general" && (
          <GeneralSettings showTitle={false} />
        )}
        {tab === "llm" && (
          <LlmConfigForm
            config={llm}
            loading={false}
            onSave={(config) => {
              void setLlmConfig(config);
            }}
          />
        )}
        {tab === "reminder" && <ReminderManager visible onClose={() => {}} />}
        {tab === "monitor" && (
          <div className="p-4">
            <p className="text-sm text-slate-200 mb-3">
              系统监控将定期采集 CPU、内存、网速数据，供监控悬浮窗使用。
            </p>
            <MonitorToggle showLabel />
            <p className="mt-2 text-xs text-slate-500">
              当前提供商：{llm?.provider ?? "未配置"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

SettingsPanel.displayName = "SettingsPanel";
