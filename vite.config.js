import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
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
        start_url: "./",
        display: "standalone",
        background_color: "#0a0a0a",
        theme_color: "#0a0a0a",
        orientation: "any",
        scope: "./",
        icons: [
          {
            src: "icon-192.png",
            sizes: "192x192",
            type: "image/png",
            purpose: "any maskable",
          },
          {
            src: "icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        // Keep the complete reviewed event archive in the install cache so
        // Add to Home Screen remains useful without a network connection.
        globPatterns: ["**/*.{js,css,html,ico,png,svg,webp,json}"],
        navigateFallback: "index.html",
        runtimeCaching: [
          {
            urlPattern: /\/events\/index\.json$/,
            handler: "StaleWhileRevalidate",
            options: { cacheName: "comiket-event-index" },
          },
          {
            urlPattern: /\/events\/[^/]+\/(manifest|booths|artists)\.json$/,
            handler: "StaleWhileRevalidate",
            options: { cacheName: "comiket-event-data" },
          },
          {
            urlPattern: /\/events\/[^/]+\/maps\/.*\.webp$/,
            handler: "CacheFirst",
            options: { cacheName: "comiket-event-maps", expiration: { maxEntries: 40 } },
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
  },

  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
