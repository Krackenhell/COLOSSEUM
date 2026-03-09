import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "::",
    port: 8080,
    hmr: {
      overlay: false,
    },
    proxy: {
      // Proxy API calls to Colosseum backend when VITE_API_BASE_URL is empty
      "/health": "http://localhost:8787",
      "/market-status": "http://localhost:8787",
      "/tournaments": "http://localhost:8787",
      "/gateway": "http://localhost:8787",
      "/agent-api": "http://localhost:8787",
      "/test-agent": "http://localhost:8787",
    },
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
