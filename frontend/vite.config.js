import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const headers = env.APP_API_KEY
    ? { Authorization: `Bearer ${env.APP_API_KEY}` }
    : {};

  return {
    server: {
      proxy: {
        "/api": {
          target: env.BACKEND_URL || "http://127.0.0.1:8000",
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
          headers,
        },
      },
    },
  };
});
