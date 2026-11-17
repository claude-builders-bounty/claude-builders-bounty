/**
 * PetLive2D — 宠物 Live2D 核心展示组件
 *
 * 职责：
 * 1. 内部使用 useLive2D hook 创建与管理 PixiJS + Live2D 实例
 * 2. 将 Pixi Canvas 挂载到 DOM 容器，背景透明，适配无边框透明窗口
 * 3. 监听窗口 resize，自动调用 controller.resize() 做响应式适配
 * 4. 通过 useImperativeHandle 暴露 { playAnimation, setExpression, resize, isReady }
 * 5. 不可变性：不修改入参，所有配置通过 props 传入，内部状态由 ref 管理
 */

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useCallback,
} from "react";

import { useLive2D } from "../../hooks/useLive2D";
import type { PetAnimation, PetMood } from "@shared/ipc";

/** PetLive2D 组件属性 */
export interface PetLive2DProps {
  /** 模型资源根路径（生产环境建议传入 file://${process.resourcesPath}/models/tsunade/） */
  modelBaseUrl?: string;
  /** 初始缩放，默认 1 */
  scale?: number;
  /** 是否自动播放 idle 动作，默认 true */
  autoPlayIdle?: boolean;
  /** 容器宽度（px），默认 320 */
  width?: number;
  /** 容器高度（px），默认 320 */
  height?: number;
  /** 容器额外的 CSS 类名 */
  className?: string;
  /** 模型加载成功回调 */
  onLoad?: () => void;
  /** 模型加载失败回调 */
  onError?: (error: Error) => void;
}

/** 对外暴露的控制句柄 */
export interface PetLive2DHandle {
  /** 播放动作（PetAnimation，内部映射为模型 motion group） */
  playAnimation: (animation: PetAnimation) => Promise<void>;
  /** 设置表情（PetMood，内部映射为模型表情名） */
  setExpression: (mood: PetMood) => Promise<void>;
  /** 调整画布尺寸 */
  resize: (width: number, height: number) => void;
  /** 是否已就绪（模型加载完成） */
  isReady: boolean;
}

export const PetLive2D = forwardRef<PetLive2DHandle, PetLive2DProps>(
  (
    {
      modelBaseUrl,
      scale = 1,
      autoPlayIdle = true,
      width = 320,
      height = 320,
      className,
      onLoad,
      onError,
    },
    ref,
  ) => {
    const containerRef = useRef<HTMLDivElement>(null);

    const controller = useLive2D({
      modelBaseUrl,
      scale,
      autoPlayIdle,
      onLoad,
      onError,
    });

    // 将 Pixi Canvas 挂载到 DOM 容器
    useEffect(() => {
      const container = containerRef.current;
      const view = controller.view;
      if (!container || !view) {
        return undefined;
      }
      container.appendChild(view);
      return () => {
        if (view.parentElement === container) {
          container.removeChild(view);
        }
      };
    }, [controller.view]);

    // 监听窗口 resize，做响应式适配
    const handleResize = useCallback(() => {
      const container = containerRef.current;
      if (!container) {
        return;
      }
      const rect = container.getBoundingClientRect();
      controller.resize(rect.width, rect.height);
    }, [controller]);

    useEffect(() => {
      handleResize();
      window.addEventListener("resize", handleResize);
      return () => {
        window.removeEventListener("resize", handleResize);
      };
    }, [handleResize]);

    // 暴露控制句柄
    useImperativeHandle(
      ref,
      () => ({
        playAnimation: controller.playAnimation,
        setExpression: controller.setExpression,
        resize: controller.resize,
        get isReady() {
          return controller.isReady;
        },
      }),
      [controller],
    );

    return (
      <div
        ref={containerRef}
        className={className}
        style={{
          position: "relative",
          width,
          height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
          background: "transparent",
        }}
      />
    );
  },
);

PetLive2D.displayName = "PetLive2D";
