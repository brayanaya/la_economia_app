"use client";

import { useEffect, useRef, useState } from "react";
import { chatear, type Producto } from "@/lib/api";
import { useCarrito } from "@/context/CarritoContext";
import { mostrarAviso } from "@/lib/aviso";

type Mensaje = { rol: "usuario" | "asistente"; texto: string; productos?: Producto[] };

type Props = {
  sedeId: string | null;
  onAgregar?: (p: Producto) => void;
};

const cop = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

export default function ChatAgente({ sedeId, onAgregar }: Props) {
  const { agregar } = useCarrito();
  const [abierto, setAbierto] = useState(false);
  const [input, setInput] = useState("");
  const [cargando, setCargando] = useState(false);
  const [agregadoKey, setAgregadoKey] = useState<string | null>(null);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    { rol: "asistente", texto: "¡Hola! Soy tu asistente de compras. Cuéntame qué necesitas y te recomiendo productos." },
  ]);

  useEffect(() => {
    return () => {
      if (temporizador.current) clearTimeout(temporizador.current);
    };
  }, []);

  function agregarDesdeChat(p: Producto, clave: string) {
    if (sedeId === null) {
      mostrarAviso("Elige una sede para agregar productos desde el chat.");
      return;
    }
    agregar({
      productoId: String(p.id),
      nombre: p.nombre,
      precio: p.precio,
      sedeId,
      imagen: p.imagen ?? undefined,
    });
    mostrarAviso(`${p.nombre} agregado al carrito.`);
    setAgregadoKey(clave);
    if (temporizador.current) clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => setAgregadoKey(null), 1400);
    onAgregar?.(p);
  }

  async function enviar() {
    const texto = input.trim();
    if (!texto || cargando) return;
    setInput("");
    setMensajes((m) => [...m, { rol: "usuario", texto }]);
    setCargando(true);
    try {
      const { respuesta, productos } = await chatear(texto, sedeId);
      setMensajes((m) => [...m, { rol: "asistente", texto: respuesta, productos }]);
    } catch {
      setMensajes((m) => [
        ...m,
        { rol: "asistente", texto: "No me pude conectar con el servidor. Intenta de nuevo." },
      ]);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {abierto && (
        <div className="mb-3 flex h-[32rem] w-80 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/10 sm:w-96">
          <div className="flex items-center justify-between bg-brand-red px-4 py-3 text-white">
            <span className="font-bold">🤖 Asistente RAG</span>
            <button onClick={() => setAbierto(false)} aria-label="Cerrar" className="text-xl leading-none">×</button>
          </div>

          <div className="bg-brand-yellow px-3 py-1 text-[11px] font-medium text-brand-dark">
            Recomendaciones procesadas en tiempo real por un modelo local (Ollama qwen2.5:7b + pgvector).
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto bg-brand-bg p-3">
            {mensajes.map((m, i) => (
              <div key={i} className={m.rol === "usuario" ? "flex justify-end" : "flex justify-start"}>
                <div className="max-w-[90%] space-y-2">
                  <div
                    className={`whitespace-pre-wrap rounded-xl px-3 py-2 text-sm ${
                      m.rol === "usuario" ? "bg-brand-red text-white" : "bg-white text-brand-dark shadow-sm"
                    }`}
                  >
                    {m.texto}
                  </div>

                  {m.productos?.map((p, j) => {
                    const clave = `${i}-${j}`;
                    const agregado = agregadoKey === clave;
                    return (
                      <div
                        key={`${p.id}-${j}`}
                        className="flex items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white p-2 shadow-sm"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-xs font-semibold text-brand-dark">{p.nombre}</p>
                          <p className="text-sm font-extrabold text-brand-red">{cop.format(p.precio)}</p>
                        </div>
                        <button
                          onClick={() => agregarDesdeChat(p, clave)}
                          disabled={p.stock <= 0}
                          className={`shrink-0 rounded-md px-2 py-1 text-[11px] font-bold text-white transition-all duration-200 active:scale-95 disabled:bg-gray-300 disabled:active:scale-100 ${
                            agregado ? "bg-emerald-600" : "bg-brand-green hover:bg-brand-green-dark"
                          }`}
                        >
                          {p.stock <= 0 ? "Agotado" : agregado ? "¡Agregado! ✓" : "Agregar al carrito"}
                        </button>
                      </div>
                    );
                  })}
                </div>
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
