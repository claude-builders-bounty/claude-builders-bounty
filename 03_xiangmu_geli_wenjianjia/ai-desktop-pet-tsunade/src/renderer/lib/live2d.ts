/**
 * Live2D 工具函数
 *
 * 职责：
 * 1. 宠物动作（PetAnimation）与 Live2D 模型内部 motion group 的映射
 * 2. 宠物心情（PetMood）与 Live2D 表情的映射
 * 3. 模型资源路径解析（开发 / 生产环境）
 * 4. 从模型定义中解析可用的 group / 表情名称
 *
 * 不可变性：所有导出对象为常量，函数不修改入参，仅返回新值。
 */

import { MotionPriority } from "pixi-live2d-display";
import type { PetAnimation, PetMood } from "@shared/ipc";

/* ========================================================================
   模型资源常量
   ======================================================================== */

/** 模型文件夹名称 */
export const TSUNADE_MODEL_DIR = "tsunade";

/** 模型设置文件名（Cubism 4 标准：.model3.json） */
export const MODEL_SETTINGS_FILE = "tsunade.model3.json";

/** 默认动作播放优先级 */
export const DEFAULT_MOTION_PRIORITY = MotionPriority.NORMAL;

/* ========================================================================
   动作映射：PetAnimation -> 模型内部 motion group 候选名
   ========================================================================
   模型实际定义的 group 名取决于 .model3.json / .motion3.json，不同作者
   命名可能不同（如 "Idle" / "idle"）。此处按常见命名给出候选列表，
   运行时由 resolveMotionGroup 选取模型实际定义的第一个匹配项。
   ======================================================================== */

/** 宠物动作到 Live2D motion group 的候选名映射 */
export const MOTION_GROUP_MAP: Record<PetAnimation, string[]> = {
  idle: ["Idle", "idle"],
  talk: ["Talk", "talk"],
  drink: ["Drink", "drink"],
  gamble: ["Gamble", "gamble"],
  angry: ["Angry", "angry"],
  heal: ["Heal", "heal"],
  blush: ["Blush", "blush"],
  sulk: ["Sulk", "sulk"],
};

/* ========================================================================
   表情映射：PetMood -> 模型内部 expression 名候选
   ======================================================================== */

/** 宠物心情到 Live2D 表情名的候选映射 */
export const EXPRESSION_MAP: Record<PetMood, string[]> = {
  happy: ["happy", "Happy", "normal"],
  angry: ["angry", "Angry"],
  drunk: ["drunk", "Drunk"],
  tired: ["tired", "Tired"],
  love: ["love", "Love"],
  normal: ["normal", "Normal", "idle"],
};

/* ========================================================================
   资源路径
   ========================================================================
   - 开发环境：Vite dev server 通过 /models/tsunade/ 提供（文件放在 public/）
   - 生产环境：electron-builder 将 assets/models/ 拷贝到 resources/models/，
     渲染进程应通过 file://${process.resourcesPath}/models/tsunade/ 访问。
     renderer 进程受 contextIsolation 限制，无法直接读取 process.resourcesPath，
     生产环境的基础路径应由调用方通过 modelBaseUrl prop 注入。
   ======================================================================== */

/** 解析模型资源根路径 URL */
export function getModelBaseUrl(isDev = import.meta.env.DEV): string {
  if (isDev) {
    return `/models/${TSUNADE_MODEL_DIR}/`;
  }
  // 生产环境兜底为相对路径，实际部署时应通过 PetLive2D 的 modelBaseUrl prop
  // 传入 file://${process.resourcesPath}/models/tsunade/ 覆盖此值
  return `models/${TSUNADE_MODEL_DIR}/`;
}

/** 拼接模型设置文件的完整 URL */
export function resolveModelUrl(baseUrl: string): string {
  const normalized = baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
  return `${normalized}${MODEL_SETTINGS_FILE}`;
}

/* ========================================================================
   从模型定义中解析可用名称
   ======================================================================== */

/**
 * 从候选 motion group 名称中选取模型实际定义的第一个可用名。
 * @param definitions 模型 motionManager.definitions（Record<group, Motion[]>）
 * @param candidates 候选名称列表，按优先级排序
 * @return 匹配到的 group 名，或 undefined
 */
export function resolveMotionGroup(
  definitions: Record<string, unknown> | undefined | null,
  candidates: string[]
): string | undefined {
  if (!definitions) {
    return undefined;
  }
  for (const name of candidates) {
    if (name in definitions) {
      return name;
    }
  }
  return undefined;
}

/**
 * 从候选表情名称中选取模型实际定义的第一个可用表情名。
 * @param expressions 模型 expressionManager.definitions（{ name?: string }[]）
 * @param candidates 候选名称列表，按优先级排序
 * @return 匹配到的表情名，或 undefined
 */
export function resolveExpressionName(
  expressions: ReadonlyArray<{ name?: string }> | undefined | null,
  candidates: string[]
): string | undefined {
  if (!expressions?.length) {
    return undefined;
  }
  const names = new Set(
    expressions.map((expr) => expr.name).filter((name): name is string => Boolean(name))
  );
  for (const name of candidates) {
    if (names.has(name)) {
      return name;
    }
  }
  return undefined;
}
