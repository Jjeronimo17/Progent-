import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// En desarrollo, /api va a la API de FastAPI (puerto 8000). Así la cookie de sesión
// es del mismo origen y no hace falta CORS para el navegador.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: { "/api": { target: process.env.PROGENT_API ?? "http://localhost:8000", changeOrigin: true } },
  },
  preview: {
    port: 4173,
    proxy: { "/api": { target: process.env.PROGENT_API ?? "http://localhost:8000", changeOrigin: true } },
  },
});
