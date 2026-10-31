"use client";

import { useEffect, useRef, useState } from "react";
import { chatear, type Producto, type Receta } from "@/lib/api";
import { useCarrito } from "@/context/CarritoContext";
import { mostrarAviso } from "@/lib/aviso";
import Image from "next/image";

const CLAVE_CONSENTIMIENTO_IA = "la_economia_ia_consent_v1";

type Mensaje = {
  rol: "usuario" | "asistente";
  texto: string;
  productos?: Producto[];
  receta?: Receta;
};

type Props = {
  sedeId: string | null;
  onAgregar?: (p: Producto) => void;
};

const cop = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

const TEXTO_HABEAS_DATA = "En cumplimiento de la Ley 1581 de 2011 (Habeas Data), autorizo a La Economía Aya para el tratamiento de mis datos personales en esta interacción con la IA.";

function leerConsentimiento(): boolean {
  try { return window.localStorage.getItem(CLAVE_CONSENTIMIENTO_IA) === "true"; } catch { return false; }
}
function guardarConsentimiento(valor: boolean) { try { window.localStorage.setItem(CLAVE_CONSENTIMIENTO_IA, String(valor)); } catch {} }

export default function ChatAgente({ sedeId, onAgregar }: Props) {
  const { agregar } = useCarrito();
  const [abierto, setAbierto] = useState(false);
  const [input, setInput] = useState("");
  const [cargando, setCargando] = useState(false);
  const [agregadoKey, setAgregadoKey] = useState<string | null>(null);
  const [consentimiento, setConsentimiento] = useState(false);
  const [mostrarConsentimiento, setMostrarConsentimiento] = useState(false);
  const [recetaAbierta, setRecetaAbierta] = useState<Receta | null>(null);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    { rol: "asistente", texto: "¡Hola! Soy **Aya**, tu asistente de compras en La Economía Aya 😊\n\n¿En qué te ayudo hoy? ¿Buscas algo para cocinar, hacer el mercado de la semana, o solo se te antoja algo rico?" },
  ]);

  useEffect(() => { setConsentimiento(leerConsentimiento()); }, []);
  useEffect(() => { if (abierto && !leerConsentimiento()) setMostrarConsentimiento(true); }, [abierto]);
  useEffect(() => () => { if (temporizador.current) clearTimeout(temporizador.current); }, []);

  function agregarDesdeChat(p: Producto, clave: string) {
    if (sedeId === null) { mostrarAviso("Elige una sede para agregar productos desde el chat."); return; }
    agregar({ productoId: String(p.id), nombre: p.nombre, precio: p.precio, sedeId, imagen: p.imagen ?? undefined });
    mostrarAviso(`${p.nombre} agregado al carrito.`);
    setAgregadoKey(clave);
    if (temporizador.current) clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => setAgregadoKey(null), 1400);
    onAgregar?.(p);
  }

  async function agregarTodosIngredientes(receta: Receta) {
    if (sedeId === null) { mostrarAviso("Elige una sede para agregar productos."); return; }
    for (const ing of receta.ingredientes) {
      if (!ing.obligatorio) continue;
      try {
        const { productos } = await chatear(ing.busqueda_catalogo, sedeId);
        if (productos.length > 0) {
          const mejor = productos[0];
          agregar({ productoId: String(mejor.id), nombre: mejor.nombre, precio: mejor.precio, sedeId, imagen: mejor.imagen ?? undefined });
        }
      } catch {}
    }
    mostrarAviso("¡Ingredientes agregados al carrito! 🛒");
  }

  async function enviar() {
    if (!consentimiento) { setMostrarConsentimiento(true); return; }
    const texto = input.trim();
    if (!texto || cargando) return;
    setInput("");
    setMensajes((m) => [...m, { rol: "usuario", texto }]);
    setCargando(true);
    try {
      const { respuesta, productos, receta } = await chatear(texto, sedeId);
      setMensajes((m) => [...m, { rol: "asistente", texto: respuesta, productos, receta }]);
      if (receta) setRecetaAbierta(receta);
    } catch {
      setMensajes((m) => [...m, { rol: "asistente", texto: "No me pude conectar con el servidor. Intenta de nuevo." }]);
    } finally { setCargando(false); }
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Modal de receta completa */}
      {recetaAbierta && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={() => setRecetaAbierta(null)}>
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-2xl ring-2 ring-black" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white border-b border-black/10 px-4 py-3 flex items-center justify-between rounded-t-2xl">
              <h2 className="font-black text-lg text-brand-dark">{recetaAbierta.nombre}</h2>
              <button onClick={() => setRecetaAbierta(null)} className="text-2xl leading-none text-brand-dark/60 hover:text-black">×</button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-brand-dark/70 text-sm">{recetaAbierta.descripcion}</p>

              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-2 py-1 bg-brand-yellow text-brand-dark rounded-full font-medium">{recetaAbierta.tiempo_min} min</span>
                <span className="px-2 py-1 bg-brand-yellow text-brand-dark rounded-full font-medium">{recetaAbierta.porciones} porciones</span>
                <span className="px-2 py-1 bg-brand-red text-white rounded-full font-medium">{cop.format(recetaAbierta.costo_estimado_cop)}</span>
                {recetaAbierta.tags.map(t => <span key={t} className="px-2 py-1 bg-gray-100 text-gray-700 rounded-full font-medium text-xs">#{t}</span>)}
              </div>

              {/* Grid de ingredientes con imágenes */}
              <div className="space-y-2">
                <h3 className="font-black text-brand-dark flex items-center gap-2">🛒 Ingredientes</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {recetaAbierta.ingredientes.map((ing, idx) => (
                    <div key={idx} className={`relative group rounded-lg border-2 p-2 transition-all ${ing.obligatorio ? "border-brand-red/30 bg-brand-red/5" : "border-gray-200 bg-gray-50"}`}>
                      <div className="aspect-square bg-gray-100 rounded mb-2 overflow-hidden">
                        {ing.busqueda_catalogo && (
                          <Image
                            src={`https://placehold.co/100x100/F5F5F5/333?text=${encodeURIComponent(ing.nombre)}`}
                            alt={ing.nombre}
                            fill
                            className="object-cover group-hover:scale-105 transition-transform"
                            sizes="100px"
                          />
                        )}
                      </div>
                      <p className="text-xs font-black text-brand-dark truncate">{ing.nombre}</p>
                      <p className="text-[10px] text-gray-600">{ing.cantidad}</p>
                      {ing.notas && <p className="text-[9px] text-gray-400 italic">{ing.notas}</p>}
                      {!ing.obligatorio && <span className="absolute -top-1 -right-1 text-[9px] bg-gray-300 text-gray-600 px-1 rounded">Opcional</span>}
                    </div>
                  ))}
                </div>
              </div>

              {/* Botón agregar todo */}
              <button
                onClick={() => { agregarTodosIngredientes(recetaAbierta!); setRecetaAbierta(null); }}
                className="w-full bg-brand-green text-white font-black py-3 rounded-lg hover:bg-brand-green-dark active:scale-[0.98] transition flex items-center justify-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
                Agregar TODOS los ingredientes al carrito
              </button>

              {/* Pasos de preparación */}
              <details className="group border-t border-gray-200 pt-4">
                <summary className="font-bold text-brand-dark cursor-pointer flex items-center justify-between">
                  <span>👨‍🍳 Ver preparación paso a paso</span>
                  <svg className="w-5 h-5 text-brand-red group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                </summary>
                <div className="mt-3 space-y-2 text-sm text-brand-dark/80">
                  {recetaAbierta.pasos.map((paso, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="shrink-0 w-6 h-6 rounded-full bg-brand-red text-white text-[10px] font-bold flex items-center justify-center">{i + 1}</span>
                      <p>{paso}</p>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          </div>
        </div>
      )}

      {/* Chat principal */}
      {abierto && (
        <div className="mb-3 flex h-[36rem] w-80 flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/10 sm:w-96">
          {mostrarConsentimiento && !consentimiento && (
            <div className="flex flex-col gap-3 border-b border-black/10 bg-[#fff8e7] px-4 py-3">
              <p className="text-sm font-black text-black leading-relaxed">{TEXTO_HABEAS_DATA}</p>
              <label className="flex items-start gap-3 cursor-pointer">
                <input type="checkbox" onChange={(e) => { const v = e.target.checked; setConsentimiento(v); guardarConsentimiento(v); if (v) setMostrarConsentimiento(false); }} className="mt-1 h-4 w-4 accent-[#e30ba6] border-2 border-black" />
                <span className="text-sm font-semibold text-black">Acepto el tratamiento de mis datos personales</span>
              </label>
              <p className="text-xs text-black/60">Puedes revocar este consentimiento en cualquier momento desde la configuración.</p>
            </div>
          )}

          <div className="flex items-center justify-between bg-brand-red px-4 py-3 text-white">
            <span className="font-black flex items-center gap-2">🤖 <span>Aya</span></span>
            <button onClick={() => setAbierto(false)} aria-label="Cerrar" className="text-xl leading-none">×</button>
          </div>

          <div className="bg-brand-yellow px-3 py-1 text-[11px] font-medium text-brand-dark">
            Tu asistente personal de compras y cocina • Powered by Ollama + pgvector
          </div>

          <div className="flex-1 space-y-3 overflow-y-auto bg-brand-bg p-3">
            {mensajes.map((m, i) => (
              <div key={i} className={m.rol === "usuario" ? "flex justify-end" : "flex justify-start"}>
                <div className="max-w-[90%] space-y-2">
                  <div className={`whitespace-pre-wrap rounded-xl px-3 py-2 text-sm ${m.rol === "usuario" ? "bg-brand-red text-white" : "bg-white text-brand-dark shadow-sm"}`}>
                    {m.texto}
                  </div>

                  {/* Productos recomendados */}
                  {m.productos?.map((p, j) => {
                    const clave = `${i}-${j}`;
                    const agregado = agregadoKey === clave;
                    return (
                      <div key={`${p.id}-${j}`} className="flex items-center justify-between gap-2 rounded-lg border border-gray-200 bg-white p-2 shadow-sm">
                        <div className="min-w-0">
                          <p className="truncate text-xs font-semibold text-brand-dark">{p.nombre}</p>
                          <p className="text-sm font-extrabold text-brand-red">{cop.format(p.precio)}</p>
                        </div>
                        <button onClick={() => agregarDesdeChat(p, clave)} disabled={p.stock <= 0} className={`shrink-0 rounded-md px-2 py-1 text-[11px] font-bold text-white transition-all duration-200 active:scale-95 disabled:bg-gray-300 disabled:active:scale-100 ${agregado ? "bg-emerald-600" : "bg-brand-green hover:bg-brand-green-dark"}`}>
                          {p.stock <= 0 ? "Agotado" : agregado ? "¡Agregado! ✓" : "Agregar"}
                        </button>
                      </div>
                    );
                  })}

                  {/* Tarjeta de receta detectada */}
                  {m.receta && (
                    <div className="rounded-xl border-2 border-brand-red/30 bg-brand-red/5 p-3 shadow-sm">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <p className="font-black text-brand-dark">{m.receta.nombre}</p>
                          <p className="text-xs text-brand-dark/70">{m.receta.descripcion}</p>
                        </div>
                        <button onClick={() => setRecetaAbierta(m.receta!)} className="shrink-0 text-brand-red text-xs font-bold underline hover:text-brand-red-dark">Ver todo →</button>
                      </div>

                      <div className="flex flex-wrap gap-1 mb-2">
                        <span className="px-2 py-0.5 bg-brand-yellow text-brand-dark rounded-full text-[10px] font-medium">{m.receta.tiempo_min} min</span>
                        <span className="px-2 py-0.5 bg-brand-yellow text-brand-dark rounded-full text-[10px] font-medium">{m.receta.porciones} porc.</span>
                        <span className="px-2 py-0.5 bg-brand-red text-white rounded-full text-[10px] font-medium">{cop.format(m.receta.costo_estimado_cop)}</span>
                      </div>

                      {/* Mini grid ingredientes */}
                      <div className="grid grid-cols-3 gap-1.5">
                        {m.receta.ingredientes.filter(ing => ing.obligatorio).slice(0, 6).map((ing, idx) => (
                          <div key={idx} className="relative aspect-square bg-gray-100 rounded overflow-hidden">
                            <Image
                              src={`https://placehold.co/80x80/F5F5F5/333?text=${encodeURIComponent(ing.nombre)}`}
                              alt={ing.nombre}
                              fill
                              className="object-cover"
                              sizes="80px"
                            />
                            <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[8px] px-1 py-0.5 truncate">{ing.nombre}</div>
                          </div>
                        ))}
                        {m.receta.ingredientes.filter(ing => ing.obligatorio).length > 6 && (
                          <div className="relative aspect-square bg-gray-100 rounded overflow-hidden flex items-center justify-center">
                            <span className="text-[10px] font-bold text-gray-500">+{m.receta.ingredientes.filter(ing => ing.obligatorio).length - 6} más</span>
                          </div>
                        )}
                      </div>

                      <button onClick={() => { agregarTodosIngredientes(m.receta!); }} className="mt-2 w-full text-xs font-bold text-brand-red hover:underline flex items-center justify-center gap-1">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
                        Agregar ingredientes al carrito
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {cargando && <div className="text-xs text-gray-500 flex items-center gap-1"><span className="animate-pulse">●</span><span className="animate-pulse">●</span><span className="animate-pulse">●</span> Aya está pensando…</div>}
          </div>

          {!mostrarConsentimiento && (
            <div className="flex gap-2 border-t border-gray-200 bg-white p-2">
              <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && enviar()} placeholder="¿Qué buscas hoy? (ej: café, huevos pericos, mercado semana, snacks sanos...)" className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-brand-dark outline-none focus:border-brand-red" />
              <button onClick={enviar} disabled={cargando} className="rounded-lg bg-brand-green px-3 text-sm font-bold text-white hover:bg-brand-green-dark disabled:opacity-50">Enviar</button>
            </div>
          )}
        </div>
      )}

      {/* Botón flotante */}
      <button onClick={() => setAbierto(v => !v)} className="group relative ml-auto flex h-14 w-14 items-center justify-center rounded-full border-2 border-brand-yellow bg-brand-red text-2xl text-white shadow-lg transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl active:scale-95" aria-label={abierto ? "Cerrar asistente" : "Abrir asistente"}>
        {!abierto && <span aria-hidden="true" className="absolute inset-0 -z-10 animate-ping rounded-full bg-brand-red/40" />}
        <span aria-hidden="true">{abierto ? "×" : "💬"}</span>
        {!abierto && <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-brand-yellow px-1 text-[10px] font-extrabold text-brand-dark shadow">IA</span>}
      </button>
    </div>
  );
}