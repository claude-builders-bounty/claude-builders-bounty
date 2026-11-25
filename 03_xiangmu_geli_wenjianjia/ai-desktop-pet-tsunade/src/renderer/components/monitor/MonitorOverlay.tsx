import { useCallback, useEffect, useRef, useState } from "react";
import type { SystemStats } from "@shared/ipc";
import { useMonitor, usePetApi } from "@/hooks/usePetApi";

/** 本地持久化键 */
const STORAGE_KEY = "tsunade-monitor-overlay";

/** 默认位置（左上角偏移，避免被宠物/窗口边缘遮挡） */
const DEFAULT_POS = { x: 20, y: 20 };

/** 每条网速项的显示文本 */
function formatNet(bytesPerSec: number): string {
  if (bytesPerSec < 1024) {
    return `${bytesPerSec.toFixed(0)} B/s`;
  }
  const kb = bytesPerSec / 1024;
  return `${kb.toFixed(1)} KB/s`;
}

/** 内存显示：used MB + percent */
function formatMemory(used: number, percent: number): string {
  const mb = used / (1024 * 1024);
  return `${mb.toFixed(1)} MB / ${percent.toFixed(1)}%`;
}

type Mode = "compact" | "detail";

export interface MonitorOverlayProps {
  /** 是否可见（由上层/右键菜单控制） */
  visible: boolean;
  /** 点击关闭按钮时回调（仅隐藏，不停止监控） */
  onClose: () => void;
  /** 点击模式切换时回调（可选，内部默认自行切换） */
  onToggleMode?: () => void;
}

/**
 * MonitorOverlay — 系统监控悬浮窗
 *
 * 展示 CPU、内存、网速实时数据，支持紧凑/详细两种模式、拖拽移动、
 * 位置本地记忆、毛玻璃深色主题。关闭按钮仅隐藏面板，不停止后台监控。
 */
