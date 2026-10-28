"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Send, X } from "lucide-react";
import { chatear, type MensajeHistorial, type Producto } from "@/lib/api";
import { useCarrito } from "@/context/CarritoContext";
import { mostrarAviso } from "@/lib/aviso";

type Mensaje = {
  rol: "usuario" | "asistente";
  texto: string;
  productos?: Producto[];
  generadoPorLlm?: boolean;
};

type Props = {
  sedeId: string | null;
  onAgregar?: (p: Producto) => void;
};

const SUGERENCIAS = [
  "¿Qué puedo hacer de desayuno?",
  "¿Cómo hago huevos pericos?",
  "Algo dulce para la tarde",
  "¿Cómo puedo pagar?",
];

// Clases completas (no interpoladas) para que Tailwind las detecte.
const RETARDOS_PUNTOS = ["[animation-delay:0ms]", "[animation-delay:150ms]", "[animation-delay:300ms]"];

const cop = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

export default function ChatAgente({ sedeId, onAgregar }: Props) {
  const { agregar } = useCarrito();
  const [abierto, setAbierto] = useState(false);
  const [input, setInput] = useState("");
  const [cargando, setCargando] = useState(false);
  const [agregadoKey, setAgregadoKey] = useState<string | null>(null);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);
  const contenedor = useRef<HTMLDivElement | null>(null);
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    {
      rol: "asistente",
      texto: "¡Hola! Soy el asistente de La Economía Aya. Pregúntame por productos, precios o ideas para tu desayuno.",
      generadoPorLlm: true,
    },
  ]);

  useEffect(() => {
    return () => {
      if (temporizador.current) clearTimeout(temporizador.current);
    };
  }, []);

  useEffect(() => {
    const el = contenedor.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [mensajes, cargando]);

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
      categoria: p.categoria,
    });
    mostrarAviso(`${p.nombre} agregado al carrito.`);
    setAgregadoKey(clave);
    if (temporizador.current) clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => setAgregadoKey(null), 1400);
    onAgregar?.(p);
  }

  async function enviar(textoPrefijado?: string) {
    const texto = (textoPrefijado ?? input).trim();
    if (!texto || cargando) return;
    setInput("");
    // El asistente recuerda la conversacion: se envian los ultimos 8 turnos.
    const historial: MensajeHistorial[] = mensajes
      .slice(-8)
      .map((m) => ({ rol: m.rol, texto: m.texto }));
    setMensajes((m) => [...m, { rol: "usuario", texto }]);
    setCargando(true);
    try {
      const { respuesta, productos, generadoPorLlm } = await chatear(texto, sedeId, historial);
      setMensajes((m) => [...m, { rol: "asistente", texto: respuesta, productos, generadoPorLlm }]);
    } catch (error) {
      const textoError = error instanceof TypeError
        ? "No hay conexión con el servicio de compras. Comprueba que la API esté activa e inténtalo de nuevo."
        : "El servicio de recomendaciones no pudo responder ahora. Inténtalo de nuevo en un momento.";
      setMensajes((m) => [
        ...m,
        { rol: "asistente", texto: textoError, generadoPorLlm: false },
      ]);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {abierto && (
        <div className="anim-drawer mb-3 flex h-[calc(100dvh-6rem)] max-h-[34rem] w-[calc(100vw-2rem)] max-w-[24rem] flex-col overflow-hidden rounded-3xl bg-[#1C0709]/95 shadow-[0_24px_60px_rgba(24,3,7,0.5)] ring-1 ring-white/10 backdrop-blur-xl">
          <div className="flex items-center justify-between bg-gradient-to-r from-[#570008] to-[#7A0A18] px-4 py-3.5 text-white">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/15 ring-1 ring-white/20">
                <Bot className="h-5 w-5 text-amber-300" aria-hidden="true" />
              </span>
              <div>
                <p className="text-sm font-bold leading-tight">Asistente de compras</p>
                <p className="flex items-center gap-1.5 text-[11px] font-medium text-white/70">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
                  en línea · recomienda y ayuda
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setAbierto(false)}
              aria-label="Cerrar asistente"
              className="rounded-full p-1.5 text-white/80 transition hover:bg-white/10 hover:text-white"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>

          <div ref={contenedor} className="flex-1 space-y-3 overflow-y-auto bg-[#140407] p-3">
            {mensajes.map((m, i) => (
              <div key={i} className={m.rol === "usuario" ? "flex justify-end" : "flex justify-start"}>
                <div className="max-w-[90%] space-y-2">
                  <div
                    className={`whitespace-pre-wrap rounded-2xl px-3.5 py-2 text-sm leading-relaxed ${
                      m.rol === "usuario"
                        ? "rounded-br-md bg-[#C8102E] text-white"
                        : "rounded-bl-md bg-white/10 text-white ring-1 ring-white/10"
                    }`}
                  >
                    {m.texto}
                  </div>

                  {m.rol === "asistente" && m.generadoPorLlm === false && (
                    <p className="px-1 text-[10px] font-medium text-amber-300/70">
                      modo básico · la IA principal no respondió
                    </p>
                  )}

                  {m.productos?.map((p, j) => {
                    const clave = `${i}-${j}`;
                    const agregado = agregadoKey === clave;
                    return (
                      <div
                        key={`${p.id}-${j}`}
                        className="flex items-center gap-2.5 rounded-xl bg-white/10 p-2 ring-1 ring-white/10"
                      >
                        <span className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-white">
                          {p.imagen ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={p.imagen} alt="" className="h-full w-full object-contain" />
                          ) : (
                            <span className="text-lg" aria-hidden="true">🛒</span>
                          )}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-xs font-semibold text-white">{p.nombre}</p>
                          <p className="text-sm font-extrabold text-amber-300">{cop.format(p.precio)}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => agregarDesdeChat(p, clave)}
                          disabled={p.stock <= 0}
                          className={`shrink-0 rounded-full px-2.5 py-1.5 text-[11px] font-bold text-white transition-all duration-200 active:scale-95 disabled:bg-white/20 disabled:text-white/40 disabled:active:scale-100 ${
                            agregado ? "bg-emerald-600" : "bg-brand-green hover:bg-brand-green-dark"
                          }`}
                        >
                          {p.stock <= 0 ? "Agotado" : agregado ? "¡Agregado! ✓" : "Agregar"}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}

            {cargando && (
              <div className="flex justify-start">
                <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md bg-white/10 px-4 py-3 ring-1 ring-white/10">
                  {RETARDOS_PUNTOS.map((retardo) => (
                    <span key={retardo} aria-hidden="true" className={`h-1.5 w-1.5 animate-bounce rounded-full bg-amber-300/80 ${retardo}`} />
                  ))}
                </div>
              </div>
            )}
          </div>

          {mensajes.length <= 2 && !cargando && (
            <div className="flex gap-2 overflow-x-auto border-t border-white/10 bg-[#160409]/95 px-3 py-2 [scrollbar-width:none]">
              {SUGERENCIAS.map((sugerencia) => (
                <button
                  key={sugerencia}
                  type="button"
                  onClick={() => enviar(sugerencia)}
                  className="whitespace-nowrap rounded-full bg-white/10 px-3 py-1.5 text-[11px] font-semibold text-white/85 ring-1 ring-white/10 transition hover:bg-amber-400/20 hover:text-amber-200"
                >
                  {sugerencia}
                </button>
              ))}
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              enviar();
            }}
            className="flex items-center gap-2 border-t border-white/10 bg-[#160409]/95 p-3"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="¿Qué necesitas hoy?"
              aria-label="Escribe tu mensaje al asistente"
              className="min-w-0 flex-1 rounded-full bg-white/10 px-4 py-2.5 text-sm text-white outline-none ring-1 ring-white/10 placeholder:text-white/40 focus:ring-amber-400/60"
            />
            <button
              type="submit"
              disabled={cargando || !input.trim()}
              aria-label="Enviar mensaje"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber-400 text-[#32100D] transition hover:bg-amber-300 disabled:opacity-40"
            >
              <Send className="h-5 w-5" aria-hidden="true" />
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => setAbierto((v) => !v)}
        aria-label={abierto ? "Cerrar asistente de compras" : "Abrir asistente de compras"}
        aria-expanded={abierto}
        className="relative ml-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-[#C8102E] to-[#570008] text-white shadow-[0_14px_35px_rgba(88,3,12,0.45)] ring-2 ring-amber-400/70 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_18px_45px_rgba(88,3,12,0.55)] active:scale-95"
      >
        {!abierto && (
          <span aria-hidden="true" className="absolute inset-0 -z-10 animate-ping rounded-full bg-[#C8102E]/40" />
        )}
        {abierto ? (
          <X className="h-6 w-6" aria-hidden="true" />
        ) : (
          <Bot className="h-6 w-6" aria-hidden="true" />
        )}
        {!abierto && (
          <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-amber-400 px-1 text-[10px] font-extrabold text-[#32100D] shadow">
            IA
          </span>
        )}
      </button>
    </div>
  );
}
