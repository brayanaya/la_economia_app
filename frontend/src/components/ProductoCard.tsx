"use client";

import { useEffect, useRef, useState } from "react";

type Props = {
  nombre: string;
  precio: number;
  imagen?: string;
  sede: string;
  stock: number;
  /** Similitud pgvector, 0 a 1. Solo en resultados RAG. */
  similitud?: number;
  /** Devuelve false si no se pudo agregar (ej. sin sede elegida). */
  onAgregar?: () => void | boolean;
};

const cop = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

export default function ProductoCard({ nombre, precio, imagen, sede, stock, similitud, onAgregar }: Props) {
  const disponible = stock > 0;
  const [agregado, setAgregado] = useState(false);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (temporizador.current) clearTimeout(temporizador.current);
    };
  }, []);

  function manejarClick() {
    if (!disponible) return;
    const resultado = onAgregar?.();
    if (resultado === false) return;
    setAgregado(true);
    if (temporizador.current) clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => setAgregado(false), 1400);
  }

  return (
    <article className="anim-aparecer group relative flex flex-col rounded-[25px] border-2 border-[#3f0791] bg-white p-4 transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#3f0791]">
      {similitud !== undefined && (
        <span className="absolute left-5 top-5 z-10 rounded-[52px] bg-[#e30ba6] px-3 py-1 text-[11px] font-black text-white">
          🎯 {Math.round(similitud * 100)}% coincidencia
        </span>
      )}

      <div className="mb-3 flex h-40 items-center justify-center overflow-hidden rounded-[18px] bg-[#dad9ff]">
        {imagen ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imagen}
            alt={nombre}
            className="h-full w-full object-contain transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <span className="text-4xl">🛒</span>
        )}
      </div>

      <h3 className="line-clamp-2 min-h-10 text-sm font-bold leading-snug text-[#3f0791]">{nombre}</h3>
      <p className="mt-2 text-2xl font-black leading-none tracking-tight text-[#3f0791]">{cop.format(precio)}</p>

      <p className={`mt-2 text-xs font-bold ${disponible ? "text-emerald-700" : "text-[#e30ba6]"}`}>
        {disponible ? `● ${stock} disponibles en ${sede}` : `● Agotado en ${sede}`}
      </p>

      <button
        type="button"
        onClick={manejarClick}
        disabled={!disponible}
        className={`mt-3 w-full rounded-[52px] border-2 py-2.5 text-sm font-black text-white transition-all duration-200 active:scale-95 disabled:cursor-not-allowed disabled:border-gray-300 disabled:bg-gray-300 disabled:active:scale-100 ${
          agregado
            ? "border-emerald-600 bg-emerald-600"
            : "border-[#3f0791] bg-[#3f0791] hover:border-[#5b00ed] hover:bg-[#5b00ed]"
        }`}
      >
        {agregado ? "¡Agregado! ✓" : "Agregar al carrito"}
      </button>
    </article>
  );
}
