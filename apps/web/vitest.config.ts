import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

/**
 * Vitest configuration for apps/web.
 *
 * Adds the first programmatic frontend test layer for ForgeMind.
 * Targets React 19 components under a jsdom environment with RTL.
 * Scope is intentionally narrow: component-level + pure-function tests.
 * Next.js route integration tests are out of scope for this pass.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["**/__tests__/**/*.{test,spec}.{ts,tsx}"],
    exclude: [
      "node_modules/**",
      ".next/**",
      "dist/**",
    ],
    css: false,
  },
});
