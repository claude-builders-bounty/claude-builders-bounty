/**
 * 系统监控模块
 *
 * 定期采集 CPU 使用率、内存占用、网速，通过 IPC 事件推送给渲染进程。
 * 使用 Electron 的 process.cpuUsage() 与 Node os 模块实现，避免重型依赖。
 */

import { app } from "electron";
import os from "node:os";
import { EventEmitter } from "node:events";

interface NetworkSnapshot {
  timestamp: number;
  bytesSent: number;
  bytesRecv: number;
}

interface MonitorState {
  interval: NodeJS.Timeout | null;
  lastCpu: { user: number; system: number } | null;
  lastCpuTimestamp: number | null;
  lastNet: NetworkSnapshot | null;
  enabled: boolean;
}

const state: MonitorState = {
  interval: null,
  lastCpu: null,
  lastCpuTimestamp: null,
  lastNet: null,
  enabled: false,
};

// 事件发射器，供 ipc 模块订阅并转发给渲染进程
export const monitorEmitter = new EventEmitter();

/** 读取系统网络 IO 计数（跨平台兼容） */
function getNetworkIO(): NetworkSnapshot | null {
  try {
    const ifaces = os.networkInterfaces();
    let bytesSent = 0;
    let bytesRecv = 0;

    for (const name of Object.keys(ifaces)) {
      const details = ifaces[name];
      if (!details) continue;
      for (const detail of details) {
        // 内部接口（如 loopback）跳过
        if (detail.internal) continue;
        // Node 类型定义未暴露 bytesSent/bytesRecv，运行时实际存在，此处断言
        const iface = detail as { bytesSent?: number; bytesRecv?: number };
        bytesSent += iface.bytesSent ?? 0;
        bytesRecv += iface.bytesRecv ?? 0;
      }
    }

    return { timestamp: Date.now(), bytesSent, bytesRecv };
  } catch {
    return null;
  }
}

/** 计算 CPU 使用率百分比 */
function calculateCpuPercent(current: NodeJS.CpuUsage): number {
  const totalCurrent = current.user + current.system;
  let percent = 0;

  if (state.lastCpu && state.lastCpuTimestamp !== null) {
    const totalDelta = totalCurrent - (state.lastCpu.user + state.lastCpu.system);
    const timeDelta = Date.now() - state.lastCpuTimestamp;
    if (timeDelta > 0) {
      percent = (totalDelta / timeDelta) * 100 * os.cpus().length;
    }
  }

  state.lastCpu = { user: current.user, system: current.system };
  state.lastCpuTimestamp = Date.now();

  return Math.max(0, Math.min(100, percent));
}

/** 采集一次监控数据并发送事件 */
function collectStats(): void {
  const cpuUsage = process.cpuUsage();
  const cpuPercent = calculateCpuPercent(cpuUsage);

  const totalMem = os.totalmem();
  const freeMem = os.freemem();
  const usedMem = totalMem - freeMem;
  const memPercent = (usedMem / totalMem) * 100;

  const netNow = getNetworkIO();
  let up = 0;
  let down = 0;

  if (state.lastNet && netNow) {
    const timeDelta = netNow.timestamp - state.lastNet.timestamp;
    if (timeDelta > 0) {
      up = (netNow.bytesSent - state.lastNet.bytesSent) / (timeDelta / 1000);
      down = (netNow.bytesRecv - state.lastNet.bytesRecv) / (timeDelta / 1000);
    }
  }

  if (netNow) state.lastNet = netNow;

  const stats = {
    cpu: Math.round(cpuPercent * 10) / 10,
    memory: {
      total: totalMem,
      used: usedMem,
      free: freeMem,
      percent: Math.round(memPercent * 10) / 10,
    },
    network: {
      up: Math.round(up * 10) / 10,
      down: Math.round(down * 10) / 10,
    },
    timestamp: Date.now(),
  };

  monitorEmitter.emit("stats", stats);
}

/** 启动监控 */
export function startMonitor(intervalMs: number = 5000): void {
  if (state.interval) return;
  state.enabled = true;
  // 先采集一次基线
  process.cpuUsage();
  state.lastNet = getNetworkIO();
  state.lastCpuTimestamp = Date.now();

  state.interval = setInterval(collectStats, intervalMs);
  // 立即采集一次
  collectStats();
}

/** 停止监控 */
export function stopMonitor(): void {
  if (state.interval) {
    clearInterval(state.interval);
    state.interval = null;
  }
  state.enabled = false;
  state.lastCpu = null;
  state.lastCpuTimestamp = null;
  state.lastNet = null;
}

/** 是否正在监控 */
export function isMonitoring(): boolean {
  return state.enabled;
}

/** 应用退出时清理 */
app.on("before-quit", () => {
  stopMonitor();
});
