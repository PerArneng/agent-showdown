import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  // Everything inlined into one index.html. Browsers refuse to load module scripts and
  // stylesheets from a file:// origin, so a multi-file build cannot be opened from disk --
  // and opening it from disk is what demo mode is for.
  base: "./",
  plugins: [viteSingleFile()],
  build: { outDir: "dist", emptyOutDir: true, assetsInlineLimit: Infinity },
});
