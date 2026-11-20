import { defineConfig } from "vite";

// Static site: relative base so dist/ can be served from any folder; no runtime fetches.
export default defineConfig({
  base: "./",
  build: { outDir: "dist", assetsInlineLimit: 0, chunkSizeWarningLimit: 4000 },
});
