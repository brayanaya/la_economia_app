"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { OrdenConsulta } from "@/lib/ordenes";
import { nombreSede } from "@/lib/sedes";
import BotonPagarPedido from "@/components/BotonPagarPedido";

const COP = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
const FECHA = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "long",
  timeStyle: "short",
  timeZone: "America/Bogota",
});

const BOTON_SECUNDARIO =
  "rounded-[52px] border-2 border-[#3f0791] px-5 py-2 text-sm font-black text-[#3f0791] transition-all duration-200 hover:-translate-y-0.5 hover:bg-white active:scale-95";

function etiquetaEstado(estado: string): string {
  const texto = estado.replace(/_/g, " ");
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

export default function TicketPedido({ orden, nuevo }: { orden: OrdenConsulta; nuevo: boolean }) {
  const [copiado, setCopiado] = useState(false);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (temporizador.current) clearTimeout(temporizador.current);
    };
  }, []);

  async function copiar() {
    try {
      await navigator.clipboard.writeText(orden.id);
    } catch {
      return;
    }
    setCopiado(true);
    if (temporizador.current) clearTimeout(temporizador.current);
    temporizador.current = setTimeout(() => setCopiado(false), 1800);
  }

  const codigo = orden.id.slice(0, 8).toUpperCase();
  const Titulo = nuevo ? "h2" : "h1";
  const fechaCreacion = new Date(orden.creado_en);
  const fecha = Number.isNaN(fechaCreacion.getTime()) ? "" : FECHA.format(fechaCreacion);

  return (
    <div className="mx-auto max-w-2xl">
      {nuevo && (
        <div
          role="status"
          className="anim-aparecer mb-6 rounded-[25px] border-2 border-[#3f0791] bg-white p-6 text-center shadow-xl print:hidden"
        >
          <div
            aria-hidden="true"
            className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full border-2 border-[#3f0791] bg-[#dad9ff] text-3xl font-black text-[#3f0791]"
          >
            ✓
          </div>
          <h1 className="text-4xl font-black leading-none tracking-tight text-[#3f0791]">¡Pedido confirmado!</h1>
          <p className="mt-2 text-[#3f0791]/80">Gracias, {orden.cliente_nombre}. Este es tu ticket.</p>
        </div>
      )}

      <article
        aria-label="Ticket del pedido"
        className="overflow-hidden rounded-[25px] border-2 border-[#3f0791] bg-white shadow-xl"
      >
        <div className="bg-[#3f0791] px-6 py-5 text-white">
          <p className="text-xs font-black uppercase tracking-widest text-white/80">Ticket de pedido</p>
          <div className="mt-1 flex flex-wrap items-center justify-between gap-3">
            <Titulo className="text-4xl font-black leading-none tracking-tight">Pedido #{codigo}</Titulo>
            <span className="rounded-[52px] bg-[#dad9ff] px-4 py-1 text-sm font-black text-[#3f0791]">
              {etiquetaEstado(orden.estado)}
            </span>
          </div>
        </div>

        <dl className="grid gap-4 px-6 py-5 text-sm text-[#3f0791] sm:grid-cols-2">
          <div>
            <dt className="font-black">Cliente</dt>
            <dd>{orden.cliente_nombre}</dd>
          </div>
          <div>
            <dt className="font-black">Sede</dt>
            <dd>{nombreSede(orden.sede_id)}</dd>
          </div>
          {fecha && (
            <div>
              <dt className="font-black">Fecha</dt>
              <dd>{fecha}</dd>
            </div>
          )}
        </dl>

        <div className="border-t-2 border-dashed border-[#dad9ff] px-6 py-5">
          <p className="text-xs font-black uppercase tracking-wide text-[#3f0791]/70">Número de pedido completo</p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <code className="break-all rounded-[12px] bg-[#dad9ff]/60 px-3 py-2 text-sm font-bold text-[#3f0791]">
              {orden.id}
            </code>
            <button type="button" onClick={copiar} className={`${BOTON_SECUNDARIO} print:hidden`}>
              {copiado ? "¡Copiado! ✓" : "Copiar número"}
            </button>
          </div>
          <p className="mt-2 text-xs text-[#3f0791]/70">
            Guárdalo: lo necesitas para consultar el estado de tu pedido más adelante.
          </p>
        </div>

        <div className="border-t-2 border-dashed border-[#dad9ff] px-6 py-5">
          <ul className="divide-y-2 divide-[#dad9ff]">
            {orden.items.map((it, i) => (
              <li key={`${it.nombre}-${i}`} className="flex items-center gap-3 py-3">
                {it.imagen_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={it.imagen_url}
                    alt=""
                    className="h-12 w-12 rounded-[12px] border-2 border-[#dad9ff] object-cover"
                  />
                ) : (
                  <div className="h-12 w-12 rounded-[12px] bg-[#dad9ff]" aria-hidden="true" />
                )}
                <div className="min-w-0 flex-1 text-[#3f0791]">
                  <p className="truncate text-sm font-bold">{it.nombre}</p>
                  <p className="text-xs text-[#3f0791]/70">
                    {it.cantidad} × {COP.format(Number(it.precio_unitario))}
                  </p>
                </div>
                <p className="text-sm font-black text-[#3f0791]">{COP.format(Number(it.subtotal))}</p>
              </li>
            ))}
          </ul>
          <div className="mt-4 flex items-center justify-between border-t-2 border-[#3f0791] pt-4">
            <span className="font-bold text-[#3f0791]">Total</span>
            <span className="text-3xl font-black tracking-tight text-[#3f0791]">{COP.format(Number(orden.total))}</span>
          </div>
        </div>
      </article>

      <div className="mt-6 flex flex-wrap justify-center gap-3 print:hidden">
        <BotonPagarPedido ordenId={orden.id} estado={orden.estado} />
        <button type="button" onClick={() => window.print()} className={BOTON_SECUNDARIO}>
          Imprimir ticket
        </button>
        <Link href="/pedidos" className={BOTON_SECUNDARIO}>
          Consultar otro pedido
        </Link>
        <Link
          href="/"
          className="rounded-[52px] border-2 border-[#3f0791] bg-[#3f0791] px-5 py-2 text-sm font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#5b00ed] active:scale-95"
        >
          Seguir comprando
        </Link>
      </div>
    </div>
  );
}

