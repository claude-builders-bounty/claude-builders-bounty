/**
 * 宠物窗口管理
 *
 * 创建透明、无边框、始终置顶的宠物窗口。
 * 支持点击穿透、拖拽移动、双击等交互。
 */

import { BrowserWindow, BrowserWindowConstructorOptions, globalShortcut } from "electron";
import path from "node:path";

/** 宠物窗口配置 */
export interface PetWindowOptions extends Partial<BrowserWindowConstructorOptions> {
  width?: number;
  height?: number;
  x?: number;
  y?: number;
}

/** 创建宠物主窗口 */
export function createPetWindow(options: PetWindowOptions = {}): BrowserWindow {
  const {
    width = 320,
    height = 320,
    x = 100,
    y = 100,
    ...winOpts
  } = options;

  // 透明无边框窗口，背景完全透明，宠物 UI 由渲染进程绘制
  const window: BrowserWindow = new BrowserWindow({
    width,
    height,
    x,
    y,
    frame: false,
    transparent: true,              // ← 透明背景，宠物窗口不显示色块
    backgroundColor: "#00000000",   // ← 完全透明，避免渲染失败时出现色块
    skipTaskbar: false,
    focusable: true,
    hasShadow: false,               // ← 无阴影，保持纯透明宠物外观
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      devTools: true,
      sandbox: false,
    },
    ...winOpts,
  });

  // 调试日志：记录窗口创建后的状态
  console.log("[PetWindow] 窗口创建，bounds=",
    JSON.stringify(window.getBounds()),
    "isVisible=", window.isVisible(),
    "isDestroyed=", window.isDestroyed(),
    "isMinimized=", window.isMinimized());

  // 窗口首次准备好显示时触发
  window.once("ready-to-show", () => {
    console.log("[PetWindow] ready-to-show 触发，bounds=",
      JSON.stringify(window.getBounds()),
      "isVisible=", window.isVisible());
  });

  // 页面加载失败 / 渲染进程崩溃监控（部分事件在此 Electron 版本的类型定义中缺失，故以 any 绑定）
  const wc = window.webContents as unknown as { on: (name: string, handler: (...args: unknown[]) => void) => void };
  wc.on("did-fail-load", (_event: unknown, errorCode: unknown, errorDescription: unknown, validatedURL: unknown) => {
    console.error("[PetWindow] 页面加载失败:", errorCode, errorDescription, validatedURL);
  });

  wc.on("crashed", () => {
    console.error("[PetWindow] 渲染进程崩溃");
  });

  wc.on("unresponsive", () => {
    console.error("[PetWindow] 渲染进程无响应");
  });

  // 先 showInactive 再 show 再 focus，确保窗口在桌面上可见并获得焦点
  window.showInactive();
  window.show();
  window.focus();

  console.log("[PetWindow] show/focus 后，isVisible=", window.isVisible(),
    "isMinimized=", window.isMinimized(),
    "isFocused=", window.isFocused(),
    "bounds=", JSON.stringify(window.getBounds()));

  if (process.platform === "win32") {
    window.setSkipTaskbar(false);
  }

  window.setAlwaysOnTop(true);

  // 注册全局快捷键（示例：Ctrl+Shift+D 切换开发者工具，Ctrl+Shift+T 切换点击穿透）
  let ignoringMouseEvents = false;
  globalShortcut.register("CommandOrControl+Shift+D", () => {
    window.webContents.toggleDevTools();
  });

  globalShortcut.register("CommandOrControl+Shift+T", () => {
    ignoringMouseEvents = !ignoringMouseEvents;
    window.setIgnoreMouseEvents(ignoringMouseEvents);
  });

  return window;
}

/** 设置点击穿透 */
export function setClickThrough(window: BrowserWindow, enabled: boolean): void {
  window.setIgnoreMouseEvents(enabled, { forward: true });
}

/** 设置始终置顶 */
export function setAlwaysOnTop(window: BrowserWindow, enabled: boolean): void {
  window.setAlwaysOnTop(enabled);
}

/** 关闭窗口并释放引用 */
export function closeWindow(window: BrowserWindow | null): void {
  if (window) {
    window.close();
  }
}