export function MonitorOverlay({
  visible,
  onClose,
  onToggleMode,
}: MonitorOverlayProps) {
  const { stats, monitorActive, startMonitor, setStats } = useMonitor();
  const { on } = usePetApi();
  const [mode, setMode] = useState<Mode>("compact");
  const [pos, setPos] = useState({ x: DEFAULT_POS.x, y: DEFAULT_POS.y });
  const [dragging, setDragging] = useState(false);
  const startRef = useRef({ clientX: 0, clientY: 0, x: 0, y: 0 });

  // 读取位置记忆
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (
          typeof parsed.x === "number" &&
          typeof parsed.y === "number" &&
          Number.isFinite(parsed.x) &&
          Number.isFinite(parsed.y)
        ) {
          setPos({ x: parsed.x, y: parsed.y });
        }
      }
    } catch {
      // localStorage 不可用时使用默认位置，静默忽略
    }
  }, []);

  // 显示时启动监控并订阅实时数据；隐藏时取消订阅（监控本身保持运行）
  useEffect(() => {
    if (!visible) return undefined;

    const start = async () => {
      if (!monitorActive) {
        await startMonitor().catch((err: unknown) => {
          console.error("[MonitorOverlay] 启动监控失败:", err);
        });
      }
    };
    void start();

    const unsubscribe = on<SystemStats>("monitor:stats", (s: SystemStats) => {
      setStats(s);
    });

    return () => {
      unsubscribe();
    };
  }, [visible, monitorActive, startMonitor, setStats, on]);

  // 持久化拖拽后的位置
  const persistPosition = useCallback(
    (x: number, y: number) => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ x, y }));
      } catch {
        // localStorage 不可用时忽略
      }
    },
    []
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // 排除关闭按钮与模式切换按钮上的点击，避免误触发拖拽
      if ((e.target as HTMLElement).closest("button")) {
        return;
      }
      e.preventDefault();
      setDragging(true);
      startRef.current = {
        clientX: e.clientX,
        clientY: e.clientY,
        x: pos.x,
        y: pos.y,
      };
    },
    [pos]
  );

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!dragging) return;
      const dx = e.clientX - startRef.current.clientX;
      const dy = e.clientY - startRef.current.clientY;
      setPos({ x: startRef.current.x + dx, y: startRef.current.y + dy });
    },
    [dragging]
  );

  const handleMouseUp = useCallback(() => {
    if (!dragging) return;
    setDragging(false);
    persistPosition(pos.x, pos.y);
  }, [dragging, pos, persistPosition]);

  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [handleMouseMove, handleMouseUp]);

  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  const handleToggleMode = useCallback(() => {
    setMode((prev) => (prev === "compact" ? "detail" : "compact"));
    onToggleMode?.();
  }, [onToggleMode]);

  if (!visible) {
    return null;
  }

  const cpu = stats?.cpu ?? 0;
  const mem = stats?.memory;
  const net = stats?.network;

  return (
    <div
      className="fixed z-50"
      style={{ left: pos.x, top: pos.y }}
      onMouseDown={handleMouseDown}
      role="region"
      aria-label="系统监控悬浮窗"
    >
      {/* 标题栏：拖拽区域 + 关闭 + 切换模式 */}
      <div
        className="flex items-center justify-between gap-2 px-2.5 py-1.5 bg-slate-800/60 backdrop-blur-sm rounded-t-xl border-b border-slate-700/40 select-none"
        onMouseDown={handleMouseDown}
      >
        <span className="text-xs font-semibold text-slate-300">系统监控</span>
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={handleToggleMode}
            className="flex -m-1.5 items-center gap-1 px-1.5 py-1 rounded hover:bg-slate-700 transition text-xs text-slate-400 hover:text-white"
            aria-label="切换显示模式"
            title={mode === "compact" ? "切换到详细模式" : "切换到紧凑模式"}
          >
            {mode === "compact" ? "详细" : "紧凑"}
          </button>
          <button
            type="button"
            onClick={handleClose}
            className="flex -m-1.5 items-center gap-1 px-1.5 py-1 rounded hover:bg-slate-700 transition text-xs text-slate-400 hover:text-white"
            aria-label="关闭监控悬浮窗"
            title="关闭（监控将在后台继续运行）"
          >
            关闭
          </button>
        </div>
      </div>

      {/* 内容区：毛玻璃背景，暗色主题 */}
      <div
        className="px-2.5 pb-2.5 pt-1 bg-slate-900/80 backdrop-blur-md border border-slate-700/50 rounded-b-xl shadow-2xl"
      >
        {mode === "compact" ? (
          // 紧凑模式：单行
          <div className="flex items-center gap-3 text-xs text-slate-200">
            <span className="font-mono text-slate-400">CPU</span>
            <span className="font-mono text-emerald-400">{cpu.toFixed(1)}%</span>
            <span className="w-px h-3 bg-slate-600 mx-1"></span>
            <span className="font-mono text-slate-400">内存</span>
            <span className="font-mono text-emerald-400">
              {mem ? formatMemory(mem.used, mem.percent) : "—"}
            </span>
            <span className="w-px h-3 bg-slate-600 mx-1"></span>
            <span className="font-mono text-slate-400">↑</span>
            <span className="font-mono text-blue-400">
              {net ? formatNet(net.up) : "—"}
            </span>
            <span className="font-mono text-slate-400">↓</span>
            <span className="font-mono text-blue-400">
              {net ? formatNet(net.down) : "—"}
            </span>
          </div>
        ) : (
          // 详细模式：三行
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-200">
              <span className="text-slate-400">CPU 使用率</span>
              <span className="font-mono text-emerald-400">{cpu.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between text-slate-200">
              <span className="text-slate-400">内存占用</span>
              <span className="font-mono text-emerald-400">
                {mem ? formatMemory(mem.used, mem.percent) : "—"}
              </span>
            </div>
            <div className="flex justify-between text-slate-200">
              <span className="text-slate-400">网速 上行 / 下行</span>
              <span className="font-mono text-blue-400">
                {net ? `${formatNet(net.up)} / ${formatNet(net.down)}` : "— / —"}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

MonitorOverlay.displayName = "MonitorOverlay";
