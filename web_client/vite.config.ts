import { defineConfig } from "vite";

export default defineConfig({
  // Relative asset URLs, so the build also works when index.html is opened straight from disk.
  // Demo mode depends on that.
  base: "./",
  build: { outDir: "dist", emptyOutDir: true },
});
