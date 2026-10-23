"use client";

import { useState, type FormEvent } from "react";

interface Props {
  cargando: boolean;
  onBuscar: (consulta: string) => void;
}

const SUGERENCIAS = ["café molido", "algo para el desayuno", "aseo del hogar", "bebidas frías"];

function IconoLupa({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={className} aria-hidden="true">
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
      <form onSubmit={enviar} role="search" className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <IconoLupa className="pointer-events-none absolute left-5 top-1/2 h-5 w-5 -translate-y-1/2 text-[#6B1020]/55" />
          <input
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            placeholder="Busca lo que necesitas: café molido, algo para el desayuno…"
            aria-label="Buscar productos"
            className="h-14 w-full rounded-full border border-white/30 bg-white pl-12 pr-12 text-base font-medium text-[#4A0B16] shadow-[0_12px_32px_rgba(0,0,0,0.16)] outline-none transition-all duration-300 ease-in-out placeholder:text-slate-500 focus:ring-4 focus:ring-amber-300/35"
          />
          {valor && (
            <button
              type="button"
              onClick={limpiar}
              aria-label="Limpiar búsqueda"
              className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full px-2 py-1 text-sm font-bold text-[#6B1020]/60 transition-all duration-200 hover:bg-[#F3E6D9] hover:text-[#6B1020] active:scale-95"
            >
              ✕
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={cargando}
          className="flex h-14 items-center justify-center gap-2 rounded-full bg-[#090909] px-8 font-semibold text-white shadow-[0_10px_30px_rgba(0,0,0,0.24)] transition-all duration-300 ease-in-out hover:-translate-y-1 hover:bg-[#191919] hover:shadow-[0_12px_34px_rgba(0,0,0,0.3)] active:scale-95 disabled:cursor-wait disabled:opacity-70 disabled:active:scale-100"
        >
          {cargando ? <IconoCarga className="h-5 w-5" /> : <IconoLupa className="h-5 w-5" />}
          <span>Buscar</span>
        </button>
      </form>

      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
        <span className="font-semibold text-white/80">Prueba con:</span>
        {SUGERENCIAS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => usarSugerencia(s)}
            className="rounded-[52px] border-2 border-white/70 bg-[#6B1020]/60 px-4 py-1 font-bold text-white backdrop-blur-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-white hover:text-[#6B1020] active:scale-95"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}


