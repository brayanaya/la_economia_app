"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  chatear,
  obtenerConversaciones,
  obtenerConversacion,
  eliminarConversacion,
  type Producto,
  type Receta,
  type Presupuesto,
  type Comparacion,
  type CartAction,
  type CartActionAdd,
  type CartActionRemove,
  type CartActionUpdate,
  type CartActionClear,
  type CartActionList,
  type CartActionConfirmClear,
  type ConversacionItem,
} from "@/lib/api";
import { useCarrito } from "@/context/CarritoContext";
import { useAuth } from "@/context/AuthContext";
import { mostrarAviso } from "@/lib/aviso";
import { SafeImage, SafeProductImage, SafeIngredientImage, SafeRecipeImage } from "@/components/SafeImage";

const CLAVE_CONSENTIMIENTO_IA = "la_economia_ia_consent_v1";
const CLAVE_CONVERSACION_ID = "la_economia_ia_conversacion_id_v1";

type Mensaje = {
  rol: "usuario" | "asistente";
  texto: string;
  productos?: Producto[];
  receta?: Receta;
  presupuesto?: Presupuesto;
  comparacion?: Comparacion;
  cart_actions?: CartAction[];
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

function leerConversacionId(): string | null {
  try { return window.localStorage.getItem(CLAVE_CONVERSACION_ID); } catch { return null; }
}
function guardarConversacionId(id: string | null) {
  try {
    if (id) window.localStorage.setItem(CLAVE_CONVERSACION_ID, id);
    else window.localStorage.removeItem(CLAVE_CONVERSACION_ID);
  } catch {}
}

export default function ChatAgente({ sedeId, onAgregar }: Props) {
  const { agregar, quitar, cambiarCantidad, vaciar, vaciarSede, items } = useCarrito();
  const { user } = useAuth();
  const [abierto, setAbierto] = useState(false);
  const [input, setInput] = useState("");
  const [cargando, setCargando] = useState(false);
  const [agregadoKey, setAgregadoKey] = useState<string | null>(null);
  const [consentimiento, setConsentimiento] = useState(false);
  const [mostrarConsentimiento, setMostrarConsentimiento] = useState(false);
  const [recetaAbierta, setRecetaAbierta] = useState<Receta | null>(null);
  const [presupuestoAbierto, setPresupuestoAbierto] = useState<Presupuesto | null>(null);
  const [comparacionAbierta, setComparacionAbierta] = useState<Comparacion | null>(null);
  const [confirmarVaciar, setConfirmarVaciar] = useState<{ sedeId?: string; mensaje: string } | null>(null);
  // Estado para presupuesto modal mejorado
  const [cantidadesEditadas, setCantidadesEditadas] = useState<Record<number, number>>({});
  const [presupuestoRecalculando, setPresupuestoRecalculando] = useState(false);
  const [presupuestoError, setPresupuestoError] = useState<string | null>(null);
  // Estado para comparación modal
  const [productosComparacionSeleccionados, setProductosComparacionSeleccionados] = useState<Set<string>>(new Set());
  // Estado para persistencia y lista de conversaciones (Bloque 3)
  const [conversacionId, setConversacionId] = useState<string | null>(null);
  const [panelHistorialAbierto, setPanelHistorialAbierto] = useState(false);
  const [listaConversaciones, setListaConversaciones] = useState<ConversacionItem[]>([]);
  const [cargandoHistorial, setCargandoHistorial] = useState(false);

  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    { rol: "asistente", texto: "¡Hola! Soy **Aya**, tu asistente de compras en La Economía Aya 😊\n\n¿En qué te ayudo hoy? ¿Buscas algo para cocinar, hacer el mercado de la semana, o solo se te antoja algo rico?" },
  ]);

  // Cargar estado inicial persistente
  useEffect(() => {
    setConsentimiento(leerConsentimiento());
    const guardadoId = leerConversacionId();
    if (guardadoId) {
      setConversacionId(guardadoId);
      // Restaurar conversación previa si existe
      void obtenerConversacion(guardadoId).then((detalle) => {
        if (detalle && detalle.mensajes.length > 0) {
          setMensajes(detalle.mensajes.map((m) => ({
            rol: m.rol,
            texto: m.contenido,
          })));
        }
      });
    }
  }, []);

  useEffect(() => { if (abierto && !leerConsentimiento()) setMostrarConsentimiento(true); }, [abierto]);
  useEffect(() => () => { if (temporizador.current) clearTimeout(temporizador.current); }, []);

  // Cargar lista de conversaciones cuando se abre el panel
  const cargarListaConversaciones = useCallback(async () => {
    setCargandoHistorial(true);
    try {
      const items = await obtenerConversaciones(20);
      setListaConversaciones(items);
    } finally {
      setCargandoHistorial(false);
    }
  }, []);

  const iniciarNuevaConversacion = () => {
    guardarConversacionId(null);
    setConversacionId(null);
    setMensajes([
      { rol: "asistente", texto: "¡Hola de nuevo! Iniciamos una nueva conversación 🛒✨\n\n¿En qué te puedo asesorar hoy?" },
    ]);
    setPanelHistorialAbierto(false);
    mostrarAviso("Nueva conversación iniciada.");
  };

  const seleccionarConversacion = async (id: string) => {
    setCargando(true);
    try {
      const detalle = await obtenerConversacion(id);
      if (detalle && detalle.mensajes.length > 0) {
        setConversacionId(id);
        guardarConversacionId(id);
        setMensajes(detalle.mensajes.map((m) => ({
          rol: m.rol,
          texto: m.contenido,
        })));
        setPanelHistorialAbierto(false);
        mostrarAviso("Conversación restaurada.");
      }
    } finally {
      setCargando(false);
    }
  };

  const borrarConversacionItem = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    const ok = await eliminarConversacion(id);
    if (ok) {
      setListaConversaciones((prev) => prev.filter((c) => c.id !== id));
      if (conversacionId === id) {
        iniciarNuevaConversacion();
      }
      mostrarAviso("Conversación eliminada.");
    }
  };

  function agregarDesdeChat(p: Producto, clave: string) {
    if (sedeId === null) { mostrarAviso("Elige una sede para agregar productos desde el chat."); return; }
    agregar({ productoId: String(p.id), nombre: p.nombre, precio: p.precio, sedeId, imagen: p.imagen ?? undefined });
    mostrarAviso(`${p.nombre} agregado al carrito.`);
    setAgregadoKey(clave);
    if (temporizador.current) clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => setAgregadoKey(null), 1400);
    onAgregar?.(p);
  }

  // Ejecutar acciones de carrito devueltas por el agente
  // Retorna un resumen de lo que realmente se ejecutó para confirmaciones visuales precisas
  async function ejecutarAccionesCarrito(acciones: CartAction[]): Promise<string[]> {
    const resultados: string[] = [];

    for (const accion of acciones) {
      switch (accion.tipo) {
        case "add": {
          let agregados = 0;
          for (const item of accion.items) {
            // Validar que el producto tenga precio > 0 (producto verificado)
            if (item.precio_unitario <= 0) {
              resultados.push(`⚠️ ${item.nombre}: no se encontró en el catálogo (precio no disponible)`);
              continue;
            }
            const sede = sedeId ?? item.sede_id;
            if (sede) {
              agregar({
                productoId: item.producto_id,
                nombre: item.nombre,
                precio: item.precio_unitario,
                sedeId: sede,
                imagen: item.imagen_url ?? undefined,
              }, item.cantidad);
              agregados++;
            } else {
              resultados.push(`⚠️ ${item.nombre}: requiere seleccionar una sede`);
            }
          }
          if (agregados > 0) {
            resultados.push(`✅ ${agregados} producto(s) agregado(s) al carrito`);
          }
          break;
        }
        case "remove": {
          let quitados = 0;
          for (const productoId of accion.producto_ids) {
            const sede = sedeId ?? accion.sede_id;
            if (sede) {
              // Verificar si el producto está realmente en el carrito antes de quitar
              const enCarrito = items.some(i => i.productoId === productoId && i.sedeId === sede);
              if (enCarrito) {
                quitar(productoId, sede);
                quitados++;
              } else {
                resultados.push(`⚠️ Producto ${productoId} no estaba en el carrito`);
              }
            }
          }
          if (quitados > 0) {
            resultados.push(`✅ ${quitados} producto(s) quitado(s) del carrito`);
          }
          break;
        }
        case "update": {
          let actualizados = 0;
          for (const item of accion.items) {
            const sede = sedeId ?? item.sede_id;
            if (sede) {
              // Verificar si el producto está en el carrito
              const enCarrito = items.some(i => i.productoId === item.producto_id && i.sedeId === sede);
              if (enCarrito) {
                cambiarCantidad(item.producto_id, sede, item.cantidad);
                actualizados++;
              } else {
                resultados.push(`⚠️ ${item.nombre} no está en el carrito para actualizar`);
              }
            }
          }
          if (actualizados > 0) {
            resultados.push(`✅ ${actualizados} producto(s) actualizado(s)`);
          }
          break;
        }
        case "confirm_clear": {
          // Solicitar confirmación al usuario (fix issue #3)
          setConfirmarVaciar({ sedeId: accion.sede_id, mensaje: accion.mensaje });
          resultados.push(`❓ ${accion.mensaje}`);
          break;
        }
        case "clear": {
          // Ejecución directa de clear (solo si ya se confirmó)
          if (accion.sede_id) {
            vaciarSede(accion.sede_id);
            resultados.push(`✅ Carrito de sede vaciado`);
          } else {
            vaciar();
            resultados.push(`✅ Carrito vaciado completamente`);
          }
          break;
        }
        case "list": {
          // Mostrar contenido real del carrito (fix issue #7)
          if (items.length === 0) {
            resultados.push(`📋 El carrito está vacío`);
          } else {
            const totalItems = items.reduce((sum, i) => sum + i.cantidad, 0);
            const totalPrecio = items.reduce((sum, i) => sum + i.precio * i.cantidad, 0);
            const itemsText = items.map(i => `${i.cantidad}x ${i.nombre} (${cop.format(i.precio * i.cantidad)})`).join(", ");
            resultados.push(`📋 Carrito: ${totalItems} items, Total: ${cop.format(totalPrecio)}`);
            resultados.push(`   ${itemsText}`);
          }
          break;
        }
      }
    }

    return resultados;
  }

  // Recalcular presupuesto con cantidades editadas
  async function recalcularPresupuesto(presupuesto: Presupuesto) {
    if (!sedeId) { mostrarAviso("Elige una sede para recalcular."); return; }
    setPresupuestoRecalculando(true);
    setPresupuestoError(null);

    // Construir mensaje con items actualizados
    const itemsActualizados = presupuesto.items.map((item, idx) => ({
      ...item,
      cantidad: cantidadesEditadas[idx] ?? item.cantidad,
    }));

    const lineas = itemsActualizados.map(item =>
      `${item.cantidad} ${item.unidad} de ${item.termino_busqueda} (${cop.format(item.precio_unitario)}/unid)`
    ).join(", ");

    const mensaje = `Recalcula mi presupuesto: ${lineas}. Presupuesto límite: ${presupuesto.presupuesto_limite ? cop.format(presupuesto.presupuesto_limite) : "sin límite"}`;

    try {
      const response = await chatear(mensaje, sedeId);
      if (response.presupuesto) {
        setPresupuestoAbierto(response.presupuesto);
        setCantidadesEditadas({}); // Reset cantidades editadas
        mostrarAviso("Presupuesto recalculado.");
      } else if (response.respuesta) {
        mostrarAviso(response.respuesta);
      }
    } catch {
      setPresupuestoError("No se pudo recalcular. Intenta de nuevo.");
    } finally {
      setPresupuestoRecalculando(false);
    }
  }

  // Solicitar alternativa para un producto del presupuesto
  async function solicitarAlternativaPresupuesto(terminoBusqueda: string, presupuestoActual: Presupuesto) {
    if (!sedeId) { mostrarAviso("Elige una sede para buscar alternativas."); return; }

    const mensaje = `Quiero una alternativa más barata o similar a "${terminoBusqueda}" para mi lista de mercado.`;
    try {
      const response = await chatear(mensaje, sedeId);
      if (response.comparacion) {
        setPresupuestoAbierto(null);
        setComparacionAbierta(response.comparacion);
      } else if (response.respuesta) {
        mostrarAviso(response.respuesta);
      }
    } catch {
      mostrarAviso("No se pudo buscar alternativas.");
    }
  }

  // Agregar producto individual del presupuesto al carrito
  function agregarItemPresupuesto(item: Presupuesto["items"][0]) {
    if (!sedeId || !item.producto_id || item.estado !== "disponible") return;
    agregar({
      productoId: item.producto_id,
      nombre: item.producto_nombre ?? item.termino_busqueda,
      precio: item.precio_unitario,
      sedeId,
    }, item.cantidad);
    mostrarAviso(`${item.producto_nombre ?? item.termino_busqueda} agregado al carrito.`);
  }

  // Agregar producto de comparación al carrito
  function agregarProductoComparacion(prod: Comparacion["productos"][0]) {
    if (!sedeId || prod.precio_final <= 0 || !prod.disponible) return;
    agregar({
      productoId: prod.id,
      nombre: prod.nombre,
      precio: prod.precio_final,
      sedeId,
      // ComparacionItem no tiene imagen_url, se omite
    });
    mostrarAviso(`${prod.nombre} agregado al carrito.`);
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
      const response = await chatear(texto, sedeId, conversacionId);
      const { respuesta, productos, receta, presupuesto, comparacion, cart_actions, conversacion_id: resCid } = response;

      if (resCid && resCid !== conversacionId) {
        setConversacionId(resCid);
        guardarConversacionId(resCid);
      }

      // Ejecutar acciones de carrito si las hay y obtener resultados reales
      let resultadosCarrito: string[] = [];
      if (cart_actions && cart_actions.length > 0) {
        resultadosCarrito = await ejecutarAccionesCarrito(cart_actions);
      }

      // Combinar respuesta del agente con resultados reales de carrito
      let respuestaFinal = respuesta;
      if (resultadosCarrito.length > 0) {
        respuestaFinal += "\n\n" + resultadosCarrito.join("\n");
      }

      setMensajes((m) => [...m, {
        rol: "asistente",
        texto: respuestaFinal,
        productos,
        receta,
        presupuesto,
        comparacion,
        cart_actions
      }]);

      if (receta) setRecetaAbierta(receta);
      if (presupuesto) setPresupuestoAbierto(presupuesto);
      if (comparacion) setComparacionAbierta(comparacion);
    } catch {
      setMensajes((m) => [...m, { rol: "asistente", texto: "No me pude conectar con el servidor. Intenta de nuevo." }]);
    } finally { setCargando(false); }
  }


  // Confirmar vaciado de carrito
  function confirmarVaciarCarrito(confirmado: boolean) {
    if (confirmarVaciar && confirmado) {
      if (confirmarVaciar.sedeId) {
        vaciarSede(confirmarVaciar.sedeId);
        mostrarAviso("Carrito de sede vaciado.");
      } else {
        vaciar();
        mostrarAviso("Carrito vaciado completamente.");
      }
    }
    setConfirmarVaciar(null);
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
                          <SafeIngredientImage
                            src={undefined}
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

      {/* Modal de presupuesto completo - Neo-Pop */}
      {presupuestoAbierto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={() => setPresupuestoAbierto(null)}>
          <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-[8px_8px_0_0_#3f0791] border-2 border-black" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white border-b-2 border-brand-green/30 px-4 py-3 flex items-center justify-between">
              <h2 className="font-black text-lg text-brand-dark flex items-center gap-2">📊 Presupuesto de Mercado</h2>
              <button onClick={() => setPresupuestoAbierto(null)} className="w-10 h-10 rounded-xl border-2 border-gray-200 bg-white font-black text-brand-dark hover:bg-brand-red/10 hover:border-brand-red hover:text-brand-red active:scale-[0.95] transition flex items-center justify-center">×</button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-brand-dark/70 text-sm">{presupuestoAbierto.resumen_usuario}</p>

              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-3 py-1.5 bg-brand-yellow text-brand-dark rounded-full font-black border-2 border-brand-yellow/50 shadow-[2px_2px_0_0_#3f0791]">Total: {cop.format(presupuestoAbierto.total_con_precio)}</span>
                {presupuestoAbierto.presupuesto_limite && (
                  <span className={`px-3 py-1.5 rounded-full font-black border-2 shadow-[2px_2px_0_0_#3f0791] ${presupuestoAbierto.presupuesto_excedido ? "bg-brand-red text-white border-brand-red" : "bg-brand-green text-white border-brand-green"}`}>
                    Límite: {cop.format(presupuestoAbierto.presupuesto_limite)}
                    {presupuestoAbierto.presupuesto_excedido && (
                      <span className="ml-1">(Excedido por {cop.format(presupuestoAbierto.diferencia_presupuesto)})</span>
                    )}
                  </span>
                )}
                <span className="px-3 py-1.5 bg-white text-gray-700 rounded-full font-black border-2 border-gray-200 shadow-[2px_2px_0_0_#3f0791]">{presupuestoAbierto.items.length} items</span>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto">
                {presupuestoAbierto.items.map((item, idx) => {
                  const cantidadActual = cantidadesEditadas[idx] ?? item.cantidad;
                  const subtotalActual = cantidadActual * item.precio_unitario;
                  return (
                    <div key={idx} className={`flex flex-col sm:flex-row sm:items-center gap-3 p-3 rounded-xl border-2 ${item.estado === "disponible" ? "bg-green-50 border-brand-green/30 shadow-[2px_2px_0_0_#16a34a]" : item.estado === "sin_stock" ? "bg-yellow-50 border-brand-yellow/30 shadow-[2px_2px_0_0_#ca8a04]" : "bg-red-50 border-brand-red/30 shadow-[2px_2px_0_0_#dc2626]"}`}>
                      <div className="w-14 h-14 rounded-lg bg-brand-green/10 flex items-center justify-center flex-shrink-0 overflow-hidden relative">
                        <SafeProductImage
                          src={item.producto_imagen_url}
                          alt={item.termino_busqueda}
                          fill
                          className="object-contain"
                          sizes="56px"
                        />
                        {item.estado !== "disponible" && (
                          <span className="absolute inset-0 bg-red-500/70 flex items-center justify-center">
                            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                          </span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-black text-brand-dark truncate">{item.producto_nombre ?? item.termino_busqueda}</p>
                        <p className="text-[11px] text-brand-dark/50">{item.unidad} • {cop.format(item.precio_unitario)}/unid</p>
                      </div>
                      <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
                        <div className="flex items-center gap-1 border-2 border-gray-200 rounded-lg bg-white shadow-sm">
                          <button
                            onClick={() => {
                              const nueva = Math.max(0, cantidadActual - 1);
                              setCantidadesEditadas(prev => ({ ...prev, [idx]: nueva }));
                            }}
                            className="w-9 h-9 rounded-l-lg text-brand-dark font-black hover:bg-brand-green/10 active:scale-[0.95] transition flex items-center justify-center"
                            aria-label="Disminuir cantidad"
                          >−</button>
                          <input
                            type="number"
                            value={cantidadActual}
                            onChange={(e) => {
                              const val = Math.max(0, parseInt(e.target.value) || 0);
                              setCantidadesEditadas(prev => ({ ...prev, [idx]: val }));
                            }}
                            min="0"
                            max="99"
                            className="w-16 text-center text-sm font-medium text-brand-dark border-0 focus:outline-none"
                          />
                          <button
                            onClick={() => {
                              const nueva = Math.min(99, cantidadActual + 1);
                              setCantidadesEditadas(prev => ({ ...prev, [idx]: nueva }));
                            }}
                            className="w-9 h-9 rounded-r-lg text-brand-dark font-black hover:bg-brand-green/10 active:scale-[0.95] transition flex items-center justify-center"
                            aria-label="Aumentar cantidad"
                          >+</button>
                        </div>
                        <span className="text-sm font-extrabold text-brand-dark min-w-[70px] text-right whitespace-nowrap">
                          {cop.format(subtotalActual)}
                        </span>
                        <span className={`text-[10px] capitalize px-2 py-0.5 rounded-full font-black border-2 ${item.estado === "disponible" ? "bg-green-100 text-green-800 border-green-300" : item.estado === "sin_stock" ? "bg-yellow-100 text-yellow-800 border-yellow-300" : "bg-red-100 text-red-800 border-red-300"}`}>
                          {item.estado.replace("_", " ")}
                        </span>
                        {item.estado === "disponible" && item.producto_id && (
                          <button
                            onClick={() => {
                              agregar({
                                productoId: item.producto_id!,
                                nombre: item.producto_nombre ?? item.termino_busqueda,
                                precio: item.precio_unitario,
                                sedeId: sedeId!,
                              }, cantidadActual);
                              mostrarAviso(`${item.producto_nombre ?? item.termino_busqueda} agregado al carrito.`);
                            }}
                            className="px-3 py-1.5 text-[10px] font-black text-brand-green hover:underline flex items-center gap-1 hover:text-brand-green-dark transition"
                            title="Agregar al carrito"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
                          </button>
                        )}
                        {item.estado !== "disponible" && (
                          <button
                            onClick={() => solicitarAlternativaPresupuesto(item.termino_busqueda, presupuestoAbierto!)}
                            className="px-3 py-1.5 text-[10px] font-black text-brand-blue hover:underline flex items-center gap-1 hover:text-brand-blue-dark transition"
                            title="Buscar alternativa"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {presupuestoAbierto.limitaciones && presupuestoAbierto.limitaciones.length > 0 && (
                <details className="border-t-2 border-brand-green/20 pt-3">
                  <summary className="font-black text-brand-dark cursor-pointer flex items-center justify-between text-sm">
                    <span className="flex items-center gap-1">⚠️ Limitaciones y notas</span>
                    <svg className="w-4 h-4 text-brand-red" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  </summary>
                  <ul className="mt-2 text-xs text-brand-dark/70 space-y-1 ml-4">
                    {presupuestoAbierto.limitaciones.map((lim, idx) => (
                      <li key={idx} className="flex gap-1">• {lim}</li>
                    ))}
                  </ul>
                </details>
              )}

              {presupuestoError && (
                <div className="p-3 bg-red-50 border-2 border-red-200 rounded-xl text-red-700 text-xs flex items-center gap-2">
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                  {presupuestoError}
                </div>
              )}

              <div className="flex flex-wrap gap-2 border-t-2 border-brand-green/20 pt-4">
                <button
                  onClick={() => recalcularPresupuesto(presupuestoAbierto!)}
                  disabled={presupuestoRecalculando}
                  className="flex-1 bg-brand-purple text-white font-black py-3 rounded-xl border-2 border-brand-purple hover:bg-brand-purple/90 active:scale-[0.98] transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-[2px_2px_0_0_#3f0791]"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                  {presupuestoRecalculando ? "Recalculando…" : "Recalcular presupuesto"}
                </button>
                <button
                  onClick={() => {
                    if (sedeId === null) { mostrarAviso("Elige una sede para agregar productos."); return; }
                    presupuestoAbierto.items.forEach(item => {
                      if (item.producto_id && item.estado === "disponible") {
                        const cant = cantidadesEditadas[presupuestoAbierto.items.indexOf(item)] ?? item.cantidad;
                        agregar({
                          productoId: item.producto_id,
                          nombre: item.producto_nombre ?? item.termino_busqueda,
                          precio: item.precio_unitario,
                          sedeId,
                        }, cant);
                      }
                    });
                    mostrarAviso("Productos del presupuesto agregados al carrito.");
                    setPresupuestoAbierto(null);
                    setCantidadesEditadas({});
                  }}
                  className="flex-1 bg-brand-green text-white font-black py-3 rounded-xl border-2 border-brand-green hover:bg-brand-green/90 active:scale-[0.98] transition flex items-center justify-center gap-2 shadow-[2px_2px_0_0_#3f0791]"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
                  Agregar disponibles
                </button>
                <button
                  onClick={() => {
                    const sinStock = presupuestoAbierto.items.filter(i => i.estado === "sin_stock");
                    if (sinStock.length === 0) { mostrarAviso("No hay productos sin stock en este presupuesto."); return; }
                    const mensaje = `Quiero quitar del presupuesto estos productos sin stock: ${sinStock.map(i => i.termino_busqueda).join(", ")}.`;
                    chatear(mensaje, sedeId).then(response => {
                      if (response.presupuesto) {
                        setPresupuestoAbierto(response.presupuesto);
                        setCantidadesEditadas({});
                        mostrarAviso("Productos sin stock eliminados del presupuesto.");
                      }
                    }).catch(() => mostrarAviso("No se pudo actualizar el presupuesto."));
                  }}
                  className="flex-1 border-2 border-brand-yellow bg-white font-black text-brand-dark py-3 rounded-xl hover:bg-yellow-50 active:scale-[0.98] transition flex items-center justify-center gap-2 shadow-[2px_2px_0_0_#3f0791]"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 016.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  Excluir sin stock
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de confirmación para vaciar carrito */}
      {confirmarVaciar && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={() => confirmarVaciarCarrito(false)}>
          <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl ring-2 ring-black p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-brand-red/10 flex items-center justify-center">
                <svg className="w-6 h-6 text-brand-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h2 className="font-black text-brand-dark text-lg">Confirmar vaciado</h2>
            </div>
            <p className="text-brand-dark/70 mb-6">{confirmarVaciar.mensaje}</p>
            <div className="flex gap-3">
              <button onClick={() => confirmarVaciarCarrito(true)} className="flex-1 bg-brand-red text-white font-black py-3 rounded-lg hover:bg-brand-red-dark active:scale-[0.98] transition">
                Sí, vaciar carrito
              </button>
              <button onClick={() => confirmarVaciarCarrito(false)} className="flex-1 border-2 border-gray-300 bg-white font-black text-gray-700 py-3 rounded-lg hover:bg-gray-50 active:scale-[0.98] transition">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de comparación completa - Neo-Pop */}
      {comparacionAbierta && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={() => setComparacionAbierta(null)}>
          <div className="w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-[8px_8px_0_0_#3f0791] border-2 border-black" onClick={e => e.stopPropagation()}>
            <div className="sticky top-0 bg-white border-b-2 border-brand-green/30 px-4 py-3 flex items-center justify-between">
              <h2 className="font-black text-lg text-brand-dark flex items-center gap-2">⚖️ Comparación: {comparacionAbierta.criterio}</h2>
              <button onClick={() => setComparacionAbierta(null)} className="w-10 h-10 rounded-xl border-2 border-gray-200 bg-white font-black text-brand-dark hover:bg-brand-red/10 hover:border-brand-red hover:text-brand-red active:scale-[0.95] transition flex items-center justify-center">×</button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-brand-dark/70 text-sm">{comparacionAbierta.explicacion}</p>

              <div className="flex flex-wrap gap-2 text-xs">
                <span className="px-3 py-1.5 bg-brand-yellow text-brand-dark rounded-full font-black border-2 border-brand-yellow/50 shadow-[2px_2px_0_0_#3f0791]">{comparacionAbierta.tipo_comparacion}</span>
                <span className="px-3 py-1.5 bg-white text-gray-700 rounded-full font-black border-2 border-gray-200 shadow-[2px_2px_0_0_#3f0791]">{comparacionAbierta.productos.length} opciones</span>
                {comparacionAbierta.mejor_opcion_id && (
                  <span className="px-3 py-1.5 bg-emerald-100 text-emerald-800 rounded-full font-black border-2 border-emerald-300 shadow-[2px_2px_0_0_#3f0791]">Mejor opción ✓</span>
                )}
              </div>

              <div className="space-y-2">
                {comparacionAbierta.productos.map((prod) => {
                  const seleccionado = productosComparacionSeleccionados.has(prod.id);
                  const esMejor = prod.id === comparacionAbierta.mejor_opcion_id;
                  return (
                    <div key={prod.id} className={`flex items-center gap-3 p-3 rounded-xl border-2 ${esMejor ? "bg-emerald-50 border-emerald-300 shadow-[2px_2px_0_0_#16a34a]" : "bg-white border-gray-200"}`}>
                      <div className="w-14 h-14 rounded-lg bg-brand-blue/10 flex items-center justify-center flex-shrink-0 overflow-hidden relative">
                        <SafeProductImage
                          src={prod.imagen_url}
                          alt={prod.nombre}
                          fill
                          className="object-contain"
                          sizes="56px"
                        />
                        {!prod.disponible && (
                          <span className="absolute inset-0 bg-red-500/70 flex items-center justify-center">
                            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                          </span>
                        )}
                      </div>
                      <input
                        type="checkbox"
                        checked={seleccionado}
                        onChange={(e) => {
                          const newSet = new Set(productosComparacionSeleccionados);
                          if (e.target.checked) newSet.add(prod.id);
                          else newSet.delete(prod.id);
                          setProductosComparacionSeleccionados(newSet);
                        }}
                        className="w-5 h-5 accent-brand-red border-2 border-gray-300 rounded shrink-0 mt-2"
                        disabled={!prod.disponible || prod.precio_final <= 0}
                      />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-black text-brand-dark truncate">{prod.nombre}</p>
                        <p className="text-xs text-brand-dark/50">{prod.marca ?? ""} {prod.presentacion ?? ""}</p>
                        {prod.razones.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {prod.razones.slice(0, 3).map((razon, idx) => (
                              <span key={idx} className="text-[10px] bg-brand-blue/10 text-brand-blue px-2 py-0.5 rounded-full font-medium border border-brand-blue/30">{razon}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="text-right min-w-[140px]">
                        <p className="text-sm font-extrabold text-brand-red">{cop.format(prod.precio_final)}</p>
                        {prod.precio_por_unidad_base && (
                          <p className="text-xs text-brand-dark/50">{cop.format(prod.precio_por_unidad_base)}/{prod.unidad_medida}</p>
                        )}
                        <div className="mt-1 flex flex-wrap gap-1 justify-end">
                          {prod.tiene_promocion && <span className="text-[10px] bg-brand-red/10 text-brand-red px-2 py-0.5 rounded-full font-medium border border-brand-red/30">🏷 Promoción</span>}
                          {esMejor && <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium border border-emerald-300">✓ Mejor opción</span>}
                          {!prod.disponible && <span className="text-[10px] bg-red-100 text-red-800 px-2 py-0.5 rounded-full font-medium border border-red-300">Sin stock</span>}
                          {prod.precio_final <= 0 && <span className="text-[10px] bg-gray-100 text-gray-800 px-2 py-0.5 rounded-full font-medium border border-gray-300">Sin precio</span>}
                        </div>
                      </div>
                      <div className="flex flex-col gap-1 items-end w-24 shrink-0">
                        {(prod.disponible && prod.precio_final > 0) && (
                          <button
                            onClick={() => {
                              agregar({
                                productoId: prod.id,
                                nombre: prod.nombre,
                                precio: prod.precio_final,
                                sedeId: sedeId!,
                              });
                              mostrarAviso(`${prod.nombre} agregado al carrito.`);
                            }}
                            className="w-full px-2 py-1.5 text-[10px] font-black text-brand-green hover:underline flex items-center justify-center gap-1 hover:text-brand-green-dark transition"
                            title="Agregar al carrito"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
                          </button>
                        )}
                        {esMejor && (
                          <span className="text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full font-medium border border-emerald-300 text-center">Mejor opción</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {productosComparacionSeleccionados.size > 0 && (
                <div className="flex flex-wrap gap-2 p-3 bg-brand-blue/5 border-2 border-brand-blue/30 rounded-xl shadow-[2px_2px_0_0_#3f0791]">
                  <span className="text-xs font-medium text-brand-blue">Seleccionados: {productosComparacionSeleccionados.size}</span>
                  <button
                    onClick={() => {
                      if (!sedeId) { mostrarAviso("Elige una sede para agregar productos."); return; }
                      comparacionAbierta.productos.filter(p => productosComparacionSeleccionados.has(p.id)).forEach(prod => {
                        if (prod.disponible && prod.precio_final > 0) {
                          agregar({
                            productoId: prod.id,
                            nombre: prod.nombre,
                            precio: prod.precio_final,
                            sedeId,
                          });
                        }
                      });
                      mostrarAviso(`${productosComparacionSeleccionados.size} producto(s) agregado(s) al carrito.`);
                      setProductosComparacionSeleccionados(new Set());
                    }}
                    className="px-3 py-1.5 bg-brand-blue text-white text-xs font-black rounded-lg border-2 border-brand-blue hover:bg-brand-blue/90 active:scale-[0.95] transition shadow-[2px_2px_0_0_#3f0791]"
                  >
                    Agregar seleccionados
                  </button>
                  <button
                    onClick={() => {
                      if (!sedeId) { mostrarAviso("Elige una sede para buscar alternativas."); return; }
                      const mensaje = `Compara alternativas para: ${comparacionAbierta.productos.filter(p => productosComparacionSeleccionados.has(p.id)).map(p => p.nombre).join(", ")}. Busca mejores opciones.`;
                      chatear(mensaje, sedeId).then(response => {
                        if (response.comparacion) {
                          setComparacionAbierta(response.comparacion);
                          setProductosComparacionSeleccionados(new Set());
                        }
                      }).catch(() => mostrarAviso("No se pudo buscar alternativas."));
                    }}
                    className="px-3 py-1.5 border-2 border-brand-yellow bg-white font-black text-brand-dark text-xs rounded-lg hover:bg-yellow-50 active:scale-[0.95] transition shadow-[2px_2px_0_0_#3f0791]"
                  >
                    Comparar alternativas
                  </button>
                </div>
              )}

              {comparacionAbierta.limitaciones.length > 0 && (
                <details className="border-t-2 border-brand-blue/20 pt-3">
                  <summary className="font-black text-brand-dark cursor-pointer flex items-center justify-between text-sm">
                    <span className="flex items-center gap-1">⚠️ Limitaciones</span>
                    <svg className="w-4 h-4 text-brand-red" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  </summary>
                  <ul className="mt-2 text-xs text-brand-dark/70 space-y-1 ml-4">
                    {comparacionAbierta.limitaciones.map((lim, idx) => (
                      <li key={idx} className="flex gap-1">• {lim}</li>
                    ))}
                  </ul>
                </details>
              )}

              <div className="flex flex-wrap gap-2 border-t-2 border-brand-green/20 pt-4">
                {(comparacionAbierta.mejor_opcion_id && comparacionAbierta.productos.find(p => p.id === comparacionAbierta.mejor_opcion_id)?.disponible) && (
                  <button
                    onClick={() => {
                      if (!sedeId) { mostrarAviso("Elige una sede para agregar productos."); return; }
                      const mejor = comparacionAbierta.productos.find(p => p.id === comparacionAbierta.mejor_opcion_id);
                      if (mejor && mejor.disponible && mejor.precio_final > 0) {
                        agregar({
                          productoId: mejor.id,
                          nombre: mejor.nombre,
                          precio: mejor.precio_final,
                          sedeId,
                        });
                        mostrarAviso(`Mejor opción agregada: ${mejor.nombre}`);
                      }
                    }}
                    className="flex-1 bg-emerald-600 text-white font-black py-3 rounded-xl border-2 border-emerald-600 hover:bg-emerald-600/90 active:scale-[0.98] transition flex items-center justify-center gap-2 shadow-[2px_2px_0_0_#3f0791]"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                    Agregar mejor opción
                  </button>
                )}
                <button
                  onClick={() => {
                    const sinStock = comparacionAbierta.productos.filter(p => !p.disponible || p.precio_final <= 0);
                    if (sinStock.length === 0) { mostrarAviso("No hay productos sin stock ni sin precio en esta comparación."); return; }
                    const mensaje = `Compara solo productos disponibles, excluye: ${sinStock.map(p => p.nombre).join(", ")}.`;
                    chatear(mensaje, sedeId).then(response => {
                      if (response.comparacion) {
                        setComparacionAbierta(response.comparacion);
                        setProductosComparacionSeleccionados(new Set());
                      }
                    }).catch(() => mostrarAviso("No se pudo filtrar la comparación."));
                  }}
                  className="flex-1 border-2 border-brand-yellow bg-white font-black text-brand-dark py-3 rounded-xl hover:bg-yellow-50 active:scale-[0.98] transition flex items-center justify-center gap-2 shadow-[2px_2px_0_0_#3f0791]"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 016.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  Excluir sin stock/precio
                </button>
              </div>
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
            <div className="flex items-center gap-2">
              <span className="font-black flex items-center gap-2">🤖 <span>Aya</span></span>
              {user && (
                <button
                  onClick={() => {
                    setPanelHistorialAbierto(v => !v);
                    if (!panelHistorialAbierto) void cargarListaConversaciones();
                  }}
                  className="ml-2 rounded-lg bg-black/20 hover:bg-black/40 px-2 py-0.5 text-xs font-bold transition flex items-center gap-1 border border-white/20"
                  title="Ver conversaciones anteriores"
                >
                  🕒 Chats
                </button>
              )}
              <button
                onClick={iniciarNuevaConversacion}
                className="rounded-lg bg-black/20 hover:bg-black/40 px-2 py-0.5 text-xs font-bold transition flex items-center gap-1 border border-white/20"
                title="Iniciar nueva conversación"
              >
                ➕ Nuevo
              </button>
            </div>
            <button onClick={() => setAbierto(false)} aria-label="Cerrar" className="text-xl leading-none">×</button>
          </div>

          {/* Panel Desplegable de Conversaciones Guardadas (Neo-Pop) */}
          {panelHistorialAbierto && (
            <div className="border-b-2 border-brand-purple bg-white p-3 max-h-56 overflow-y-auto space-y-2 shadow-inner">
              <div className="flex items-center justify-between text-xs font-black text-brand-purple uppercase tracking-wider">
                <span>Tus conversaciones guardadas</span>
                <button
                  onClick={() => setPanelHistorialAbierto(false)}
                  className="text-gray-500 hover:text-black font-bold"
                >
                  ✕
                </button>
              </div>

              {cargandoHistorial ? (
                <p className="text-xs text-gray-500 py-2">Cargando tus conversaciones...</p>
              ) : listaConversaciones.length === 0 ? (
                <p className="text-xs text-gray-500 py-2">No tienes conversaciones previas guardadas.</p>
              ) : (
                listaConversaciones.map((conv) => {
                  const activa = conv.id === conversacionId;
                  return (
                    <div
                      key={conv.id}
                      onClick={() => void seleccionarConversacion(conv.id)}
                      className={`cursor-pointer rounded-xl border-2 p-2 text-xs transition flex items-center justify-between gap-2 shadow-[2px_2px_0_0_#3f0791] ${
                        activa
                          ? "border-[#e30ba6] bg-pink-50"
                          : "border-gray-200 bg-white hover:border-brand-purple hover:bg-purple-50"
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-bold text-brand-dark">
                          {conv.resumen}
                        </p>
                        <p className="text-[10px] text-gray-500">
                          {conv.mensaje_count} mensajes • {new Date(conv.actualizada_en).toLocaleDateString()}
                        </p>
                      </div>
                      <button
                        onClick={(e) => void borrarConversacionItem(e, conv.id)}
                        className="text-gray-400 hover:text-brand-red p-1 text-sm font-bold"
                        title="Eliminar conversación"
                      >
                        🗑
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          )}

          <div className="bg-brand-yellow px-3 py-1 text-[11px] font-medium text-brand-dark flex items-center justify-between">
            <span>Tu asistente de compras en Neiva • Memoria persistente</span>
            {conversacionId && (
              <span className="text-[9px] bg-white/70 px-1.5 py-0.5 rounded font-mono text-black">
                ID: {conversacionId.slice(0, 8)}
              </span>
            )}
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
                            <SafeIngredientImage
                              src={undefined}
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

                  {/* Tarjeta de presupuesto - Neo-Pop */}
                  {m.presupuesto && (
                    <div className="rounded-2xl border-2 border-brand-green bg-brand-green/5 p-3 shadow-[4px_4px_0_0_#3f0791]">
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="flex items-center gap-2">
                          <span className="w-8 h-8 rounded-xl bg-brand-green flex items-center justify-center text-white text-lg">📊</span>
                          <div>
                            <p className="font-black text-brand-dark text-sm">Presupuesto de Mercado</p>
                            <p className="text-xs text-brand-dark/70">{m.presupuesto.resumen_usuario}</p>
                          </div>
                        </div>
                        <button onClick={() => setPresupuestoAbierto(m.presupuesto!)} className="shrink-0 px-3 py-1.5 rounded-lg border-2 border-brand-green bg-white font-black text-brand-green text-xs hover:bg-brand-green/10 active:scale-[0.97] transition">Ver detalle →</button>
                      </div>

                      <div className="flex flex-wrap gap-1.5 mb-3">
                        <span className="px-3 py-1 bg-brand-yellow text-brand-dark rounded-full text-[10px] font-black border-2 border-brand-yellow/50 shadow-[2px_2px_0_0_#3f0791]">
                          Total: {cop.format(m.presupuesto.total_con_precio)}
                        </span>
                        {m.presupuesto.presupuesto_limite && (
                          <span className={`px-3 py-1 rounded-full text-[10px] font-black border-2 shadow-[2px_2px_0_0_#3f0791] ${m.presupuesto.presupuesto_excedido ? "bg-brand-red text-white border-brand-red" : "bg-brand-green text-white border-brand-green"}`}>
                            Límite: {cop.format(m.presupuesto.presupuesto_limite)}
                          </span>
                        )}
                        <span className="px-3 py-1 bg-white text-gray-700 rounded-full text-[10px] font-black border-2 border-gray-200 shadow-[2px_2px_0_0_#3f0791]">
                          {m.presupuesto.items.length} items
                        </span>
                      </div>

                      <div className="space-y-1 max-h-36 overflow-y-auto border-t border-brand-green/20 pt-2">
                        {m.presupuesto.items.slice(0, 6).map((item, idx) => (
                          <div key={idx} className="flex items-center justify-between py-1.5 px-2 rounded-lg bg-white/50 border border-gray-100 group hover:border-brand-green/30 transition">
                            <div className="flex items-center gap-2 min-w-0 flex-1">
                              <div className="w-10 h-10 rounded-lg bg-brand-green/10 flex items-center justify-center flex-shrink-0">
                                <SafeImage
                                  src={undefined}
                                  alt={item.termino_busqueda}
                                  fill
                                  className="object-contain"
                                  sizes="40px"
                                  fallbackType="producto"
                                />
                              </div>
                              <div className="min-w-0">
                                <p className="text-xs font-black text-brand-dark truncate">{item.cantidad}x {item.termino_busqueda}</p>
                                <p className="text-[10px] text-brand-dark/50">{item.estado === "disponible" ? "✓ Disponible" : item.estado === "sin_stock" ? "⚠ Sin stock" : "✗ No encontrado"}</p>
                              </div>
                            </div>
                            <span className="font-black text-brand-dark text-xs whitespace-nowrap">{cop.format(item.subtotal)}</span>
                          </div>
                        ))}
                        {m.presupuesto.items.length > 6 && (
                          <div className="text-[10px] text-brand-dark/50 text-center py-1 border-t border-brand-green/20">+{m.presupuesto.items.length - 6} items más</div>
                        )}
                      </div>

                      <div className="mt-3 pt-3 border-t border-brand-green/20 flex gap-2">
                        <button onClick={() => {
                          if (sedeId === null) { mostrarAviso("Elige una sede para agregar productos."); return; }
                          m.presupuesto!.items.forEach(item => {
                            if (item.producto_id && item.estado === "disponible") {
                              agregar({
                                productoId: item.producto_id,
                                nombre: item.producto_nombre ?? item.termino_busqueda,
                                precio: item.precio_unitario,
                                sedeId,
                              }, item.cantidad);
                            }
                          });
                          mostrarAviso("Productos del presupuesto agregados al carrito.");
                        }} className="flex-1 px-3 py-2 rounded-xl border-2 border-brand-green bg-brand-green text-white font-black text-xs hover:bg-brand-green/90 active:scale-[0.97] transition flex items-center justify-center gap-1.5 shadow-[2px_2px_0_0_#3f0791]">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
                          Agregar disponibles
                        </button>
                        <button onClick={() => setPresupuestoAbierto(m.presupuesto!)} className="px-3 py-2 rounded-xl border-2 border-brand-yellow bg-white font-black text-brand-dark text-xs hover:bg-yellow-50 active:scale-[0.97] transition flex items-center justify-center gap-1.5 shadow-[2px_2px_0_0_#3f0791]">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                          Ver todo
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Tarjeta de comparación - Neo-Pop */}
                  {m.comparacion && (
                    <div className="rounded-2xl border-2 border-brand-blue bg-brand-blue/5 p-3 shadow-[4px_4px_0_0_#3f0791]">
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="flex items-center gap-2">
                          <span className="w-8 h-8 rounded-xl bg-brand-blue flex items-center justify-center text-white text-lg">⚖️</span>
                          <div>
                            <p className="font-black text-brand-dark text-sm">Comparación: {m.comparacion.criterio}</p>
                            <p className="text-xs text-brand-dark/70">{m.comparacion.explicacion}</p>
                          </div>
                        </div>
                        <button onClick={() => setComparacionAbierta(m.comparacion!)} className="shrink-0 px-3 py-1.5 rounded-lg border-2 border-brand-blue bg-white font-black text-brand-blue text-xs hover:bg-brand-blue/10 active:scale-[0.97] transition">Ver detalle →</button>
                      </div>

                      <div className="flex flex-wrap gap-1.5 mb-3">
                        <span className="px-3 py-1 bg-brand-yellow text-brand-dark rounded-full text-[10px] font-black border-2 border-brand-yellow/50 shadow-[2px_2px_0_0_#3f0791]">{m.comparacion.tipo_comparacion}</span>
                        <span className="px-3 py-1 bg-white text-gray-700 rounded-full text-[10px] font-black border-2 border-gray-200 shadow-[2px_2px_0_0_#3f0791]">{m.comparacion.productos.length} opciones</span>
                        {m.comparacion.mejor_opcion_id && (
                          <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-[10px] font-black border-2 border-emerald-300 shadow-[2px_2px_0_0_#3f0791]">Mejor opción ✓</span>
                        )}
                      </div>

                      <div className="space-y-1.5 max-h-44 overflow-y-auto border-t border-brand-blue/20 pt-2">
                        {m.comparacion.productos.slice(0, 5).map((prod, idx) => (
                          <div key={prod.id} className={`flex items-center gap-3 p-2.5 rounded-xl border-2 ${prod.id === m.comparacion?.mejor_opcion_id ? "bg-emerald-50 border-emerald-300 shadow-[2px_2px_0_0_#059669]" : "bg-white border-gray-200 shadow-sm hover:border-brand-blue/50 hover:shadow-[2px_2px_0_0_#3f0791] transition"}`}>
                            <div className="w-14 h-14 rounded-lg bg-brand-blue/10 flex items-center justify-center flex-shrink-0 overflow-hidden relative">
                              <SafeImage
                                src={undefined}
                                alt={prod.nombre}
                                fill
                                className="object-cover"
                                sizes="56px"
                                fallbackType="producto"
                              />
                              {prod.id === m.comparacion?.mejor_opcion_id && (
                                <span className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 text-white text-[9px] font-black flex items-center justify-center border-2 border-white">✓</span>
                              )}
                              {!prod.disponible && (
                                <span className="absolute inset-0 bg-red-500/60 flex items-center justify-center">
                                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                </span>
                              )}
                              {prod.precio_final <= 0 && (
                                <span className="absolute inset-0 bg-gray-500/60 flex items-center justify-center">
                                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                                </span>
                              )}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-xs font-black text-brand-dark truncate">{prod.nombre}</p>
                              <p className="text-[10px] text-brand-dark/50 truncate">{prod.marca ?? ""} {prod.presentacion ?? ""}</p>
                              {prod.razones.length > 0 && (
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {prod.razones.slice(0, 2).map((razon, rIdx) => (
                                    <span key={rIdx} className="text-[9px] bg-brand-blue/10 text-brand-blue px-1.5 py-0.5 rounded">{razon}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                            <div className="text-right min-w-[90px]">
                              <p className="text-xs font-extrabold text-brand-red">{cop.format(prod.precio_final)}</p>
                              {prod.precio_por_unidad_base && (
                                <p className="text-[9px] text-brand-dark/50">{cop.format(prod.precio_por_unidad_base)}/{prod.unidad_medida}</p>
                              )}
                              {prod.tiene_promocion && <span className="text-[9px] bg-brand-red/10 text-brand-red px-1.5 py-0.5 rounded">🏷 Promo</span>}
                            </div>
                          </div>
                        ))}
                        {m.comparacion.productos.length > 5 && (
                          <div className="text-[10px] text-brand-dark/50 text-center py-2 border-t border-brand-blue/20 flex items-center justify-center gap-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                            +{m.comparacion.productos.length - 5} opciones más
                          </div>
                        )}
                      </div>

                      {m.comparacion.limitaciones.length > 0 && (
                        <details className="mt-3 pt-3 border-t border-brand-blue/20">
                          <summary className="text-xs text-brand-blue cursor-pointer font-bold flex items-center gap-1">⚠️ Limitaciones ({m.comparacion.limitaciones.length})</summary>
                          <ul className="mt-2 text-[10px] text-brand-dark/60 space-y-1 ml-4">
                            {m.comparacion.limitaciones.map((lim, idx) => (
                              <li key={idx} className="flex gap-1">• {lim}</li>
                            ))}
                          </ul>
                        </details>
                      )}
                    </div>
                  )}

                  {/* Feedback visual de acciones de carrito - muestra acciones solicitadas y resultados reales */}
                  {m.cart_actions && m.cart_actions.length > 0 && (
                    <div className="rounded-xl border-2 border-brand-purple/30 bg-brand-purple/5 p-3 shadow-sm">
                      <p className="font-black text-brand-dark text-xs mb-2">🛒 Acciones de carrito:</p>
                      <div className="space-y-1">
                        {m.cart_actions.map((accion, idx) => (
                          <div key={idx} className="text-xs text-brand-dark/80 flex items-center gap-2">
                            {accion.tipo === "add" && (
                              <>
                                <span className="text-emerald-600">➕</span>
                                <span>Solicitado: agregar {accion.items.length} producto(s)</span>
                              </>
                            )}
                            {accion.tipo === "remove" && (
                              <>
                                <span className="text-brand-red">➖</span>
                                <span>Solicitado: quitar {accion.producto_ids.length} producto(s)</span>
                              </>
                            )}
                            {accion.tipo === "update" && (
                              <>
                                <span className="text-brand-blue">🔄</span>
                                <span>Solicitado: actualizar {accion.items.length} producto(s)</span>
                              </>
                            )}
                            {accion.tipo === "confirm_clear" && (
                              <>
                                <span className="text-amber-600">⚠️</span>
                                <span>Confirmación requerida para vaciar carrito</span>
                              </>
                            )}
                            {accion.tipo === "clear" && (
                              <>
                                <span className="text-gray-600">🗑</span>
                                <span>Carrito vaciado</span>
                              </>
                            )}
                            {accion.tipo === "list" && (
                              <>
                                <span className="text-gray-600">📋</span>
                                <span>Mostrar contenido del carrito</span>
                              </>
                            )}
                          </div>
                        ))}
                      </div>
                      <p className="text-[10px] text-brand-dark/50 mt-2">Los resultados reales se muestran en el mensaje de Aya arriba.</p>
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