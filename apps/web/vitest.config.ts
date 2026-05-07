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
    exclude: ["node_modules/**", ".next/**", "dist/**"],
    css: false,
    coverage: {
      // v8 is the default provider in Vitest 3+ and doesn't require an
      // additional dev dep — keeps the install footprint small.
      provider: "v8",
      reporter: ["text", "text-summary", "json-summary", "html"],
      reportsDirectory: "./coverage",
      // Scope coverage collection to the actual source we ship. The UI
      // app, lib clients, and components form the meaningful surface.
      include: ["app/**", "components/**", "lib/**"],
      exclude: [
        "**/__tests__/**",
        "**/*.d.ts",
        "app/**/layout.tsx",
        "app/**/loading.tsx",
        "app/**/not-found.tsx",
        "app/**/error.tsx",
        "app/**/page.tsx",
      ],
      // Soft thresholds — set intentionally low so the pipeline doesn't
      // flake on incidental coverage dips; tighten over time.
      thresholds: {
        lines: 20,
        statements: 20,
        functions: 25,
        branches: 40,
      },
    },
  },
});
