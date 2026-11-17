/**
 * MonitorToggle — 系统监控开关
 *
 * 职责：
 * 1. 展示监控当前开启/关闭状态
 * 2. 点击切换：调用 startMonitor / stopMonitor
 * 3. 状态通过 zustand system slice 与 preload API 同步
 * 4. 不可变性：不修改入参，所有状态变更通过 store actions
 */

import { useCallback } from "react";

import { useMonitor } from "@/hooks/usePetApi";

/** MonitorToggle 属性 */
export interface MonitorToggleProps {
  /** 是否显示文字标签 */
  showLabel?: boolean;
}

/** 系统监控开关 */
export function MonitorToggle({ showLabel = true }: MonitorToggleProps) {
  const { monitorActive, startMonitor, stopMonitor } = useMonitor();

  const handleToggle = useCallback(() => {
    if (monitorActive) {
      void stopMonitor();
    } else {
      void startMonitor();
    }
  }, [monitorActive, startMonitor, stopMonitor]);

  return (
    <button
      type="button"
      onClick={handleToggle}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
        monitorActive
          ? "bg-emerald-900/30 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-900/50"
          : "bg-slate-800 border border-slate-600 text-slate-300 hover:bg-slate-700"
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full ${
          monitorActive ? "bg-emerald-400 animate-pulse" : "bg-slate-500"
        }`}
        aria-hidden="true"
      />
      {showLabel && (
        <span>{monitorActive ? "监控已开启" : "监控已关闭"}</span>
      )}
    </button>
  );
}

MonitorToggle.displayName = "MonitorToggle";
