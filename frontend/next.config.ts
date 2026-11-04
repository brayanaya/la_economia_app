import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  devIndicators: false,
  // cacheComponents and partialPrefetching disabled due to incompatibility with dynamic routes using client components
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  images: {
    // Solo se permiten imágenes locales (/public) y dominios explícitamente configurados
    // No se usan dominios externos - las imágenes externas usan fallback local
    remotePatterns: [],
    // Formatos modernos para mejor compresión
    formats: ["image/avif", "image/webp"],
    // Tamaños de dispositivo para responsive images
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
};

export default nextConfig;
