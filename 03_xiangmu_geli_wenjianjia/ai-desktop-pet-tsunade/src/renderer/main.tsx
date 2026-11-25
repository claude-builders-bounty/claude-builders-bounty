import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/index.css";

console.log("[Renderer] main.tsx 入口开始执行");

const rootElement = document.getElementById("root");
if (!rootElement) {
  console.error("[Renderer] 未找到 #root 容器，React 无法挂载");
  throw new Error("未找到 #root 容器，React 无法挂载");
}

console.log("[Renderer] 挂载 React 应用到 #root");
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
console.log("[Renderer] React 应用挂载完成");
