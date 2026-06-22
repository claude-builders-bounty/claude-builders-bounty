import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  // Project-local cache avoids ENOENT flakes when CI runs migration tests then the full suite.
  cacheDir: "node_modules/.vitest",
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    pool: "forks",
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "next/cache": path.resolve(__dirname, "./tests/helpers/next-cache.ts"),
    },
  },
});
