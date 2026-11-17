import {
  useEffect,
  useRef,
  useMemo,
} from "react";
import { createPortal } from "react-dom";
import {
  useWindow,
  useChat,
  useSettings,
  useMonitor,
} from "@/hooks/usePetApi";
import type { PetMood } from "@shared/ipc";

/** 宠物右键菜单属性 */
export interface PetContextMenuProps {
  /** 菜单锚点位置（相对于 viewport） */
  anchorX: number;
  anchorY: number;
  /** 关闭回调 */
  onClose: () => void;
  /** 打开聊天面板回调 */
  onOpenChat?: () => void;
  /** 打开设置面板回调 */
  onOpenSettings?: () => void;
  /** 打开监控面板回调 */
  onOpenMonitor?: () => void;
  /** 宠物当前心情（用于显示） */
  mood?: PetMood;
}

/** 菜单项：普通项 */
interface MenuItemAction {
  label: string;
  action: () => void;
  disabled?: boolean;
  danger?: boolean;
  divider?: false;
}

/** 菜单项：分割线 */
interface MenuItemDivider {
  divider: true;
  label?: never;
  action?: never;
  disabled?: never;
  danger?: never;
}

type MenuItem = MenuItemAction | MenuItemDivider;

/** 宠物右键菜单：渲染到 body，避免被父容器裁剪 */
export function PetContextMenu({
  anchorX,
  anchorY,
  onClose,
  onOpenChat,
  onOpenSettings,
  onOpenMonitor,
  mood,
}: PetContextMenuProps) {
  const {
    setClickThrough,
    setAlwaysOnTop,
    toggleDevTools,
    closeWindow,
    dragWindow,
  } = useWindow();
  const { clickThrough, alwaysOnTop } = useWindow();
  const { fetchChatHistory } = useChat();
  const { fetchSettings } = useSettings();
  const { startMonitor, stopMonitor, monitorActive } = useMonitor();

  const menuRef = useRef<HTMLDivElement>(null);
  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  // ESC 关闭
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // 构建菜单项（每次渲染时根据最新状态构建）
  const menuItems = useMemo((): MenuItem[] => {
    const showChat = () => {
      fetchChatHistory();
      onClose();
      onOpenChat?.();
    };
    const showSettings = () => {
      fetchSettings();
      onClose();
      onOpenSettings?.();
    };
    const showMonitor = () => {
      if (monitorActive) {
        stopMonitor();
      } else {
        startMonitor();
      }
      onClose();
      onOpenMonitor?.();
    };
    const resetPosition = () => {
      dragWindow();
      onClose();
    };

    return [
      { label: "💬 打开聊天", action: showChat },
      { label: "⚙️ 打开设置", action: showSettings },
      {
        label: monitorActive ? "📊 隐藏监控" : "📊 显示监控",
        action: showMonitor,
      },
      { divider: true },
      {
        label: clickThrough ? "🔓 取消点击穿透" : "🔒 启用点击穿透",
        action: () => {
          setClickThrough(!clickThrough);
          onClose();
        },
      },
      {
        label: alwaysOnTop ? "📌 取消置顶" : "📌 始终置顶",
        action: () => {
          setAlwaysOnTop(!alwaysOnTop);
          onClose();
        },
      },
      { label: "🏠 重置位置", action: resetPosition },
      { divider: true },
      { label: "🛠️ 开发者工具", action: () => { toggleDevTools(); onClose(); } },
      { divider: true },
      { label: "ℹ️ 关于", action: () => { alert("AI桌宠·纲手 v1.0.0\n基于 Electron + React + Live2D"); onClose(); } },
      { divider: true },
      { label: "❌ 退出", action: () => { closeWindow(); onClose(); }, danger: true },
    ];
  }, [
    clickThrough,
    alwaysOnTop,
    monitorActive,
    fetchChatHistory,
    fetchSettings,
    startMonitor,
    stopMonitor,
    dragWindow,
    setClickThrough,
    setAlwaysOnTop,
    toggleDevTools,
    closeWindow,
    onClose,
    onOpenChat,
    onOpenSettings,
    onOpenMonitor,
  ]);

  // 渲染到 body 避免被裁剪
  const portalContent = (
    <div
      ref={menuRef}
      className="fixed z-[9999] min-w-[180px] bg-slate-800/95 backdrop-blur-md border border-slate-700 rounded-lg shadow-2xl py-1 animate-fade-in"
      style={{ left: anchorX, top: anchorY }}
      role="menu"
      aria-orientation="vertical"
    >
      {/* 头部心情显示 */}
      {mood && (
        <div className="px-3 py-1.5 border-b border-slate-700 text-xs text-slate-400">
          当前心情：{mood}
        </div>
      )}
      <ul className="py-1" role="listbox">
        {menuItems.map((item, index) => {
          if (item.divider) {
            return (
              <li key={`divider-${index}`} className="border-t border-slate-700 my-1" />
            );
          }
          return (
            <li
              key={index}
              role="menuitem"
              className={`flex items-center w-full px-3 py-1.5 text-sm text-slate-100 hover:bg-slate-700 transition-colors ${
                item.disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"
              } ${item.danger ? "text-red-400 hover:bg-red-900/30" : ""}`}
              onClick={() => !item.disabled && item.action()}
              tabIndex={-1}
            >
              {item.label}
            </li>
          );
        })}
      </ul>
    </div>
  );

  return createPortal(portalContent, document.body);
}

PetContextMenu.displayName = "PetContextMenu";
