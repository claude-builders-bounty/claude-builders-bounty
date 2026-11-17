import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Electron + Vite 双入口构建：
// - renderer：React 渲染进程（通过 vite dev server 开发，生产构建为静态文件）
// - main：Electron 主进程（单独打包为 CommonJS，供 electron 直接运行）

export default defineConfig(() => {
  return {
    root: path.resolve(__dirname, "src/renderer"),
    base: "./",
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src/renderer"),
        "@shared": path.resolve(__dirname, "src/shared"),
        "@ai": path.resolve(__dirname, "src/ai"),
        "@main": path.resolve(__dirname, "src/main"),
      },
    },
    build: {
      outDir: path.resolve(__dirname, "dist/renderer"),
      emptyOutDir: true,
      sourcemap: true,
      // 渲染进程不打包 node 内置模块，由 Electron 运行时提供
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, "src/renderer/index.html"),
        },
      },
    },
    server: {
      port: 5173,
      strictPort: true,
      fs: {
        allow: [path.resolve(__dirname, "src"), path.resolve(__dirname, "assets")],
      },
    },
    define: {
      __ELECTRON_START_URL__: JSON.stringify(
        process.env["ELECTRON_START_URL"] || "http://localhost:5173"
      ),
    },
  };
});
