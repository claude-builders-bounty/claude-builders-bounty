/**
 * Live2D 实例管理 Hook
 *
 * 职责：
 * 1. 创建与销毁 PixiJS Application（Canvas 透明背景，适配无边框透明窗口）
 * 2. 加载 Live2D 模型（.model3.json + .moc3 + .textures/）
 * 3. 暴露控制 API：playAnimation、setExpression、resize、destroy
 * 4. 生命周期绑定：挂载时初始化，卸载时彻底销毁（app.destroy() 防内存泄漏）
 *
 * 不可变性：函数不修改入参；内部状态通过 React ref 保存，不对外暴露可变引用。
 */

import { useEffect, useRef, useCallback, useState } from "react";
import * as PIXI from "pixi.js";
import { Application, Container } from "pixi.js";
import { Live2DModel, MotionPriority } from "pixi-live2d-display/cubism4";

// 确保 Pixi 可被 pixi-live2d-display 引用，以自动注册 Ticker 驱动模型更新
if (typeof window !== "undefined" && !(window as any).PIXI) {
  (window as any).PIXI = PIXI;
}

import {
  getModelBaseUrl,
  resolveModelUrl,
  resolveMotionGroup,
  resolveExpressionName,
  MOTION_GROUP_MAP,
  EXPRESSION_MAP,
  DEFAULT_MOTION_PRIORITY,
} from "../lib/live2d";
import type { PetAnimation, PetMood } from "@shared/ipc";

/* ========================================================================
   类型定义
   ======================================================================== */

/** Pixi 容器引用（用于在外部挂载到 DOM 节点） */
export interface Live2DContainerRef {
  container: Container;
  view: HTMLCanvasElement;
}

/** Live2D 控制 API */
export interface Live2DController {
  /** 播放动作（group 优先级：按 PetAnimation 映射解析实际 group） */
  playAnimation: (animation: PetAnimation) => Promise<void>;
  /** 设置表情（PetMood 映射为模型表情名） */
  setExpression: (mood: PetMood) => Promise<void>;
  /** 播放指定 group 的动作（绕过映射，直接指定 group 名） */
  playMotion: (group: string, index?: number) => Promise<void>;
  /** 设置模型缩放 */
  setScale: (scale: number) => void;
  /** 设置模型位置 */
  setPosition: (x: number, y: number) => void;
  /** 调整画布尺寸 */
  resize: (width: number, height: number) => void;
  /** 是否已就绪（模型加载完成） */
  isReady: boolean;
  /** 销毁 Pixi 应用与 Live2D 实例 */
  destroy: () => void;
  /** Pixi 容器（只读） */
  readonly container: Container | null;
  /** Canvas 视图（只读） */
  readonly view: HTMLCanvasElement | null;
}

/** Hook 选项 */
export interface UseLive2DOptions {
  /** 模型资源根路径（生产环境建议传入 file://${process.resourcesPath}/models/tsunade/） */
  modelBaseUrl?: string;
  /** 初始缩放 */
  scale?: number;
  /** 是否自动播放 idle 动作 */
  autoPlayIdle?: boolean;
  /** 加载成功回调 */
  onLoad?: () => void;
  /** 加载失败回调 */
  onError?: (error: Error) => void;
}

/* ========================================================================
   Hook
   ======================================================================== */

/**
 * 创建并管理 Live2D 实例。
 * 调用方通过 containerRef 获取 Pixi Container 与 canvas，自行挂载到 DOM。
 */
