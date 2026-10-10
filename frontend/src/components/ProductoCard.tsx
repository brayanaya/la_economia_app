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
    <article className="group relative flex flex-col rounded-2xl border border-black/5 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
      {similitud !== undefined && (
        <span className="absolute left-3 top-3 z-10 rounded-full bg-brand-yellow px-2 py-1 text-[11px] font-bold text-brand-dark">
          🎯 {Math.round(similitud * 100)}% coincidencia
        </span>
      )}

      <div className="mb-3 flex h-40 items-center justify-center overflow-hidden rounded-xl bg-brand-bg">
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

      <h3 className="line-clamp-2 min-h-10 text-sm font-semibold text-brand-dark">{nombre}</h3>
      <p className="mt-2 text-xl font-extrabold text-brand-red">{cop.format(precio)}</p>

      <p className={`mt-1 text-xs font-medium ${disponible ? "text-brand-green" : "text-brand-red"}`}>
        {disponible ? `● ${stock} disponibles en ${sede}` : `● Agotado en ${sede}`}
      </p>

      <button
        type="button"
        onClick={manejarClick}
        disabled={!disponible}
        className={`mt-3 w-full rounded-xl py-2 text-sm font-bold text-white transition-all duration-200 active:scale-95 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:active:scale-100 ${
          agregado ? "bg-emerald-600" : "bg-brand-green hover:bg-brand-green-dark"
        }`}
      >
        {agregado ? "¡Agregado! ✓" : "Agregar al carrito"}
      </button>
    </article>
  );
}

