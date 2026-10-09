// carrito-v1
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface ItemCarrito {
  productoId: string;
  nombre: string;
  precio: number;
  cantidad: number;
  sedeId: string;
  sedeNombre?: string;
  imagen?: string;
}

interface CarritoContextValue {
  items: ItemCarrito[];
  hidratado: boolean;
  abierto: boolean;
  totalItems: number;
  totalPrecio: number;
  abrir: () => void;
  cerrar: () => void;
  agregar: (item: Omit<ItemCarrito, "cantidad">, cantidad?: number) => void;
  cambiarCantidad: (productoId: string, sedeId: string, cantidad: number) => void;
  quitar: (productoId: string, sedeId: string) => void;
  vaciarSede: (sedeId: string) => void;
  vaciar: () => void;
}

const STORAGE_KEY = "la_economia_carrito_v1";
const MAX_CANTIDAD = 99;

const CarritoContext = createContext<CarritoContextValue | null>(null);

function esItem(x: unknown): x is ItemCarrito {
  if (typeof x !== "object" || x === null) return false;
  const o = x as Record<string, unknown>;
  return (
    typeof o.productoId === "string" &&
    typeof o.nombre === "string" &&
    typeof o.precio === "number" &&
    Number.isFinite(o.precio) &&
    typeof o.cantidad === "number" &&
    o.cantidad >= 1 &&
    typeof o.sedeId === "string"
  );
}

export function CarritoProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ItemCarrito[]>([]);
  const [hidratado, setHidratado] = useState(false);
  const [abierto, setAbierto] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const data: unknown = JSON.parse(raw);
        if (Array.isArray(data)) setItems(data.filter(esItem));
      }
    } catch {
      /* storage no disponible o JSON corrupto */
    }
    setHidratado(true);
  }, []);

  useEffect(() => {
    if (!hidratado) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    } catch {
      /* cuota o modo privado */
    }
  }, [items, hidratado]);

  const agregar = useCallback((item: Omit<ItemCarrito, "cantidad">, cantidad = 1) => {
    const productoId = String(item.productoId);
    const cant = Math.min(MAX_CANTIDAD, Math.max(1, Math.floor(cantidad)));
    setItems((prev) => {
      const idx = prev.findIndex((i) => i.productoId === productoId && i.sedeId === item.sedeId);
      if (idx >= 0) {
        const copia = [...prev];
        copia[idx] = { ...copia[idx], cantidad: Math.min(MAX_CANTIDAD, copia[idx].cantidad + cant) };
        return copia;
      }
      return [...prev, { ...item, productoId, cantidad: cant }];
    });
  }, []);

  const cambiarCantidad = useCallback((productoId: string, sedeId: string, cantidad: number) => {
    setItems((prev) =>
      cantidad < 1
        ? prev.filter((i) => !(i.productoId === productoId && i.sedeId === sedeId))
        : prev.map((i) =>
            i.productoId === productoId && i.sedeId === sedeId
              ? { ...i, cantidad: Math.min(MAX_CANTIDAD, Math.floor(cantidad)) }
              : i,
          ),
    );
  }, []);

  const quitar = useCallback((productoId: string, sedeId: string) => {
    setItems((prev) => prev.filter((i) => !(i.productoId === productoId && i.sedeId === sedeId)));
  }, []);

  const vaciarSede = useCallback((sedeId: string) => {
    setItems((prev) => prev.filter((i) => i.sedeId !== sedeId));
  }, []);

  const vaciar = useCallback(() => setItems([]), []);
  const abrir = useCallback(() => setAbierto(true), []);
  const cerrar = useCallback(() => setAbierto(false), []);

  const totalItems = useMemo(() => items.reduce((a, i) => a + i.cantidad, 0), [items]);
  const totalPrecio = useMemo(() => items.reduce((a, i) => a + i.precio * i.cantidad, 0), [items]);

  const value = useMemo<CarritoContextValue>(
    () => ({
      items, hidratado, abierto, totalItems, totalPrecio,
      abrir, cerrar, agregar, cambiarCantidad, quitar, vaciarSede, vaciar,
    }),
    [items, hidratado, abierto, totalItems, totalPrecio, abrir, cerrar, agregar, cambiarCantidad, quitar, vaciarSede, vaciar],
  );

  return <CarritoContext.Provider value={value}>{children}</CarritoContext.Provider>;
}

export function useCarrito(): CarritoContextValue {
  const ctx = useContext(CarritoContext);
  if (!ctx) throw new Error("useCarrito debe usarse dentro de <CarritoProvider>");
  return ctx;
}
