/**
 * GeneralSettings — 常规设置
 *
 * 职责：
 * 1. 展示应用级常规设置：语言、自动启动、点击穿透、始终置顶
 * 2. 通过 zustand store 的 settings/window slice 与 preload API 同步
 * 3. 不可变性：所有变更通过 store actions 完成，不修改入参
 */

import { useCallback } from "react";

import { useSettings, useWindow } from "@/hooks/usePetApi";

/** GeneralSettings 属性 */
export interface GeneralSettingsProps {
  /** 是否显示标题 */
  showTitle?: boolean;
}

/** 常规设置面板 */
export function GeneralSettings({ showTitle = true }: GeneralSettingsProps) {
  const {
    language,
    autoStart,
    setSettings,
  } = useSettings();
  const {
    clickThrough,
    alwaysOnTop,
    setClickThrough,
    setAlwaysOnTop,
  } = useWindow();

  const handleLanguageChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      void setSettings({ language: e.currentTarget.value as "zh-CN" | "en-US" });
    },
    [setSettings]
  );

  const handleAutoStartChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      void setSettings({ autoStart: e.currentTarget.checked });
    },
    [setSettings]
  );

  const handleClickThroughChange = useCallback(() => {
    void setClickThrough(!clickThrough);
  }, [clickThrough, setClickThrough]);

  const handleAlwaysOnTopChange = useCallback(() => {
    void setAlwaysOnTop(!alwaysOnTop);
  }, [alwaysOnTop, setAlwaysOnTop]);

  return (
    <div className="space-y-5">
      {showTitle && (
        <h2 className="text-base font-semibold text-slate-100">常规设置</h2>
      )}

      <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 space-y-4">
        {/* 语言 */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-200">界面语言</p>
            <p className="text-xs text-slate-500">选择应用显示语言</p>
          </div>
          <select
            value={language}
            onChange={handleLanguageChange}
            className="px-3 py-1.5 rounded bg-slate-900 border border-slate-600 text-slate-100 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="zh-CN">中文（简体）</option>
            <option value="en-US">English</option>
          </select>
        </div>

        {/* 自动启动 */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-200">开机自动启动</p>
            <p className="text-xs text-slate-500">登录后自动启动桌宠</p>
          </div>
          <input
            type="checkbox"
            checked={autoStart}
            onChange={handleAutoStartChange}
            className="rounded bg-slate-900 border-slate-600 text-indigo-600 focus:ring-indigo-500"
          />
        </div>

        <div className="pt-2 border-t border-slate-700/50">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">窗口行为</h3>

          {/* 点击穿透 */}
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm text-slate-200">点击穿透</p>
              <p className="text-xs text-slate-500">
                开启后可穿透宠物点击桌面窗口
              </p>
            </div>
            <button
              type="button"
              onClick={handleClickThroughChange}
              className={`rounded-full px-2.5 py-1 text-xs transition ${
                clickThrough
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-700 text-slate-300"
              }`}
            >
              {clickThrough ? "开启" : "关闭"}
            </button>
          </div>

          {/* 始终置顶 */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">始终置顶</p>
              <p className="text-xs text-slate-500">宠物窗口始终保持在最前</p>
            </div>
            <button
              type="button"
              onClick={handleAlwaysOnTopChange}
              className={`rounded-full px-2.5 py-1 text-xs transition ${
                alwaysOnTop
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-700 text-slate-300"
              }`}
            >
              {alwaysOnTop ? "开启" : "关闭"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

GeneralSettings.displayName = "GeneralSettings";
