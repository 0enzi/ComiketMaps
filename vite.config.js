import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "fs";
import path from "path";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  base: "/ComiketMaps/",
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "Comiket Map Viewer",
        short_name: "Comiket Maps",
        description: "Zoomable maps for Comiket events",
        start_url: "/",
        display: "standalone",
        background_color: "#0a0a0a",
        theme_color: "#0a0a0a",
        orientation: "landscape",
        scope: "/",
        icons: [
          {
            src: "/icon-192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any maskable",
          },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
    }),
  ],

  // tells Vite where your static files are
  publicDir: "public",

  server: {
    host: "0.0.0.0",
    port: 5173,
    hmr: {
      host: "localhost",
      protocol: "wss",
    },
  },

  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
