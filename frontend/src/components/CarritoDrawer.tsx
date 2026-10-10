// carrito-v1
"use client";

import { useMemo, useState } from "react";
import { useCarrito, type ItemCarrito } from "@/context/CarritoContext";
import { crearOrden, type OrdenCreada } from "@/lib/ordenes";
import { mostrarAviso } from "@/lib/aviso";

const COP = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

const NOMBRES_SEDE: Record<string, string> = {
  "a0000000-0000-0000-0000-000000000001": "Santa Isabel",
  "a0000000-0000-0000-0000-000000000002": "Machines",
};

interface GrupoSede {
  sedeId: string;
  sedeNombre: string;
  items: ItemCarrito[];
  subtotal: number;
}

export default function CarritoDrawer() {
  const { items, hidratado, abierto, totalItems, totalPrecio, abrir, cerrar, cambiarCantidad, quitar, vaciarSede } =
    useCarrito();
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [notas, setNotas] = useState("");
  const [acepta, setAcepta] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [creadas, setCreadas] = useState<OrdenCreada[]>([]);

  const grupos = useMemo<GrupoSede[]>(() => {
    const mapa = new Map<string, GrupoSede>();
    for (const it of items) {
      const g: GrupoSede = mapa.get(it.sedeId) ?? {
        sedeId: it.sedeId,
        sedeNombre: it.sedeNombre ?? NOMBRES_SEDE[it.sedeId] ?? "Sede",
        items: [],
        subtotal: 0,
      };
      g.items.push(it);
      g.subtotal += it.precio * it.cantidad;
      mapa.set(it.sedeId, g);
    }
    return Array.from(mapa.values());
  }, [items]);

  const finalizar = async () => {
    setError(null);
    if (nombre.trim().length < 2) return setError("Ingresa tu nombre para el pedido.");
    if (!acepta) return setError("Debes aceptar el tratamiento de datos personales (Ley 1581 de 2012).");

    setEnviando(true);
    const ok: OrdenCreada[] = [];
    const fallos: string[] = [];
    for (const g of grupos) {
      try {
        const orden = await crearOrden({
          sede_id: g.sedeId,
          cliente_nombre: nombre.trim(),
          cliente_telefono: telefono.trim() || null,
          notas: notas.trim() || null,
          items: g.items.map((i) => ({
            producto_id: i.productoId,
            nombre: i.nombre,
            cantidad: i.cantidad,
            precio_unitario: i.precio,
            imagen_url: i.imagen ?? null,
          })),
        });
        ok.push(orden);
        vaciarSede(g.sedeId);
      } catch (e) {
        fallos.push(`${g.sedeNombre}: ${e instanceof Error ? e.message : "error desconocido"}`);
      }
    }
    setEnviando(false);
    if (ok.length > 0) setCreadas(ok);
    if (fallos.length > 0) {
      setError(fallos.join(" | "));
      mostrarAviso("Error al procesar la orden. Inténtalo de nuevo.");
    }
  };

  const cerrarTodo = () => {
    setCreadas([]);
    setError(null);
    cerrar();
  };

  return (
    <>
      <button
        type="button"
        onClick={abrir}
        aria-label="Abrir carrito de compras"
        className="fixed bottom-4 left-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-green-600 text-white shadow-lg hover:bg-green-700"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-6 w-6" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l3-8H5.4M7 13L5.4 5M7 13l-2 4h13M9 21a1 1 0 100-2 1 1 0 000 2zm9 0a1 1 0 100-2 1 1 0 000 2z" />
        </svg>
        {hidratado && totalItems > 0 && (
          <span className="absolute -right-1 -top-1 min-w-[1.4rem] rounded-full bg-red-600 px-1 text-center text-xs font-bold leading-6">
            {totalItems}
          </span>
        )}
      </button>

      {abierto && (
        <div className="fixed inset-0 z-[65]" role="dialog" aria-modal="true" aria-label="Carrito de compras">
          <div className="absolute inset-0 bg-black/50" onClick={cerrarTodo} />
          <aside className="absolute right-0 top-0 flex h-full w-full max-w-md flex-col bg-white shadow-xl">
            <header className="flex items-center justify-between border-b px-4 py-3">
              <h2 className="text-lg font-bold text-gray-900">Tu carrito</h2>
              <button type="button" onClick={cerrarTodo} aria-label="Cerrar carrito" className="rounded p-1 text-2xl leading-none text-gray-600 hover:bg-gray-100">
                ×
              </button>
            </header>

            <div className="flex-1 overflow-y-auto px-4 py-3">
              {creadas.length > 0 && (
                <div className="mb-4 rounded-lg border border-green-300 bg-green-50 p-3 text-sm text-green-900">
                  <p className="font-semibold">¡Pedido registrado!</p>
                  <ul className="mt-1 space-y-1">
                    {creadas.map((o) => (
                      <li key={o.id}>
                        #{o.id.slice(0, 8).toUpperCase()} · {NOMBRES_SEDE[o.sede_id] ?? "Sede"} · {COP.format(Number(o.total))}
                      </li>
                    ))}
                  </ul>
                  <button type="button" onClick={() => setCreadas([])} className="mt-2 text-green-800 underline">
                    Seguir comprando
                  </button>
                </div>
              )}

              {hidratado && items.length === 0 && creadas.length === 0 && (
                <p className="py-10 text-center text-gray-500">Tu carrito está vacío.</p>
              )}

              {grupos.map((g) => (
                <section key={g.sedeId} className="mb-5">
                  <h3 className="mb-2 text-sm font-bold uppercase tracking-wide text-green-700">Sede {g.sedeNombre}</h3>
                  <ul className="divide-y">
                    {g.items.map((it) => (
                      <li key={`${it.sedeId}-${it.productoId}`} className="flex items-center gap-3 py-2">
                        {it.imagen ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img src={it.imagen} alt={it.nombre} className="h-12 w-12 rounded object-cover" />
                        ) : (
                          <div className="h-12 w-12 rounded bg-gray-100" aria-hidden="true" />
                        )}
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-gray-900">{it.nombre}</p>
                          <p className="text-xs text-gray-500">{COP.format(it.precio)} c/u</p>
                          <div className="mt-1 flex items-center gap-2">
                            <button type="button" onClick={() => cambiarCantidad(it.productoId, it.sedeId, it.cantidad - 1)} aria-label="Disminuir cantidad" className="h-6 w-6 rounded border text-sm hover:bg-gray-100">−</button>
                            <span className="w-6 text-center text-sm">{it.cantidad}</span>
                            <button type="button" onClick={() => cambiarCantidad(it.productoId, it.sedeId, it.cantidad + 1)} aria-label="Aumentar cantidad" className="h-6 w-6 rounded border text-sm hover:bg-gray-100">+</button>
                            <button type="button" onClick={() => quitar(it.productoId, it.sedeId)} className="ml-2 text-xs text-red-600 hover:underline">Quitar</button>
                          </div>
                        </div>
                        <p className="text-sm font-semibold text-gray-900">{COP.format(it.precio * it.cantidad)}</p>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-1 text-right text-sm text-gray-600">Subtotal sede: <span className="font-semibold">{COP.format(g.subtotal)}</span></p>
                </section>
              ))}

              {items.length > 0 && (
                <div className="space-y-2 border-t pt-3">
                  <input value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={120} placeholder="Tu nombre *" className="w-full rounded border px-3 py-2 text-sm" />
                  <input value={telefono} onChange={(e) => setTelefono(e.target.value)} maxLength={30} inputMode="tel" placeholder="Teléfono (opcional)" className="w-full rounded border px-3 py-2 text-sm" />
                  <textarea value={notas} onChange={(e) => setNotas(e.target.value)} maxLength={500} rows={2} placeholder="Notas del pedido (opcional)" className="w-full rounded border px-3 py-2 text-sm" />
                  <label className="flex items-start gap-2 text-xs text-gray-600">
                    <input type="checkbox" checked={acepta} onChange={(e) => setAcepta(e.target.checked)} className="mt-0.5" />
                    <span>Autorizo el tratamiento de mis datos personales para gestionar este pedido (Ley 1581 de 2012).</span>
                  </label>
                </div>
              )}

              {error && <p role="alert" className="mt-3 rounded bg-red-50 p-2 text-sm text-red-700">{error}</p>}
            </div>

            {items.length > 0 && (
              <footer className="border-t px-4 py-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total ({totalItems} uds.)</span>
                  <span className="text-xl font-bold text-gray-900">{COP.format(totalPrecio)}</span>
                </div>
                <button type="button" onClick={finalizar} disabled={enviando} className="w-full rounded-lg bg-green-600 py-3 font-semibold text-white hover:bg-green-700 disabled:opacity-60">
                  {enviando ? "Procesando…" : grupos.length > 1 ? `Finalizar compra (${grupos.length} pedidos)` : "Finalizar compra"}
                </button>
              </footer>
            )}
          </aside>
        </div>
      )}
    </>
  );
}
