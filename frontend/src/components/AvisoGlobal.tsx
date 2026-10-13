"use client";

import { useCallback, useEffect, useState } from "react";
import { EVENTO_AVISO } from "@/lib/aviso";

interface Aviso {
  id: number;
  mensaje: string;
}

const DURACION_MS = 3500;
const SALIDA_MS = 250;

function Toast({ aviso, onCerrar }: { aviso: Aviso; onCerrar: (id: number) => void }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const entrada = requestAnimationFrame(() => setVisible(true));
    const salida = setTimeout(() => setVisible(false), DURACION_MS);
    const retirar = setTimeout(() => onCerrar(aviso.id), DURACION_MS + SALIDA_MS);
    return () => {
      cancelAnimationFrame(entrada);
      clearTimeout(salida);
      clearTimeout(retirar);
    };
  }, [aviso.id, onCerrar]);

  return (
    <div
      role="status"
      className={`pointer-events-auto flex max-w-sm items-start gap-3 rounded-2xl border border-black/5 bg-brand-dark px-4 py-3 text-sm text-white shadow-lg transition-all duration-200 ${
        visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
      }`}
    >
      <span aria-hidden className="mt-1 h-2 w-2 shrink-0 rounded-full bg-brand-yellow" />
      <p className="flex-1 leading-snug">{aviso.mensaje}</p>
      <button
        type="button"
        onClick={() => onCerrar(aviso.id)}
        aria-label="Cerrar aviso"
        className="-mr-1 rounded-md px-1.5 text-white/60 transition-colors hover:text-white active:scale-95"
      >
        ✕
      </button>
    </div>
  );
}

export default function AvisoGlobal() {
  const [avisos, setAvisos] = useState<Aviso[]>([]);

  const quitar = useCallback((id: number) => {
    setAvisos((actuales) => actuales.filter((a) => a.id !== id));
  }, []);

  useEffect(() => {
    let contador = 0;
    function alAviso(evento: Event) {
      const mensaje = (evento as CustomEvent<string>).detail;
      if (!mensaje) return;
      contador += 1;
      const id = Date.now() + contador;
      setAvisos((actuales) => [...actuales.slice(-2), { id, mensaje }]);
    }
    window.addEventListener(EVENTO_AVISO, alAviso);
    return () => window.removeEventListener(EVENTO_AVISO, alAviso);
  }, []);

  return (
    <div
      aria-live="polite"
      className="pointer-events-none fixed inset-x-0 bottom-4 z-[100] flex flex-col items-center gap-2 px-4"
    >
      {avisos.map((aviso) => (
        <Toast key={aviso.id} aviso={aviso} onCerrar={quitar} />
      ))}
    </div>
  );
}
