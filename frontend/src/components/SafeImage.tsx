"use client";

import Image from "next/image";
import { useState, useCallback, useMemo } from "react";

export type ImageFallbackType = "producto" | "ingrediente" | "receta" | "general";

interface SafeImageProps {
  /** URL de la imagen (puede ser relativa, absoluta, o externa) */
  src?: string | null;
  /** Texto alternativo para accesibilidad */
  alt: string;
  /** Ancho en píxeles */
  width?: number;
  /** Alto en píxeles */
  height?: number;
  /** Tipo de fallback para elegir imagen de respaldo apropiada */
  fallbackType?: ImageFallbackType;
  /** Clases CSS adicionales */
  className?: string;
  /** Prioridad de carga (para imágenes above-the-fold) */
  priority?: boolean;
  /** Tamaños responsive (para fill) */
  sizes?: string;
  /** Calidad de la imagen (1-100) */
  quality?: number;
  /** Estilo del objeto (cover, contain, etc.) */
  objectFit?: "cover" | "contain" | "fill" | "none" | "scale-down";
  /** ID ARIA opcional */
  id?: string;
  /** Si usar fill (requiere padre con position relative) */
  fill?: boolean;
}

/**
 * Mapeo de tipos de fallback a URLs locales
 */
const FALLBACK_MAP: Record<ImageFallbackType, string> = {
  producto: "/img/fallback-producto.svg",
  ingrediente: "/img/fallback-ingrediente.svg",
  receta: "/img/fallback-receta.svg",
  general: "/img/fallback-general.svg",
};

/**
 * Máximo número de reintentos antes de rendirse (evita bucles infinitos)
 * 2 fallbacks * 1 intento cada uno = 2 intentos totales
 */
const MAX_RETRIES = 2;

/**
 * Normaliza una URL de imagen:
 * - Si es null/undefined/vacío -> undefined (usará fallback)
 * - Si es data URL (base64) -> permitir (self-contained)
 * - Si empieza con http/https -> validar dominio
 * - Si empieza con / -> mantener (local)
 * - Si no empieza con / ni http -> prepender /
 */
function normalizarSrc(src: string | null | undefined): string | undefined {
  if (!src || src.trim() === "") return undefined;

  const trimmed = src.trim();

  // Data URLs (base64 encoded) - permitir ya que son self-contained
  if (trimmed.startsWith("data:")) {
    return trimmed;
  }

  // Ya es URL absoluta
  if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
    return trimmed;
  }

  // Ya es ruta local absoluta
  if (trimmed.startsWith("/")) {
    return trimmed;
  }

  // Ruta relativa -> hacer absoluta
  return `/${trimmed}`;
}

/**
 * Verifica si una URL es de un dominio externo permitido
 * Actualmente no hay dominios externos permitidos - todo externo usa fallback
 * Data URLs se permiten ya que son self-contained
 */
function esDominioPermitido(src: string): boolean {
  // Data URLs son self-contained, no dependen de servicios externos
  if (src.startsWith("data:")) {
    return true;
  }
  // En el futuro se pueden agregar dominios CDN legítimos aquí
  // Por ahora: no permitir dominios externos para evitar dependencias
  return false;
}

/**
 * SafeImage - Componente de imagen seguro con fallback local automático
 *
 * Características:
 * - Usa Next.js Image para optimización
 * - Fallback automático a SVGs locales en /public/img/
 * - Manejo de errores sin bucles infinitos
 * - Tipos de fallback semánticos (producto, ingrediente, receta, general)
 * - Sin dependencia de placehold.co ni servicios externos
 */
export function SafeImage({
  src,
  alt,
  width = 100,
  height = 100,
  fallbackType = "general",
  className = "",
  priority = false,
  sizes,
  quality = 75,
  objectFit = "cover",
  id,
  fill = false,
}: SafeImageProps) {
  const [errorCount, setErrorCount] = useState(0);
  const [useFallback, setUseFallback] = useState(false);

  // Fallback actual (rotar entre intentos, máximo MAX_RETRIES)
  const currentFallback = useMemo(() => {
    // Si agotamos reintentos, usar fallback general definitivo
    if (errorCount >= MAX_RETRIES) {
      return FALLBACK_MAP.general;
    }
    const fallbacks = [
      FALLBACK_MAP[fallbackType],
      FALLBACK_MAP.general,
    ];
    return fallbacks[errorCount % fallbacks.length];
  }, [fallbackType, errorCount]);

  // Determinar src final
  const finalSrc = useMemo(() => {
    if (useFallback) return currentFallback;

    const normalized = normalizarSrc(src);
    if (!normalized) return currentFallback;

    // Si es externo y no está permitido, usar fallback
    if ((normalized.startsWith("http://") || normalized.startsWith("https://")) && !esDominioPermitido(normalized)) {
      return currentFallback;
    }

    return normalized;
  }, [src, useFallback, currentFallback, fallbackType]);

  // Manejar error de carga
  const handleError = useCallback(() => {
    setErrorCount((prev) => {
      const next = prev + 1;
      // Si ya agotamos los reintentos máximos, no seguimos intentando
      if (next >= MAX_RETRIES) {
        return prev; // No incrementar más
      }
      return next;
    });
    if (!useFallback) {
      setUseFallback(true);
    }
  }, [useFallback]);

  // Renderizar imagen con Next.js Image
  const imageProps = useMemo(() => {
    const baseProps = {
      src: finalSrc,
      alt,
      className,
      quality,
      onError: handleError,
      id,
      style: { objectFit } as React.CSSProperties,
    };

    if (fill) {
      return { ...baseProps, fill: true, sizes: sizes || "100vw" };
    }

    return { ...baseProps, width, height };
  }, [finalSrc, alt, className, quality, handleError, id, objectFit, fill, width, height, sizes]);

  return <Image {...imageProps} />;
}

/**
 * Hook para obtener URL de fallback por tipo (útil para casos especiales)
 */
export function getFallbackUrl(type: ImageFallbackType): string {
  return FALLBACK_MAP[type];
}

/**
 * Componente wrapper para imágenes de productos en catálogo
 */
export function SafeProductImage({ src, alt, ...props }: Omit<SafeImageProps, "fallbackType">) {
  return <SafeImage src={src} alt={alt} fallbackType="producto" {...props} />;
}

/**
 * Componente wrapper para imágenes de ingredientes/recetas
 */
export function SafeIngredientImage({ src, alt, ...props }: Omit<SafeImageProps, "fallbackType">) {
  return <SafeImage src={src} alt={alt} fallbackType="ingrediente" {...props} />;
}

/**
 * Componente wrapper para imágenes de recetas
 */
export function SafeRecipeImage({ src, alt, ...props }: Omit<SafeImageProps, "fallbackType">) {
  return <SafeImage src={src} alt={alt} fallbackType="receta" {...props} />;
}