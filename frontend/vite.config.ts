import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: { outDir: "dist", assetsDir: "static", emptyOutDir: true },
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000", "/fonts": "http://localhost:8000", "/assets": "http://localhost:8000" },
  },
});
