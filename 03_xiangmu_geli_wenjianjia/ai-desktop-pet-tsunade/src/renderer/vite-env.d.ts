/// <reference types="vite/client" />

// 环境变量类型
interface ImportMetaEnv {
  readonly VITE_APP_VERSION: string;
  readonly VITE_DEV_SERVER_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
