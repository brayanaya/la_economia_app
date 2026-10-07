"use client";

import { useState } from "react";

type Props = {
  cargando: boolean;
  onBuscar: (consulta: string) => void;
};

export default function BuscadorSemantico({ cargando, onBuscar }: Props) {
  const [texto, setTexto] = useState("");

  function enviar(e: React.FormEvent) {
    e.preventDefault();
    const q = texto.trim();
    if (q && !cargando) onBuscar(q);
  }

  return (
    <form onSubmit={enviar} className="flex gap-2">
      <input
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        placeholder="Busca por lo que necesitas: café molido, algo para el desayuno..."
        className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm text-brand-dark outline-none focus:border-brand-red"
      />
      <button
        type="submit"
        disabled={cargando}
        className="flex min-w-28 items-center justify-center gap-2 rounded-lg bg-brand-red px-5 py-3 text-sm font-bold text-white transition hover:bg-brand-red-dark disabled:opacity-60"
      >
        {cargando ? (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
        ) : (
          "🔍 Buscar"
        )}
      </button>
    </form>
  );
}