import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/demo/test/setup.ts"],
    include: ["src/demo/**/*.{test,spec}.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      include: ["src/demo/**/*.{ts,tsx}"],
      exclude: [
        "src/demo/main.tsx",
        "src/demo/test/**",
        "src/demo/**/*.test.{ts,tsx}",
        "src/demo/vite-env.d.ts",
      ],
    },
  },
});
