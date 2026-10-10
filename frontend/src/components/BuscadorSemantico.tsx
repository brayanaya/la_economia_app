"use client";

import { useState, type FormEvent } from "react";

interface Props {
  cargando: boolean;
  onBuscar: (consulta: string) => void;
}

const SUGERENCIAS = ["café molido", "algo para el desayuno", "aseo del hogar", "bebidas frías"];

function IconoLupa({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className={className} aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
  );
}

function IconoCarga({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={`animate-spin ${className ?? ""}`} aria-hidden="true">
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" className="opacity-25" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export default function BuscadorSemantico({ cargando, onBuscar }: Props) {
  const [valor, setValor] = useState("");

  function enviar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (cargando) return;
    onBuscar(valor.trim());
  }

  function usarSugerencia(sugerencia: string) {
    setValor(sugerencia);
    onBuscar(sugerencia);
  }

  function limpiar() {
    setValor("");
    onBuscar("");
  }

  return (
    <div>
      <form onSubmit={enviar} role="search" className="flex gap-3">
        <div className="relative flex-1">
          <IconoLupa className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
          <input
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            placeholder="Busca por lo que necesitas: café molido, algo para el desayuno…"
            aria-label="Buscar productos"
            className="h-14 w-full rounded-2xl border border-gray-200/80 bg-white pl-12 pr-12 text-base text-brand-dark shadow-md outline-none transition-all duration-200 placeholder:text-gray-400 focus:border-transparent focus:ring-2 focus:ring-brand-red"
          />
          {valor && (
            <button
              type="button"
              onClick={limpiar}
              aria-label="Limpiar búsqueda"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full px-2 py-1 text-sm text-gray-400 transition-all duration-200 hover:bg-gray-100 hover:text-brand-dark active:scale-95"
            >
              ✕
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={cargando}
          className="flex h-14 items-center gap-2 rounded-2xl bg-brand-red px-5 font-bold text-white shadow-md transition-all duration-200 hover:bg-brand-red/90 hover:shadow-lg active:scale-95 disabled:cursor-wait disabled:opacity-70 disabled:active:scale-100 sm:px-7"
        >
          {cargando ? <IconoCarga className="h-5 w-5" /> : <IconoLupa className="h-5 w-5" />}
          <span className="hidden sm:inline">Buscar</span>
        </button>
      </form>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-gray-500">Prueba con:</span>
        {SUGERENCIAS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => usarSugerencia(s)}
            className="rounded-full border border-gray-200/80 bg-white px-3 py-1 font-medium text-brand-dark/80 transition-all duration-200 hover:-translate-y-0.5 hover:border-brand-red/40 hover:text-brand-red active:scale-95"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
