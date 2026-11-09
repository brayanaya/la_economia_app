"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";
import EstadoVacio from "@/components/EstadoVacio";
import FooterCompliance from "@/components/FooterCompliance";
import { useCarrito, type ItemCarrito } from "@/context/CarritoContext";
import { useAuth } from "@/context/AuthContext";
import { useEffect } from "react";
import { mostrarAviso } from "@/lib/aviso";
import { crearOrden, type OrdenCreada, type MetodoPago, iniciarPagoWompi } from "@/lib/ordenes";
import { nombreSede } from "@/lib/sedes";
import { SafeImage } from "@/components/SafeImage";
import { QrCode, Smartphone, CreditCard, Truck, Shield } from "lucide-react";

const COP = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

const METODOS_PAGO: { value: MetodoPago; label: string; icon: React.ReactNode; descripcion: string }[] = [
  { value: "contra_entrega", label: "Contra entrega", icon: <Truck className="w-5 h-5" />, descripcion: "Pagas al recibir (efectivo, Nequi, Daviplata)" },
  { value: "wompi", label: "Pago en línea (Wompi)", icon: <CreditCard className="w-5 h-5" />, descripcion: "Tarjeta, PSE, Nequi, Bancolombia - Seguro y rápido" },
  { value: "bre_b", label: "Bre-B", icon: <QrCode className="w-5 h-5" />, descripcion: "Transferencia inmediata entre bancos" },
];

const CAMPO =
  "h-12 w-full rounded-[18px] border-2 bg-white px-4 text-[#6B1020] outline-none transition-all duration-200 placeholder:text-[#6B1020]/50 focus:ring-4 focus:ring-[#6B1020]/20";
const ETIQUETA = "mb-1.5 block text-sm font-black text-[#6B1020]";
const ERROR = "mt-1.5 text-sm font-bold text-[#B42335]";

function normalizarCelular(valor: string): string {
  const digitos = valor.replace(/\D/g, "");
  return digitos.length === 12 && digitos.startsWith("57") ? digitos.slice(2) : digitos;
}

function validar(v: { nombre: string; telefono: string; direccion: string; acepta: boolean }): Record<string, string> {
  const e: Record<string, string> = {};
  if (v.nombre.trim().length < 2) e.nombre = "Ingresa tu nombre completo.";
  if (!/^3\d{9}$/.test(normalizarCelular(v.telefono))) {
    e.telefono = "Ingresa un celular colombiano de 10 dígitos, por ejemplo 310 123 4567.";
  }
  if (v.direccion.trim().length < 6) e.direccion = "Ingresa una dirección de entrega más completa.";
  if (!v.acepta) e.acepta = "Debes autorizar el tratamiento de tus datos personales (Ley 1581 de 2012).";
  return e;
}

interface GrupoSede {
  sedeId: string;
  sedeNombre: string;
  items: ItemCarrito[];
  subtotal: number;
}

interface OrdenConfirmada {
  orden: OrdenCreada;
  sedeNombre: string;
}

type Errores = Partial<Record<"nombre" | "telefono" | "direccion" | "acepta", string>>;

