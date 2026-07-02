import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Dev server on 5173 (the origin the api-gateway allows via CORS).
// The browser calls the gateway directly at VITE_API_BASE.
export default defineConfig({
  plugins: [react()],
  server: { host: "0.0.0.0", port: 5173, strictPort: true },
  preview: { host: "0.0.0.0", port: 5173, strictPort: true },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
  },
});
