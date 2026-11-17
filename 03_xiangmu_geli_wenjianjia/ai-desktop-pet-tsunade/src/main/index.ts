/**
 * Electron 主进程入口
 *
 * 职责：
 * 1. 创建并管理宠物窗口（透明、无边框、置顶、可点击穿透）
 * 2. 注册所有 IPC 处理器
 * 3. 启动系统监控与提醒定时器
 * 4. 应用生命周期管理
 */

import { app, BrowserWindow } from "electron";
import path from "node:path";
import { createPetWindow } from "./window";
import { registerAllIpcHandlers, setPetWindow } from "./ipc";
import { initDb } from "./db";
import { stopMonitor } from "./monitor";
import { stopReminderScheduler } from "./reminder";

// 是否开发模式：NODE_ENV=development 或 显式传了 ELECTRON_START_URL
const isDev = process.env["NODE_ENV"] === "development" || !!process.env["ELECTRON_START_URL"];

// 主窗口实例
let petWindow: BrowserWindow | null = null;

// 确保单实例应用
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on("second-instance", () => {
    // 有人尝试启动第二个实例，将现有窗口聚焦
    if (petWindow) {
      if (petWindow.isMinimized()) petWindow.restore();
      petWindow.focus();
    }
  });
}

// 禁用硬件加速可降低部分显卡驱动的兼容性问题（可选）
app.disableHardwareAcceleration();

// 禁用 GPU 加速（彻底规避 GPU 进程崩溃导致的绿屏/渲染异常）
app.commandLine.appendSwitch("disable-gpu");
app.commandLine.appendSwitch("disable-gpu-compositing");
app.commandLine.appendSwitch("disable-software-rasterizer");

// 所有窗口关闭时不退出（托盘式常驻，此处仅保留宠物窗口）
app.on("window-all-closed", () => {
  // macOS 习惯：点击 dock 图标重新打开
  if (process.platform !== "darwin") {
    // 不退出，保持后台运行
  }
});

app.whenReady().then(async () => {
  await initDb();
  createMainWindow();
});

app.on("activate", () => {
  // macOS：dock 图标被点击且无窗口时重新创建
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

function createMainWindow(): void {
  if (petWindow) {
    petWindow.focus();
    return;
  }

  // 窗口大小
  const winWidth = 320;
  const winHeight = 320;

  // 固定在屏幕可见区域 (100, 100) 便于调试；后续可改回右下角自适应
  const x = 100;
  const y = 100;

  const newWindow = createPetWindow({
    width: winWidth,
    height: winHeight,
    x,
    y,
  });

  petWindow = newWindow;
  setPetWindow(petWindow);

  // 捕获渲染进程控制台输出，便于诊断挂载失败
  petWindow.webContents.on("console-message", (_event, level, message) => {
    const levelMap: Record<number, string> = { 0: "INFO", 1: "WARNING", 2: "ERROR", 3: "LOG" };
    const lv = levelMap[level ?? 0] ?? "LOG";
    console.log(`[Renderer][${lv}] ${message}`);
  });

  // 加载渲染进程
  if (isDev && process.env["ELECTRON_START_URL"]) {
    petWindow.loadURL(process.env["ELECTRON_START_URL"]);
  } else {
    petWindow.loadFile(path.join(__dirname, "../../renderer/index.html"));
  }

  // 开发模式：在独立窗口打开 DevTools，不遮挡宠物窗口
  if (isDev) {
    const win = petWindow!;
    win.webContents.once("dom-ready", () => {
      win.webContents.openDevTools({ mode: "detach" });
    });
  }

  petWindow.on("closed", () => {
    petWindow = null;
  });
}

// 注册 IPC 处理器
registerAllIpcHandlers();

// 退出时清理
app.on("before-quit", () => {
  stopMonitor();
  stopReminderScheduler();
});
