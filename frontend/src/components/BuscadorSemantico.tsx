"use client";

import { useState, type FormEvent, useEffect, useRef, useCallback } from "react";
import { buscarSemantica, type Producto } from "@/lib/api";

interface Props {
  cargando: boolean;
  onBuscar: (consulta: string) => void;
  sedeId?: string | null;
}

const SUGERENCIAS_ESTATICAS = ["café molido", "algo para el desayuno", "aseo del hogar", "bebidas frías"];

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

function IconoVector({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className={className} aria-hidden="true">
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
    </svg>
  );
}

export default function BuscadorSemantico({ cargando, onBuscar, sedeId }: Props) {
  const [valor, setValor] = useState("");
  const [sugerenciasVectoriales, setSugerenciasVectoriales] = useState<Producto[]>([]);
  const [mostrarSugerencias, setMostrarSugerencias] = useState(false);
  const [buscandoSugerencias, setBuscandoSugerencias] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function enviar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (cargando) return;
    onBuscar(valor.trim());
    setMostrarSugerencias(false);
  }

  function usarSugerencia(sugerencia: string) {
    setValor(sugerencia);
    onBuscar(sugerencia);
    setMostrarSugerencias(false);
  }

  function usarProducto(p: Producto) {
    const texto = p.nombre;
    setValor(texto);
    onBuscar(texto);
    setMostrarSugerencias(false);
  }

  function limpiar() {
    setValor("");
    setSugerenciasVectoriales([]);
    setMostrarSugerencias(false);
    onBuscar("");
  }

  const buscarSugerencias = useCallback(async (consulta: string) => {
    if (consulta.length < 2) {
      setSugerenciasVectoriales([]);
      return;
    }
    setBuscandoSugerencias(true);
    try {
      const resultados = await buscarSemantica(consulta, sedeId ?? null, 5);
      setSugerenciasVectoriales(resultados.slice(0, 4));
    } catch {
      setSugerenciasVectoriales([]);
    } finally {
      setBuscandoSugerencias(false);
    }
  }, [sedeId]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const nuevoValor = e.target.value;
    setValor(nuevoValor);
    setMostrarSugerencias(true);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      buscarSugerencias(nuevoValor);
    }, 300);
  }

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setMostrarSugerencias(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return (
    <div className="relative" ref={inputRef}>
      <form onSubmit={enviar} role="search" className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <IconoLupa className="pointer-events-none absolute left-5 top-1/2 h-5 w-5 -translate-y-1/2 text-[#3f0791]/60" />
          <input
            value={valor}
            onChange={handleChange}
            onFocus={() => valor.length >= 2 && setMostrarSugerencias(true)}
            placeholder="Busca lo que necesitas: café molido, algo para el desayuno…"
            aria-label="Buscar productos"
            aria-expanded={mostrarSugerencias && (sugerenciasVectoriales.length > 0 || SUGERENCIAS_ESTATICAS.length > 0)}
            aria-controls="sugerencias-list"
            className="h-14 w-full rounded-[52px] border-2 border-[#3f0791] bg-white pl-12 pr-12 text-base font-medium text-[#3f0791] shadow-lg outline-none transition-all duration-200 placeholder:text-[#3f0791]/70 focus:ring-4 focus:ring-white/60"
          />
          {valor && (
            <button
              type="button"
              onClick={limpiar}
              aria-label="Limpiar búsqueda"
              className="absolute right-4 top-1/2 -translate-y-1/2 rounded-full px-2 py-1 text-sm font-bold text-[#3f0791]/60 transition-all duration-200 hover:bg-[#dad9ff] hover:text-[#3f0791] active:scale-95"
            >
              ✕
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={cargando}
          className="flex h-14 items-center justify-center gap-2 rounded-[52px] border-2 border-[#3f0791] bg-[#3f0791] px-8 font-black text-white shadow-lg transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#2f0570] active:scale-95 disabled:cursor-wait disabled:opacity-70 disabled:active:scale-100"
        >
          {cargando ? <IconoCarga className="h-5 w-5" /> : <IconoLupa className="h-5 w-5" />}
          <span>Buscar</span>
        </button>
      </form>

      {mostrarSugerencias && !cargando && (
        <div
          id="sugerencias-list"
          className="absolute z-10 mt-2 w-full max-h-60 overflow-y-auto rounded-[18px] border-2 border-[#3f0791] bg-white shadow-[6px_6px_0_0_#3f0791]"
          role="listbox"
        >
          {buscandoSugerencias && (
            <div className="flex items-center justify-center gap-2 px-4 py-3 text-[#3f0791]/70">
              <IconoCarga className="h-4 w-4" />
              <span className="text-sm font-medium">Buscando sugerencias vectoriales…</span>
            </div>
          )}

          {sugerenciasVectoriales.length > 0 && (
            <div className="p-2 border-b border-[#3f0791]/20">
              <p className="px-3 py-1 text-xs font-black uppercase tracking-wider text-[#3f0791]/60">
                <IconoVector className="inline h-3 w-3 mr-1" /> Sugerencias IA
              </p>
              {sugerenciasVectoriales.map((p, i) => (
                <button
                  key={`${p.id}-${i}`}
                  type="button"
                  onClick={() => usarProducto(p)}
                  role="option"
                  className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium text-[#3f0791] rounded-[12px] hover:bg-[#dad9ff] transition-colors duration-150"
                >
                  <span className="flex-1 text-left truncate">{p.nombre}</span>
                  <span className="shrink-0 text-xs font-bold text-[#e30ba6]">
                    {new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(p.precio)}
                  </span>
                  {p.similitud !== undefined && (
                    <span className="shrink-0 text-[10px] font-medium text-[#3f0791]/50">
                      {Math.round(p.similitud * 100)}%
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          {SUGERENCIAS_ESTATICAS.length > 0 && (
            <div className="p-2">
              <p className="px-3 py-1 text-xs font-black uppercase tracking-wider text-[#3f0791]/60">
                Prueba con:
              </p>
              {SUGERENCIAS_ESTATICAS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => usarSugerencia(s)}
                  role="option"
                  className="w-full px-3 py-2 text-xs font-bold text-[#3f0791] rounded-[12px] hover:bg-[#dad9ff] transition-colors duration-150 text-left"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {sugerenciasVectoriales.length === 0 && !buscandoSugerencias && valor.length >= 2 && (
            <div className="px-4 py-3 text-center text-sm text-[#3f0791]/60">
              No hay sugerencias vectoriales para esta búsqueda
            </div>
          )}
        </div>
      )}

      {!mostrarSugerencias && SUGERENCIAS_ESTATICAS.length > 0 && (
        <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
          <span className="font-semibold text-white/80">Prueba con:</span>
          {SUGERENCIAS_ESTATICAS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => usarSugerencia(s)}
              className="rounded-[52px] border-2 border-white/70 bg-[#3f0791]/60 px-4 py-1 font-bold text-white backdrop-blur-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-white hover:text-[#3f0791] active:scale-95"
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}