export function useLive2D(options: UseLive2DOptions = {}): Live2DController {
  const {
    modelBaseUrl,
    scale = 1,
    autoPlayIdle = true,
    onLoad,
    onError,
  } = options;

  const appRef = useRef<Application | null>(null);
  const modelRef = useRef<Live2DModel | null>(null);
  const containerRef = useRef<Container | null>(null);
  const readyRef = useRef(false);

  // 是否已挂载（用于异步加载完成后的状态守护）
  const mountedRef = useRef(true);

  const [isReady, setIsReady] = useState(false);

  const baseUrl = useCallback(() => {
    return modelBaseUrl ?? getModelBaseUrl();
  }, [modelBaseUrl]);

  /* ----------------------------------------------------------------
     创建 Pixi 应用
     ---------------------------------------------------------------- */
  const createApp = useCallback((): Application => {
    const app = new Application({
      view: document.createElement("canvas"),
      backgroundAlpha: 0, // 透明背景，适配无边框透明窗口
      autoStart: true,
      resolution: window.devicePixelRatio || 1,
      antialias: true,
      width: 320,
      height: 320,
    });

    // 禁用 Pixi 默认的画布排版（由父容器 CSS 控制尺寸）
    app.view.style.display = "block";
    app.view.style.width = "100%";
    app.view.style.height = "100%";

    const container = new Container();
    app.stage.addChild(container);
    containerRef.current = container;

    return app;
  }, []);

  /* ----------------------------------------------------------------
     加载 Live2D 模型
     ---------------------------------------------------------------- */
  const loadModel = useCallback(async (app: Application) => {
    const url = resolveModelUrl(baseUrl());

    const model = await Live2DModel.from(url, {
      autoUpdate: true,
      autoInteract: false,
    });

    app.stage.addChild(model);
    modelRef.current = model;

    // 设置缩放与位置（居中）
    model.scale.set(scale, scale);
    model.position.set(app.screen.width / 2, app.screen.height / 2);

    // 启用内置 physics、eyeBlink、breathing（通过 Live2DModel 内部 autoUpdate）
    readyRef.current = true;
    setIsReady(true);

    if (autoPlayIdle) {
      await playIdle(model);
    }

    onLoad?.();
  }, [baseUrl, scale, autoPlayIdle, onLoad]);

  /* ----------------------------------------------------------------
     播放动作
     ---------------------------------------------------------------- */
  const playAnimation = useCallback(
    async (animation: PetAnimation): Promise<void> => {
      const model = modelRef.current;
      if (!model || !readyRef.current) {
        throw new Error("Live2D 模型尚未就绪，无法播放动作");
      }

      const definitions = model.internalModel?.motionManager?.definitions;
      const candidates = MOTION_GROUP_MAP[animation];
      const group = resolveMotionGroup(definitions, candidates);

      if (!group) {
        throw new Error(
          `未找到与动作 "${animation}" 对应的 motion group（候选：${candidates.join(
            ", "
          )}）`
        );
      }

      const success = await model.motion(group, undefined, DEFAULT_MOTION_PRIORITY);
      if (!success) {
        throw new Error(`动作 "${animation}" 播放失败（group: ${group}）`);
      }
    },
    []
  );

  const playMotion = useCallback(
    async (group: string, index?: number): Promise<void> => {
      const model = modelRef.current;
      if (!model || !readyRef.current) {
        throw new Error("Live2D 模型尚未就绪，无法播放动作");
      }
      const success = await model.motion(group, index, DEFAULT_MOTION_PRIORITY);
      if (!success) {
        throw new Error(`动作播放失败（group: ${group}, index: ${index ?? -1}）`);
      }
    },
    []
  );

  const playIdle = useCallback(
    async (model: Live2DModel): Promise<void> => {
      const definitions = model.internalModel?.motionManager?.definitions;
      const group = resolveMotionGroup(definitions, MOTION_GROUP_MAP.idle);
      if (group) {
        await model.motion(group, undefined, MotionPriority.IDLE);
      }
    },
    []
  );

  /* ----------------------------------------------------------------\n     设置表情\n     ---------------------------------------------------------------- */
    const setExpression = useCallback(
      async (mood: PetMood): Promise<void> => {
        const model = modelRef.current;
        if (!model || !readyRef.current) {
          throw new Error("Live2D 模型尚未就绪，无法切换表情");
        }

        // @pixi/live2d-display v1.x: expression 直接在 model 上，内部会查找 expressionManager
        const expressions = (model as any).internalModel?.expressionManager?.definitions;
        const candidates = EXPRESSION_MAP[mood];
        const name = resolveExpressionName(expressions, candidates);

        if (name === undefined) {
          // 没有匹配表情时重置为默认表情，不抛出（兜底）
          (model as any).expressionManager?.resetExpression?.();
          return;
        }

        await model.expression(name);
      },
      []
    );

  /* ----------------------------------------------------------------
     变换操作
     ---------------------------------------------------------------- */
  const setScale = useCallback((value: number) => {
    const model = modelRef.current;
    if (model) {
      model.scale.set(value, value);
    }
  }, []);

  const setPosition = useCallback((x: number, y: number) => {
    const model = modelRef.current;
    if (model) {
      model.position.set(x, y);
    }
  }, []);

  const resize = useCallback(
    (width: number, height: number) => {
      const app = appRef.current;
      if (!app) return;
      app.renderer.resize(width, height);
      const model = modelRef.current;
      if (model) {
        model.position.set(width / 2, height / 2);
      }
    },
    []
  );

  /* ----------------------------------------------------------------
     销毁
     ---------------------------------------------------------------- */
  const destroy = useCallback(() => {
    mountedRef.current = false;
    if (modelRef.current) {
      modelRef.current.destroy({ children: true, texture: true, baseTexture: true });
      modelRef.current = null;
    }
    if (appRef.current) {
      appRef.current.destroy(true, { children: true, texture: true, baseTexture: true });
      appRef.current = null;
    }
    containerRef.current = null;
    readyRef.current = false;
    setIsReady(false);
  }, []);

  /* ----------------------------------------------------------------
     挂载：创建应用并加载模型
     ---------------------------------------------------------------- */
  useEffect(() => {
    mountedRef.current = true;

    (async () => {
      try {
        const app = createApp();
        appRef.current = app;
        await loadModel(app);
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        readyRef.current = false;
        setIsReady(false);
        onError?.(error);
        // 不静默吞掉错误：向控制台输出详细上下文，方便调试
        console.error("[useLive2D] 初始化失败:", error);
      }
    })();

    return () => {
      mountedRef.current = false;
      destroy();
    };
  }, [createApp, loadModel, destroy, onError]);

  /* 将 store 的 ready 状态与本地保持同步（供组件层读取） */
  useEffect(() => {
    // 本 hook 独立于 zustand，若需与全局同步可在此接入 useLive2DStore
  }, [isReady]);

  return {
    playAnimation,
    setExpression,
    playMotion,
    setScale,
    setPosition,
    resize,
    get isReady() {
      return isReady && readyRef.current;
    },
    destroy,
    get container(): Container | null {
      return containerRef.current;
    },
    get view(): HTMLCanvasElement | null {
      return appRef.current?.view ?? null;
    },
  };
}
