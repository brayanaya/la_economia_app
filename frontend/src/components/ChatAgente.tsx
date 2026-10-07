"use client";

import { useState } from "react";

type Mensaje = { rol: "usuario" | "asistente"; texto: string };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ChatAgente() {
  const [abierto, setAbierto] = useState(false);
  const [input, setInput] = useState("");
  const [cargando, setCargando] = useState(false);
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    { rol: "asistente", texto: "¡Hola! Soy tu asistente de compras. Cuéntame qué necesitas y te recomiendo productos." },
  ]);

  async function enviar() {
    const texto = input.trim();
    if (!texto || cargando) return;
    setInput("");
    setMensajes((m) => [...m, { rol: "usuario", texto }]);
    setCargando(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/agente/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensaje: texto }),
      });
      if (!res.ok) throw new Error(String(res.status));
      const data = await res.json();
      const respuesta = data.respuesta ?? data.response ?? data.message ?? "No pude generar una respuesta.";
      setMensajes((m) => [...m, { rol: "asistente", texto: String(respuesta) }]);
    } catch {
      setMensajes((m) => [...m, { rol: "asistente", texto: "No me pude conectar con el servidor. Intenta de nuevo." }]);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {abierto && (
        <div className="mb-3 flex h-[28rem] w-80 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/10">
          <div className="flex items-center justify-between bg-brand-red px-4 py-3 text-white">
            <span className="font-bold">🤖 Asistente RAG</span>
            <button onClick={() => setAbierto(false)} aria-label="Cerrar" className="text-xl leading-none">×</button>
          </div>

          <div className="bg-brand-yellow px-3 py-1 text-[11px] font-medium text-brand-dark">
            Recomendaciones procesadas en tiempo real por un modelo local (Ollama qwen2.5:7b + pgvector).
          </div>

          <div className="flex-1 space-y-2 overflow-y-auto bg-brand-bg p-3">
            {mensajes.map((m, i) => (
              <div
                key={i}
                className={`max-w-[85%] whitespace-pre-wrap rounded-xl px-3 py-2 text-sm ${
                  m.rol === "usuario" ? "ml-auto bg-brand-red text-white" : "bg-white text-brand-dark shadow-sm"
                }`}
              >
                {m.texto}
              </div>
            ))}
            {cargando && <div className="text-xs text-gray-500">Pensando…</div>}
          </div>

          <div className="flex gap-2 border-t border-gray-200 bg-white p-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && enviar()}
              placeholder="¿Qué buscas hoy?"
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-brand-dark outline-none focus:border-brand-red"
            />
            <button
              onClick={enviar}
              disabled={cargando}
              className="rounded-lg bg-brand-green px-3 text-sm font-bold text-white hover:bg-brand-green-dark disabled:opacity-50"
            >
              Enviar
            </button>
          </div>
        </div>
      )}

      <button
        onClick={() => setAbierto((v) => !v)}
        className="ml-auto flex h-14 w-14 items-center justify-center rounded-full border-2 border-brand-yellow bg-brand-red text-2xl shadow-lg transition hover:bg-brand-red-dark"
        aria-label="Abrir asistente"
      >
        💬
      </button>
    </div>
  );
}