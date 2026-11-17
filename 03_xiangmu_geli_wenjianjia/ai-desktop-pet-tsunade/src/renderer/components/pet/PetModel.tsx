/**
 * PetModel — 宠物模型封装组件
 *
 * 职责：
 * 1. forwardRef 接收外部 ref，向上游透传 { playAnimation, setExpression, resize, isReady }
 * 2. 挂载时自动创建 canvas 容器，挂载 PetLive2D
 * 3. 加载失败自动降级到占位 UI（会呼吸的彩色圆形，Canvas 2D 绘制），不崩溃、不报错
 * 4. 透明背景，适配无边框透明窗口
 *
 * 不可变性：不修改入参，内部降级状态通过 useState 管理，降级后不可自动恢复（避免闪烁）。
 */

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  useCallback,
} from "react";

import { PetLive2D, type PetLive2DProps, type PetLive2DHandle } from "./PetLive2D";
import type { PetAnimation, PetMood } from "@shared/ipc";

/** PetModel 组件属性 */
export interface PetModelProps extends Omit<PetLive2DProps, "onError"> {
  /** 占位圆形的主色调（默认纲手主题紫色） */
  placeholderColor?: string;
  /** 右键菜单回调（透传给根容器，防止内部 Canvas 拦截） */
  onContextMenu?: React.MouseEventHandler<HTMLDivElement>;
}

/** 占位兜底组件：Canvas 2D 绘制的会呼吸的彩色圆形 */
function PlaceholderCircle({
  color = "#8b5cf6",
  size,
}: {
  color: string;
  size: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const frameRef = useRef<number>(0);
  const startTimeRef = useRef<number>(0);

  // 呼吸动画：半径与透明度随正弦波变化
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return undefined;
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return undefined;
    }

    startTimeRef.current = performance.now();

    const draw = () => {
      const now = performance.now();
      const elapsed = (now - startTimeRef.current) / 1000;
      const scale = 1 + Math.sin(elapsed * 2) * 0.12; // 0.88 ~ 1.12
      const alpha = 0.6 + Math.sin(elapsed * 2 + 1) * 0.25; // 0.35 ~ 0.85

      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(size * dpr);
      canvas.height = Math.floor(size * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, size, size);

      // 外层发光晕圈
      const gradient = ctx.createRadialGradient(
        size / 2,
        size / 2,
        0,
        size / 2,
        size / 2,
        size / 2,
      );
      gradient.addColorStop(0, `${color}dd`);
      gradient.addColorStop(0.4, `${color}66`);
      gradient.addColorStop(1, `${color}00`);

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(size / 2, size / 2, (size / 2) * scale, 0, Math.PI * 2);
      ctx.fill();

      // 中心实心圆
      ctx.fillStyle = `${color}${Math.round(alpha * 255).toString(16).padStart(2, "0")}`;
      ctx.beginPath();
      ctx.arc(size / 2, size / 2, (size * 0.35) * scale, 0, Math.PI * 2);
      ctx.fill();

      frameRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      cancelAnimationFrame(frameRef.current);
    };
  }, [color, size]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        display: "block",
        background: "transparent",
      }}
    />
  );
}

export const PetModel = forwardRef<PetLive2DHandle, PetModelProps>(
  (
    {
      modelBaseUrl,
      scale = 1,
      autoPlayIdle = true,
      width = 320,
      height = 320,
      className,
      placeholderColor = "#8b5cf6",
      onLoad,
      onContextMenu,
      ...rest
    },
    ref,
  ) => {
    const [isFallback, setIsFallback] = useState(false); // 默认加载 Live2D，失败时才降级到占位圆
    const live2dRef = useRef<PetLive2DHandle | null>(null);

    const handleLoad = useCallback(() => {
      setIsFallback(false);
      onLoad?.();
    }, [onLoad]);

    const handleError = useCallback((error: Error) => {
      console.warn("[PetModel] Live2D 模型加载失败，降级到占位 UI:", error.message);
      setIsFallback(true);
      console.log("[PetModel] 已切换到占位 UI，isFallback=true");
    }, []);

    useImperativeHandle(
      ref,
      () => ({
        playAnimation: async (animation: PetAnimation) => {
          if (isFallback || !live2dRef.current) {
            return;
          }
          await live2dRef.current.playAnimation(animation);
        },
        setExpression: async (mood: PetMood) => {
          if (isFallback || !live2dRef.current) {
            return;
          }
          await live2dRef.current.setExpression(mood);
        },
        resize: (width: number, height: number) => {
          if (isFallback || !live2dRef.current) {
            return;
          }
          live2dRef.current.resize(width, height);
        },
        get isReady() {
          return !isFallback && Boolean(live2dRef.current?.isReady);
        },
      }),
      [isFallback],
    );

    console.log("[PetModel] 渲染，isFallback=", isFallback);

    return (
      <div
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
          border: "2px solid red", // 红框确认渲染区域
        }}
        onContextMenu={onContextMenu}
      >
        {!isFallback ? (
          <PetLive2D
            ref={live2dRef}
            modelBaseUrl={modelBaseUrl}
            scale={scale}
            autoPlayIdle={autoPlayIdle}
            width={width}
            height={height}
            onLoad={handleLoad}
            onError={handleError}
            {...rest}
          />
        ) : (
          <PlaceholderCircle color={placeholderColor} size={Math.min(width, height)} />
        )}
      </div>
    );
  },
);

PetModel.displayName = "PetModel";
