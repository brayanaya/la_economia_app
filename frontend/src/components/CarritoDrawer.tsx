// carrito-v2
"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useCarrito, type ItemCarrito } from "@/context/CarritoContext";
import { nombreSede } from "@/lib/sedes";

const COP = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });

interface GrupoSede {
  sedeId: string;
  sedeNombre: string;
  items: ItemCarrito[];
  subtotal: number;
}

export default function CarritoDrawer() {
  const { items, hidratado, abierto, totalItems, totalPrecio, cerrar, cambiarCantidad, quitar } = useCarrito();

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

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-[65]" role="dialog" aria-modal="true" aria-label="Carrito de compras">
      <div className="anim-fade absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={cerrar} />
      <aside className="anim-drawer absolute right-0 top-0 flex h-full w-full max-w-md flex-col rounded-l-[25px] border-l-2 border-[#3f0791] bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b-2 border-[#dad9ff] px-5 py-4">
          <h2 className="text-2xl font-black leading-none tracking-tight text-[#3f0791]">
            Tu carrito{hidratado && totalItems > 0 ? ` (${totalItems})` : ""}
          </h2>
          <button
            type="button"
            onClick={cerrar}
            aria-label="Cerrar carrito"
            className="rounded-full px-3 py-1 text-2xl font-black leading-none text-[#3f0791] transition-all duration-200 hover:bg-[#dad9ff] active:scale-95"
          >
            ×
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {hidratado && items.length === 0 && (
            <p className="py-10 text-center font-semibold text-[#3f0791]/70">Tu carrito está vacío.</p>
          )}

          {grupos.map((g) => (
            <section key={g.sedeId} className="mb-6">
              <h3 className="mb-2 text-xs font-black uppercase tracking-wide text-[#5b00ed]">Sede {g.sedeNombre}</h3>
              <ul className="divide-y-2 divide-[#dad9ff]">
                {g.items.map((it) => (
                  <li key={`${it.sedeId}-${it.productoId}`} className="flex items-center gap-3 py-3">
                    {it.imagen ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img src={it.imagen} alt={it.nombre} className="h-14 w-14 rounded-[12px] border-2 border-[#dad9ff] object-cover" />
                    ) : (
                      <div className="h-14 w-14 rounded-[12px] bg-[#dad9ff]" aria-hidden="true" />
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-bold text-[#3f0791]">{it.nombre}</p>
                      <p className="text-xs text-[#3f0791]/70">{COP.format(it.precio)} c/u</p>
                      <div className="mt-1.5 flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => cambiarCantidad(it.productoId, it.sedeId, it.cantidad - 1)}
                          aria-label="Disminuir cantidad"
                          className="h-7 w-7 rounded-full border-2 border-[#3f0791] font-black text-[#3f0791] transition-all duration-200 hover:bg-[#dad9ff] active:scale-95"
                        >
                          −
                        </button>
                        <span className="w-6 text-center text-sm font-black text-[#3f0791]">{it.cantidad}</span>
                        <button
                          type="button"
                          onClick={() => cambiarCantidad(it.productoId, it.sedeId, it.cantidad + 1)}
                          aria-label="Aumentar cantidad"
                          className="h-7 w-7 rounded-full border-2 border-[#3f0791] font-black text-[#3f0791] transition-all duration-200 hover:bg-[#dad9ff] active:scale-95"
                        >
                          +
                        </button>
                        <button
                          type="button"
                          onClick={() => quitar(it.productoId, it.sedeId)}
                          className="ml-2 text-xs font-bold text-[#b3087f] hover:underline"
                        >
                          Quitar
                        </button>
                      </div>
                    </div>
                    <p className="text-sm font-black text-[#3f0791]">{COP.format(it.precio * it.cantidad)}</p>
                  </li>
                ))}
              </ul>
              <p className="mt-1 text-right text-sm font-semibold text-[#3f0791]/80">
                Subtotal sede: <span className="font-black">{COP.format(g.subtotal)}</span>
              </p>
            </section>
          ))}
        </div>

        {items.length > 0 && (
          <footer className="border-t-2 border-[#dad9ff] px-5 py-4">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm font-bold text-[#3f0791]/80">Total ({totalItems} uds.)</span>
              <span className="text-2xl font-black tracking-tight text-[#3f0791]">{COP.format(totalPrecio)}</span>
            </div>
            <Link
              href="/checkout"
              onClick={cerrar}
              className="block w-full rounded-[52px] border-2 border-[#3f0791] bg-[#3f0791] py-3 text-center text-lg font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#5b00ed] active:scale-95"
            >
              Ir a pagar
            </Link>
          </footer>
        )}
      </aside>
    </div>
  );
}
