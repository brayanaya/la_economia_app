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
import { crearOrden, type OrdenCreada } from "@/lib/ordenes";
import { nombreSede } from "@/lib/sedes";

const COP = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

const METODOS_PAGO = ["Contra entrega", "Bre-B"] as const;
type MetodoPago = (typeof METODOS_PAGO)[number];

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

const CAMPO =
  "h-12 w-full rounded-[18px] border-2 bg-white px-4 text-[#6B1020] outline-none transition-all duration-200 placeholder:text-[#6B1020]/50 focus:ring-4 focus:ring-[#6B1020]/20";
const ETIQUETA = "mb-1.5 block text-sm font-black text-[#6B1020]";
const ERROR = "mt-1.5 text-sm font-bold text-[#B42335]";

function normalizarCelular(valor: string): string {
  const digitos = valor.replace(/\D/g, "");
  return digitos.length === 12 && digitos.startsWith("57") ? digitos.slice(2) : digitos;
}

function validar(v: { nombre: string; telefono: string; direccion: string; acepta: boolean }): Errores {
  const e: Errores = {};
  if (v.nombre.trim().length < 2) e.nombre = "Ingresa tu nombre completo.";
  if (!/^3\d{9}$/.test(normalizarCelular(v.telefono))) {
    e.telefono = "Ingresa un celular colombiano de 10 dígitos, por ejemplo 310 123 4567.";
  }
  if (v.direccion.trim().length < 6) e.direccion = "Ingresa una dirección de entrega más completa.";
  if (!v.acepta) e.acepta = "Debes autorizar el tratamiento de tus datos personales (Ley 1581 de 2012).";
  return e;
}

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
  const [metodo, setMetodo] = useState<MetodoPago>("Contra entrega");
  const [acepta, setAcepta] = useState(false);
  const [errores, setErrores] = useState<Errores>({});
  const [enviando, setEnviando] = useState(false);
  const [errorGlobal, setErrorGlobal] = useState<string | null>(null);
  const [creadas, setCreadas] = useState<OrdenConfirmada[]>([]);
  const [redirigiendo, setRedirigiendo] = useState(false);

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
    if (enviando) return;
    if (authLoading || !user) { router.replace("/cuenta?returnTo=%2Fcheckout"); return; }

    const nuevos = validar({ nombre, telefono, direccion, acepta });
    setErrores(nuevos);
    setErrorGlobal(null);
    if (Object.keys(nuevos).length > 0) return;

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

  const completo = creadas.length > 0 && items.length === 0;

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b-4 border-[#8B1E2D] bg-[#6B1020]">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-4 py-3">
          <Link href="/" className="flex min-w-0 items-center gap-2 sm:gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="La Economía Aya" className="h-8 w-auto sm:h-10" />
            <span className="hidden text-lg font-black tracking-tight text-white sm:inline">La Economía Aya</span>
          </Link>
          <Link
            href="/"
            className="shrink-0 whitespace-nowrap rounded-[52px] border-2 border-white/80 px-3 py-1.5 text-xs font-black text-white transition-all duration-200 hover:bg-white hover:text-[#6B1020] active:scale-95 sm:px-4 sm:text-sm"
          >
            ← Volver a la tienda
          </Link>
        </div>
      </header>

      <main className="bg-[#F3E6D9]">
        <div className="mx-auto max-w-5xl px-4 py-10">
          {!hidratado && <div aria-busy="true" className="h-96 animate-pulse rounded-[25px] bg-white/60" />}

          {redirigiendo && (
            <div
              role="status"
              aria-live="polite"
              className="mx-auto max-w-2xl rounded-[25px] border-2 border-[#6B1020] bg-white p-10 text-center shadow-xl"
            >
              <p className="text-2xl font-black leading-none tracking-tight text-[#6B1020]">Pedido registrado</p>
              <p className="mt-2 text-[#6B1020]/80">Abriendo tu ticket…</p>
            </div>
          )}

          {hidratado && completo && (
            <section
              aria-live="polite"
              className="anim-aparecer mx-auto max-w-2xl rounded-[25px] border-2 border-[#6B1020] bg-white p-8 text-center shadow-xl sm:p-10"
            >
              <div
                aria-hidden="true"
                className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full border-2 border-[#6B1020] bg-[#F3E6D9] text-4xl font-black text-[#6B1020]"
              >
                ✓
              </div>
              <h1 className="text-4xl font-black leading-none tracking-tight text-[#6B1020]">¡Pedidos confirmados!</h1>
              <p className="mt-3 text-[#6B1020]/80">
                Gracias, {nombre.trim()}. Guardamos tus pedidos con el método de pago <strong>{metodo}</strong>.
              </p>
              <ul className="mt-6 space-y-2 text-left">
                {creadas.map(({ orden, sedeNombre }) => (
                  <li key={orden.id} className="rounded-[18px] border-2 border-[#F3E6D9] p-4 text-[#6B1020]">
                    <Link
                      href={`/pedidos/${orden.id}`}
                      className="font-black underline underline-offset-2 hover:text-[#8B1E2D]"
                    >
                      Pedido #{orden.id.slice(0, 8).toUpperCase()}
                    </Link>
                    <span className="block text-sm">
                      Sede {sedeNombre} · {COP.format(Number(orden.total))}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-sm text-[#6B1020]/70">
                Entrega en: {direccion.trim()} · Contacto: {telefono.trim()}
              </p>
              <Link
                href="/"
                className="mt-8 inline-block rounded-[52px] border-2 border-[#6B1020] bg-[#6B1020] px-8 py-3 font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#8B1E2D] active:scale-95"
              >
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
              <h1 className="text-4xl font-black leading-none tracking-tight text-[#6B1020] sm:text-5xl">
                Finalizar compra
              </h1>
              <p className="mb-8 mt-3 font-semibold text-[#6B1020]/70">
                Revisa tu pedido y completa tus datos de entrega.
              </p>

              {creadas.length > 0 && (
                <div className="mb-6 rounded-[18px] border-2 border-[#6B1020] bg-white p-4 text-sm text-[#6B1020]">
                  <p className="font-black">Estos pedidos ya quedaron registrados:</p>
                  <ul className="mt-1">
                    {creadas.map(({ orden, sedeNombre }) => (
                      <li key={orden.id}>
                        #{orden.id.slice(0, 8).toUpperCase()} · Sede {sedeNombre}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
                <form
                  onSubmit={confirmar}
                  noValidate
                  aria-label="Datos de entrega y pago"
                  className="space-y-5 rounded-[25px] border-2 border-[#6B1020] bg-white p-6 shadow-xl sm:p-8"
                >
                  <div>
                    <label htmlFor="nombre" className={ETIQUETA}>Nombre completo</label>
                    <input
                      id="nombre"
                      value={nombre}
                      onChange={(ev) => setNombre(ev.target.value)}
                      maxLength={120}
                      autoComplete="name"
                      aria-invalid={Boolean(errores.nombre)}
                      aria-describedby={errores.nombre ? "nombre-error" : undefined}
                      className={`${CAMPO} ${errores.nombre ? "border-[#B42335]" : "border-[#6B1020]"}`}
                    />
                    {errores.nombre && <p id="nombre-error" role="alert" className={ERROR}>{errores.nombre}</p>}
                  </div>

                  <div>
                    <label htmlFor="telefono" className={ETIQUETA}>Teléfono celular</label>
                    <input
                      id="telefono"
                      value={telefono}
                      onChange={(ev) => setTelefono(ev.target.value)}
                      maxLength={20}
                      inputMode="tel"
                      autoComplete="tel"
                      placeholder="310 123 4567"
                      aria-invalid={Boolean(errores.telefono)}
                      aria-describedby={errores.telefono ? "telefono-error" : undefined}
                      className={`${CAMPO} ${errores.telefono ? "border-[#B42335]" : "border-[#6B1020]"}`}
                    />
                    {errores.telefono && <p id="telefono-error" role="alert" className={ERROR}>{errores.telefono}</p>}
                  </div>

                  <div>
                    <label htmlFor="direccion" className={ETIQUETA}>Dirección de entrega</label>
                    <input
                      id="direccion"
                      value={direccion}
                      onChange={(ev) => setDireccion(ev.target.value)}
                      maxLength={200}
                      autoComplete="street-address"
                      placeholder="Calle, número, barrio"
                      aria-invalid={Boolean(errores.direccion)}
                      aria-describedby={errores.direccion ? "direccion-error" : undefined}
                      className={`${CAMPO} ${errores.direccion ? "border-[#B42335]" : "border-[#6B1020]"}`}
                    />
                    {errores.direccion && <p id="direccion-error" role="alert" className={ERROR}>{errores.direccion}</p>}
                  </div>

                  <div>
                    <label htmlFor="metodo" className={ETIQUETA}>Método de pago</label>
                    <select
                      id="metodo"
                      value={metodo}
                      disabled={authLoading || !user}
                      onChange={(ev) => setMetodo(ev.target.value as MetodoPago)}
                      className={`${CAMPO} border-[#6B1020]`}
                    >
                      {METODOS_PAGO.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    {metodo === "Bre-B" && (
                      <p className="mt-2 rounded-[18px] border-2 border-[#6B1020]/20 bg-[#F3E6D9] p-3 text-sm text-[#6B1020]">
                        El comercio debe compartirte su QR Bre-B oficial para completar el pago. Verifica que el destinatario sea La Economía Aya antes de transferir; este pedido no genera un QR ni confirma el pago automáticamente.
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="flex cursor-pointer items-start gap-3 text-sm text-[#6B1020]">
                      <input
                        type="checkbox"
                        checked={acepta}
                        onChange={(ev) => setAcepta(ev.target.checked)}
                        aria-invalid={Boolean(errores.acepta)}
                        aria-describedby={errores.acepta ? "acepta-error" : undefined}
                        className="mt-0.5 h-4 w-4 accent-[#6B1020]"
                      />
                      <span>Autorizo el tratamiento de mis datos personales para gestionar este pedido (Ley 1581 de 2012).</span>
                    </label>
                    <p className="ml-7 mt-1 text-xs">
                      <Link href="/privacidad" target="_blank" className="font-bold text-[#6B1020] underline underline-offset-2">
                        Leer la política de privacidad
                      </Link>
                    </p>
                    {errores.acepta && <p id="acepta-error" role="alert" className={ERROR}>{errores.acepta}</p>}
                  </div>

                  {errorGlobal && (
                    <p role="alert" className="rounded-[18px] border-2 border-[#B42335] bg-white p-3 text-sm font-bold text-[#B42335]">
                      {errorGlobal}
                    </p>
                  )}

                  <button
                    type="submit"
                    disabled={enviando}
                    className="h-14 w-full rounded-[52px] border-2 border-[#6B1020] bg-[#6B1020] text-lg font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#8B1E2D] active:scale-95 disabled:cursor-wait disabled:opacity-70 disabled:active:scale-100"
                  >
                    {enviando ? "Procesando…" : `Confirmar pedido · ${COP.format(totalPrecio)}`}
                  </button>
                </form>

                <aside
                  aria-label="Resumen del pedido"
                  className="h-fit rounded-[25px] border-2 border-[#6B1020] bg-white p-6 lg:sticky lg:top-6"
                >
                  <h2 className="text-2xl font-black leading-none tracking-tight text-[#6B1020]">Tu pedido</h2>
                  {grupos.map((g) => (
                    <section key={g.sedeId} className="mt-5">
                      <h3 className="text-xs font-black uppercase tracking-wide text-[#8B1E2D]">Sede {g.sedeNombre}</h3>
                      <ul className="mt-2 divide-y-2 divide-[#F3E6D9]">
                        {g.items.map((it) => (
                          <li key={`${it.sedeId}-${it.productoId}`} className="flex items-start justify-between gap-3 py-2 text-sm text-[#6B1020]">
                            <span>
                              {it.nombre} <span className="font-black">× {it.cantidad}</span>
                            </span>
                            <span className="font-bold">{COP.format(it.precio * it.cantidad)}</span>
                          </li>
                        ))}
                      </ul>
                      <p className="mt-1 text-right text-sm font-semibold text-[#6B1020]/80">
                        Subtotal: {COP.format(g.subtotal)}
                      </p>
                    </section>
                  ))}
                  <div className="mt-5 flex items-center justify-between border-t-2 border-[#6B1020] pt-4">
                    <span className="font-bold text-[#6B1020]">Total ({totalItems} uds.)</span>
                    <span className="text-2xl font-black tracking-tight text-[#6B1020]">{COP.format(totalPrecio)}</span>
                  </div>
                  {grupos.length > 1 && (
                    <p className="mt-3 text-xs font-medium text-[#6B1020]/70">
                      Tu carrito tiene productos de {grupos.length} sedes: se creará un pedido por cada sede.
                    </p>
                  )}
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
