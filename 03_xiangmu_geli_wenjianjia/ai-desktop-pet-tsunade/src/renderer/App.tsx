import { useCallback, useState } from "react";

import { PetModel } from "@/components/pet/PetModel";
import { PetContextMenu } from "@/components/pet/PetContextMenu";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { SettingsPanel } from "@/components/settings/SettingsPanel";
import { MonitorOverlay } from "@/components/monitor/MonitorOverlay";
import { usePetState, useSettings, useReminders } from "@/hooks/usePetApi";
import type { PetMood } from "@shared/ipc";

/** App 主入口：聚合宠物模型层、右键菜单、聊天面板、设置面板、监控悬浮窗 */
export default function App() {
  console.log("[App] App 组件渲染");
  // 各面板可见状态
  const [chatVisible, setChatVisible] = useState(false);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [monitorVisible, setMonitorVisible] = useState(false);
  const [menuVisible, setMenuVisible] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });

  const { state: petState, fetchPetState, fetchAffection } = usePetState();
  const { fetchSettings } = useSettings();
  const { fetchReminders } = useReminders();

  // 面板打开时拉取相关数据
  const handleOpenChat = useCallback(() => {
    setChatVisible(true);
  }, []);

  const handleOpenSettings = useCallback(() => {
    void fetchSettings();
    void fetchReminders();
    setSettingsVisible(true);
  }, [fetchSettings, fetchReminders]);

  const handleOpenMonitor = useCallback(() => {
    setMonitorVisible(true);
  }, []);

  const handleCloseMenu = useCallback(() => {
    setMenuVisible(false);
  }, []);

  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setMenuPosition({ x: e.clientX, y: e.clientY });
      setMenuVisible(true);
    },
    []
  );

  const mood: PetMood | undefined = petState?.mood;

  return (
    <div
      className="fixed inset-0 text-slate-100 selection:bg-slate-700"
      style={{
        position: "relative",
        width: "100vw",
        height: "100vh",
        overflow: "hidden",
        background: "transparent",
      }}
      onContextMenu={handleContextMenu}
    >
      {/* 宠物模型层（底层） */}
      <div
        id="pet-layer"
        className="fixed inset-0"
        aria-hidden="true"
      >
        <div
          className="absolute right-16 bottom-16 w-64 h-64"
          aria-label="宠物主体"
          onContextMenu={handleContextMenu}
        >
          <PetModel
            width={320}
            height={320}
            scale={1}
            autoPlayIdle
            onLoad={() => {
              void fetchPetState();
              void fetchAffection();
            }}
            onContextMenu={handleContextMenu}
          />
        </div>
      </div>

      {/* UI 交互层 */}
      <div id="ui-layer" className="fixed inset-0 pointer-events-auto z-10">
        {/* 宠物右键菜单 */}
        {menuVisible && (
          <PetContextMenu
            anchorX={menuPosition.x}
            anchorY={menuPosition.y}
            mood={mood}
            onClose={handleCloseMenu}
            onOpenChat={handleOpenChat}
            onOpenSettings={handleOpenSettings}
            onOpenMonitor={handleOpenMonitor}
          />
        )}

        {/* 聊天面板 */}
        <ChatPanel visible={chatVisible} onClose={() => setChatVisible(false)} />

        {/* 设置面板 */}
        <SettingsPanel
          visible={settingsVisible}
          onClose={() => setSettingsVisible(false)}
        />

        {/* 监控悬浮窗 */}
        <MonitorOverlay
          visible={monitorVisible}
          onClose={() => setMonitorVisible(false)}
        />
      </div>
    </div>
  );
}