export default function CheckoutPage() {
  const router = useRouter();
  const { items, hidratado, totalItems, totalPrecio, vaciarSede } = useCarrito();
  const { user, loading: authLoading } = useAuth();
  useEffect(() => {
    if (!authLoading && !user) router.replace("/cuenta?returnTo=%2Fcheckout");
  }, [authLoading, user, router]);

  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [direccion, setDireccion] = useState("");
  const [metodo, setMetodo] = useState<MetodoPago>("contra_entrega");
  const [acepta, setAcepta] = useState(false);
  const [errores, setErrores] = useState<Errores>({});
  const [enviando, setEnviando] = useState(false);
  const [errorGlobal, setErrorGlobal] = useState<string | null>(null);
  const [creadas, setCreadas] = useState<OrdenConfirmada[]>([]);
  const [redirigiendo, setRedirigiendo] = useState(false);
  const [wompiLoading, setWompiLoading] = useState(false);

  const grupos = useMemo<GrupoSede[]>(() => {
    const mapa = new Map<string, GrupoSede>();
    for (const it of items) {
      const g: GrupoSede = mapa.get(it.sedeId) ?? {
        sedeId: it.sedeId,
        sedeNombre: nombreSede(it.sedeId, it.sedeNombre),
        items: [],
        subtotal: 0,
      };
      g.items.push(it);
      g.subtotal += it.precio * it.cantidad;
      mapa.set(it.sedeId, g);
    }
    return Array.from(mapa.values());
  }, [items]);

  async function confirmar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (enviando || wompiLoading) return;
    if (authLoading || !user) { router.replace("/cuenta?returnTo=%2Fcheckout"); return; }

    const nuevos = validar({ nombre, telefono, direccion, acepta });
    setErrores(nuevos);
    setErrorGlobal(null);
    if (Object.keys(nuevos).length > 0) return;

    // If Wompi, initiate payment flow
    if (metodo === "wompi") {
      await iniciarPagoWompiFlow();
      return;
    }

    setEnviando(true);
    const celular = normalizarCelular(telefono);
    const exitosas: OrdenConfirmada[] = [];
    const fallos: string[] = [];

    for (const g of grupos) {
      try {
        const orden = await crearOrden({
          sede_id: g.sedeId,
          cliente_nombre: nombre.trim(),
          cliente_telefono: celular,
          notas: `Dirección: ${direccion.trim()} | Pago: ${metodo}`,
          metodo_pago: metodo,
          items: g.items.map((i) => ({
            producto_id: i.productoId,
            nombre: i.nombre,
            cantidad: i.cantidad,
            precio_unitario: i.precio,
            imagen_url: i.imagen ?? null,
          })),
        });
        exitosas.push({ orden, sedeNombre: g.sedeNombre });
        vaciarSede(g.sedeId);
      } catch (err) {
        fallos.push(`${g.sedeNombre}: ${err instanceof Error ? err.message : "error desconocido"}`);
      }
    }

    setEnviando(false);

    if (exitosas.length === 1 && fallos.length === 0 && grupos.length === 1) {
      setRedirigiendo(true);
      router.push(`/pedidos/${exitosas[0].orden.id}?nuevo=1`);
      return;
    }

    if (exitosas.length > 0) setCreadas((previas) => [...previas, ...exitosas]);
    if (fallos.length > 0) {
      setErrorGlobal(fallos.join(" | "));
      mostrarAviso("Error al procesar la orden. Inténtalo de nuevo.");
    }
  }

  async function iniciarPagoWompiFlow() {
    setWompiLoading(true);
    setErrorGlobal(null);
    const celular = normalizarCelular(telefono);

    try {
      // Create orders first (one per sede)
      const ordenesCreadas: OrdenConfirmada[] = [];
      for (const g of grupos) {
        const orden = await crearOrden({
          sede_id: g.sedeId,
          cliente_nombre: nombre.trim(),
          cliente_telefono: celular,
          notas: `Dirección: ${direccion.trim()} | Pago: wompi`,
          metodo_pago: "wompi",
          items: g.items.map((i) => ({
            producto_id: i.productoId,
            nombre: i.nombre,
            cantidad: i.cantidad,
            precio_unitario: i.precio,
            imagen_url: i.imagen ?? null,
          })),
        });
        ordenesCreadas.push({ orden, sedeNombre: g.sedeNombre });
        vaciarSede(g.sedeId);
      }

      // For now, use the first order to initiate Wompi payment
      // In a multi-sede scenario, we'd need to handle multiple payments
      const primeraOrden = ordenesCreadas[0];
      const { accion, campos } = await iniciarPagoWompi(primeraOrden.orden.id);

      // Redirect to Wompi checkout via form POST
      const form = document.createElement("form");
      form.method = "POST";
      form.action = accion;
      form.style.display = "none";
      for (const [key, value] of Object.entries(campos)) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = key;
        input.value = value;
        form.appendChild(input);
      }
      document.body.appendChild(form);
      form.submit();
    } catch (err) {
      setErrorGlobal(err instanceof Error ? err.message : "Error al iniciar el pago con Wompi");
      mostrarAviso("No pudimos iniciar el pago. Inténtalo de nuevo.");
    } finally {
      setWompiLoading(false);
    }
  }

  const completo = creadas.length > 0 && items.length === 0;

  const metodoActual = METODOS_PAGO.find(m => m.value === metodo)!;

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b-3 border-black bg-gradient-to-r from-[#3f0791] via-[#5b0cb5] to-[#e30ba6]">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-4 py-3">
          <Link href="/" className="flex min-w-0 items-center gap-2 sm:gap-3">
            <SafeImage src="/logo.png" alt="La Economía Aya" width={80} height={32} className="h-8 w-auto sm:h-10" fallbackType="general" />
            <span className="hidden text-lg font-black tracking-tight text-white sm:inline">La Economía Aya</span>
          </Link>
          <Link
            href="/"
            className="shrink-0 whitespace-nowrap rounded-xl border-2 border-black bg-white px-3 py-1.5 text-xs font-black text-black transition-all duration-200 shadow-[2px_2px_0_0_#000000] hover:bg-gray-100 active:translate-x-0.5 active:translate-y-0.5 active:shadow-none sm:px-4 sm:text-sm"
          >
            ← Volver a la tienda
          </Link>
        </div>
      </header>

      <main className="bg-gradient-to-b from-[#faf7ff] via-[#fff5fb] to-[#f4eeff]">
        <div className="mx-auto max-w-5xl px-4 py-10">
          {!hidratado && <div aria-busy="true" className="h-96 animate-pulse rounded-2xl bg-white/60 border-2 border-black" />}

          {redirigiendo && (
            <div
              role="status"
              aria-live="polite"
              className="mx-auto max-w-2xl rounded-2xl border-3 border-black bg-white p-10 text-center shadow-[8px_8px_0_0_#3f0791]"
            >
              <p className="text-2xl font-black leading-none tracking-tight text-[#3f0791]">Pedido registrado</p>
              <p className="mt-2 text-black/80 font-bold">Abriendo tu ticket…</p>
            </div>
          )}

          {hidratado && completo && (
            <section
              aria-live="polite"
              className="anim-aparecer mx-auto max-w-2xl rounded-3xl border-3 border-black bg-white p-8 text-center shadow-[8px_8px_0_0_#3f0791] sm:p-10"
            >
              <div aria-hidden="true" className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-2xl border-2 border-black bg-[#ffcc00] text-4xl font-black text-[#3f0791] shadow-[3px_3px_0_0_#000000]">✓</div>
              <h1 className="text-4xl font-black leading-none tracking-tight text-black">¡Pedidos confirmados!</h1>
              <p className="mt-3 text-gray-700 font-bold">
                Gracias, {nombre.trim()}. Guardamos tus pedidos con el método de pago <strong className="text-[#3f0791]">{metodoActual.label}</strong>.
              </p>
              <ul className="mt-6 space-y-2 text-left">
                {creadas.map(({ orden, sedeNombre }) => (
                  <li key={orden.id} className="rounded-xl border-2 border-black p-4 bg-[#faf7ff] text-black shadow-[2px_2px_0_0_#000000]">
                    <Link href={`/pedidos/${orden.id}`} className="font-black text-[#3f0791] underline underline-offset-2 hover:text-[#e30ba6]">
                      Pedido #{orden.id.slice(0, 8).toUpperCase()}
                    </Link>
                    <span className="block text-sm font-bold mt-1">Sede {sedeNombre} · {COP.format(Number(orden.total))}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-sm font-medium text-gray-600">Entrega en: {direccion.trim()} · Contacto: {telefono.trim()}</p>
              <Link href="/" className="mt-8 inline-block rounded-xl border-2 border-black bg-[#3f0791] px-8 py-3 font-black text-white transition-all shadow-[4px_4px_0_0_#e30ba6] hover:-translate-y-0.5 hover:bg-[#320575] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none">
                Seguir comprando
              </Link>
            </section>
          )}

          {hidratado && !completo && !redirigiendo && items.length === 0 && (
            <EstadoVacio
              titulo="Tu carrito está vacío"
              detalle="Agrega productos desde el catálogo para poder finalizar tu compra."
              accion={{ texto: "Volver al catálogo", href: "/" }}
            />
          )}

          {hidratado && items.length > 0 && (
            <>
              <h1 className="text-4xl font-black leading-none tracking-tight text-black sm:text-5xl">Finalizar compra</h1>
              <p className="mb-8 mt-2 font-bold text-[#3f0791]">Revisa tu pedido y completa tus datos de entrega en Neiva.</p>

              {creadas.length > 0 && (
                <div className="mb-6 rounded-2xl border-2 border-black bg-white p-4 text-sm text-black shadow-[3px_3px_0_0_#3f0791]">
                  <p className="font-black text-[#3f0791]">Estos pedidos ya quedaron registrados:</p>
                  <ul className="mt-1 font-bold">
                    {creadas.map(({ orden, sedeNombre }) => (
                      <li key={orden.id}>#{orden.id.slice(0, 8).toUpperCase()} · Sede {sedeNombre}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
                <form onSubmit={confirmar} noValidate aria-label="Datos de entrega y pago" className="space-y-5 rounded-3xl border-3 border-black bg-white p-6 shadow-[8px_8px_0_0_#3f0791] sm:p-8">
                  <div>
                    <label htmlFor="nombre" className="mb-1.5 block text-xs font-black uppercase tracking-wider text-[#3f0791]">Nombre completo</label>
                    <input id="nombre" value={nombre} onChange={(ev) => setNombre(ev.target.value)} maxLength={120} autoComplete="name" aria-invalid={Boolean(errores.nombre)} aria-describedby={errores.nombre ? "nombre-error" : undefined} className={`h-12 w-full rounded-xl border-2 bg-white px-4 text-black font-medium outline-none transition-all shadow-[2px_2px_0_0_#3f0791] focus:ring-2 focus:ring-[#e30ba6]/30 ${errores.nombre ? "border-red-600" : "border-black"}`} />
                    {errores.nombre && <p id="nombre-error" role="alert" className="mt-1.5 text-xs font-bold text-red-600">{errores.nombre}</p>}
                  </div>

                  <div>
                    <label htmlFor="telefono" className="mb-1.5 block text-xs font-black uppercase tracking-wider text-[#3f0791]">Teléfono celular</label>
                    <input id="telefono" value={telefono} onChange={(ev) => setTelefono(ev.target.value)} maxLength={20} inputMode="tel" autoComplete="tel" placeholder="310 123 4567" aria-invalid={Boolean(errores.telefono)} aria-describedby={errores.telefono ? "telefono-error" : undefined} className={`h-12 w-full rounded-xl border-2 bg-white px-4 text-black font-medium outline-none transition-all shadow-[2px_2px_0_0_#3f0791] focus:ring-2 focus:ring-[#e30ba6]/30 ${errores.telefono ? "border-red-600" : "border-black"}`} />
                    {errores.telefono && <p id="telefono-error" role="alert" className="mt-1.5 text-xs font-bold text-red-600">{errores.telefono}</p>}
                  </div>

                  <div>
                    <label htmlFor="direccion" className="mb-1.5 block text-xs font-black uppercase tracking-wider text-[#3f0791]">Dirección de entrega en Neiva</label>
                    <input id="direccion" value={direccion} onChange={(ev) => setDireccion(ev.target.value)} maxLength={200} autoComplete="street-address" placeholder="Ej: Calle 10 Sur #21-92, Barrio Santa Isabel" aria-invalid={Boolean(errores.direccion)} aria-describedby={errores.direccion ? "direccion-error" : undefined} className={`h-12 w-full rounded-xl border-2 bg-white px-4 text-black font-medium outline-none transition-all shadow-[2px_2px_0_0_#3f0791] focus:ring-2 focus:ring-[#e30ba6]/30 ${errores.direccion ? "border-red-600" : "border-black"}`} />
                    {errores.direccion && <p id="direccion-error" role="alert" className="mt-1.5 text-xs font-bold text-red-600">{errores.direccion}</p>}
                  </div>

                  <div>
                    <label htmlFor="metodo" className="mb-2 block text-xs font-black uppercase tracking-wider text-[#3f0791]">Método de pago flexible</label>
                    <div className="grid gap-3 sm:grid-cols-3">
                      {METODOS_PAGO.map((m) => (
                        <label key={m.value} className={`relative cursor-pointer rounded-2xl border-2 p-3.5 transition-all ${metodo === m.value ? "border-black bg-[#3f0791] text-white shadow-[4px_4px_0_0_#e30ba6]" : "border-black/20 bg-white text-black hover:border-black shadow-sm"}`}>
                          <input
                            type="radio"
                            name="metodo"
                            value={m.value}
                            checked={metodo === m.value}
                            onChange={() => setMetodo(m.value)}
                            className="sr-only"
                            disabled={authLoading || !user}
                          />
                          <div className="flex flex-col gap-2">
                            <div className="flex items-center justify-between">
                              <div className={`flex h-9 w-9 items-center justify-center rounded-xl border-2 border-black ${metodo === m.value ? "bg-[#ffcc00] text-black" : "bg-[#faf7ff] text-[#3f0791]"}`}>{m.icon}</div>
                              {metodo === m.value && <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#ffcc00] text-black text-xs font-black border border-black">✓</div>}
                            </div>
                            <div>
                              <p className="font-black text-sm">{m.label}</p>
                              <p className={`text-[11px] leading-tight font-medium mt-0.5 ${metodo === m.value ? "text-white/85" : "text-gray-500"}`}>{m.descripcion}</p>
                            </div>
                          </div>
                        </label>
                      ))}
                    </div>

                    {metodo === "bre_b" && (
                      <div className="mt-3 rounded-2xl border-2 border-black bg-gradient-to-r from-[#faf7ff] to-[#fff0fa] p-4 shadow-[2px_2px_0_0_#3f0791]">
                        <div className="flex items-start gap-3">
                          <Smartphone className="shrink-0 mt-0.5 h-5 w-5 text-[#3f0791]" />
                          <div className="text-xs text-black font-medium leading-relaxed">
                            <p className="font-black text-sm text-[#3f0791]">Transferencia Inmediata Bre-B</p>
                            <p className="mt-0.5">Al confirmar, obtendrás el ticket con el código QR y las llaves oficiales del comercio (Celular y Llave Alfanumérica) para transferir desde cualquier banco sin comisiones.</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {metodo === "wompi" && (
                      <div className="mt-3 rounded-2xl border-2 border-black bg-white p-4 shadow-[2px_2px_0_0_#3f0791]">
                        <div className="flex items-start gap-3">
                          <Shield className="shrink-0 mt-0.5 h-5 w-5 text-[#3f0791]" />
                          <div className="text-xs text-black font-medium leading-relaxed">
                            <p className="font-black text-sm text-[#3f0791]">Pago Cifrado con Wompi</p>
                            <p className="mt-0.5">Serás redirigido al Web Checkout protegido de Wompi con firma criptográfica de integridad SHA-256 (PSE, Bancolombia, Nequi, tarjetas de crédito y débito).</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {metodo === "contra_entrega" && (
                      <div className="mt-3 rounded-2xl border-2 border-black bg-white p-4 shadow-[2px_2px_0_0_#3f0791]">
                        <div className="flex items-start gap-3">
                          <Truck className="shrink-0 mt-0.5 h-5 w-5 text-[#3f0791]" />
                          <div className="text-xs text-black font-medium leading-relaxed">
                            <p className="font-black text-sm text-[#3f0791]">Pago al Recibir en Domicilio</p>
                            <p className="mt-0.5">El repartidor de La Economía Aya llevará datáfono y código QR para recibir en efectivo o billeteras digitales en tu puerta.</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="flex cursor-pointer items-start gap-3 text-xs text-black font-bold">
                      <input type="checkbox" checked={acepta} onChange={(ev) => setAcepta(ev.target.checked)} aria-invalid={Boolean(errores.acepta)} aria-describedby={errores.acepta ? "acepta-error" : undefined} className="mt-0.5 h-4 w-4 accent-[#3f0791] border-2 border-black rounded" />
                      <span>Autorizo el tratamiento de mis datos personales para gestionar este pedido (Ley 1581 de 2012 - Habeas Data).</span>
                    </label>
                    <p className="ml-7 mt-1 text-[11px]"><Link href="/privacidad" target="_blank" className="font-bold text-[#3f0791] underline underline-offset-2">Consultar la política de privacidad</Link></p>
                    {errores.acepta && <p id="acepta-error" role="alert" className="mt-1 text-xs font-bold text-red-600">{errores.acepta}</p>}
                  </div>

                  {errorGlobal && <p role="alert" className="rounded-xl border-2 border-black bg-red-100 p-3 text-xs font-bold text-red-800">{errorGlobal}</p>}

                  <button type="submit" disabled={enviando || wompiLoading} className="w-full rounded-2xl border-2 border-black bg-[#3f0791] py-4 text-base font-black text-white transition-all shadow-[4px_4px_0_0_#e30ba6] hover:-translate-y-0.5 hover:bg-[#320575] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none disabled:cursor-wait disabled:opacity-70 flex items-center justify-center gap-2">
                    {wompiLoading ? "Conectando con Wompi…" : enviando ? "Procesando pedido…" : `Confirmar pedido · ${COP.format(totalPrecio)}`}
                  </button>
                </form>

                <aside aria-label="Resumen del pedido" className="h-fit rounded-3xl border-3 border-black bg-white p-6 shadow-[6px_6px_0_0_#3f0791] lg:sticky lg:top-6">
                  <h2 className="text-2xl font-black leading-none tracking-tight text-black">Tu pedido</h2>
                  {grupos.map((g) => (
                    <section key={g.sedeId} className="mt-5">
                      <h3 className="text-xs font-black uppercase tracking-wide text-[#3f0791] bg-[#faf7ff] px-2 py-1 rounded border border-black/10 inline-block">Sede {g.sedeNombre}</h3>
                      <ul className="mt-2 divide-y border-t border-b border-black/10">
                        {g.items.map((it) => (
                          <li key={`${it.sedeId}-${it.productoId}`} className="flex items-start justify-between gap-3 py-2 text-xs text-black">
                            <span>{it.nombre} <span className="font-black">× {it.cantidad}</span></span>
                            <span className="font-bold">{COP.format(it.precio * it.cantidad)}</span>
                          </li>
                        ))}
                      </ul>
                      <p className="mt-1 text-right text-xs font-bold text-gray-700">Subtotal: {COP.format(g.subtotal)}</p>
                    </section>
                  ))}
                  <div className="mt-5 flex items-center justify-between border-t-2 border-black pt-4">
                    <span className="font-bold text-black text-sm">Total ({totalItems} uds.)</span>
                    <span className="text-2xl font-black tracking-tight text-[#3f0791]">{COP.format(totalPrecio)}</span>
                  </div>
                  {grupos.length > 1 && <p className="mt-3 text-xs font-medium text-gray-500">Tu carrito tiene productos de {grupos.length} sedes: se generará un pedido por cada sede.</p>}
                </aside>
              </div>
            </>
          )}
        </div>
      </main>

      <FooterCompliance />
    </div>
  );
}