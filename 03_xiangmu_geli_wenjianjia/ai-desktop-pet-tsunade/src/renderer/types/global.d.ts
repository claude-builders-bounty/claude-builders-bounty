/// <reference types="vite/client" />

import type { PetApi } from "@shared/preload-types";

/**
 * 扩展 Window 接口，声明 preload 脚本暴露的 __PET_API__。
 * 渲染进程仅通过 window.__PET_API__ 与主进程通信，绝不直接 require electron。
 */
declare global {
  interface Window {
    __PET_API__: PetApi;
  }
}

export {};
