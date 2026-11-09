"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { OrdenConsulta } from "@/lib/ordenes";
import { iniciarPagoWompi } from "@/lib/ordenes";
import { nombreSede } from "@/lib/sedes";
import { SafeProductImage } from "@/components/SafeImage";
import {
  CheckCircle2,
  Copy,
  CreditCard,
  QrCode,
  Smartphone,
  Truck,
  Printer,
  ShoppingBag,
  ExternalLink,
  Loader2,
  Sparkles,
} from "lucide-react";

const COP = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
const FECHA = new Intl.DateTimeFormat("es-CO", {
  dateStyle: "long",
  timeStyle: "short",
  timeZone: "America/Bogota",
});

function etiquetaEstado(estado: string): string {
  const texto = estado.replace(/_/g, " ");
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

export default function TicketPedido({ orden, nuevo }: { orden: OrdenConsulta; nuevo: boolean }) {
  const [copiadoId, setCopiadoId] = useState(false);
  const [copiadoLlave, setCopiadoLlave] = useState<string | null>(null);
  const [pagandoWompi, setPagandoWompi] = useState(false);
  const [errorWompi, setErrorWompi] = useState<string | null>(null);
  const temporizador = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (temporizador.current) clearTimeout(temporizador.current);
    };
  }, []);

  async function copiarTexto(texto: string, tipo: "id" | "llave", llaveNombre?: string) {
    try {
      await navigator.clipboard.writeText(texto);
      if (tipo === "id") {
        setCopiadoId(true);
        setTimeout(() => setCopiadoId(false), 2000);
      } else if (llaveNombre) {
        setCopiadoLlave(llaveNombre);
        setTimeout(() => setCopiadoLlave(null), 2000);
      }
    } catch {
      // ignore
    }
  }

  async function pagarConWompi() {
    setPagandoWompi(true);
    setErrorWompi(null);
    try {
      const { accion, campos } = await iniciarPagoWompi(orden.id);
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
      setErrorWompi(err instanceof Error ? err.message : "No pudimos iniciar el pago con Wompi");
      setPagandoWompi(false);
    }
  }

  const codigo = orden.id.slice(0, 8).toUpperCase();
  const fechaCreacion = new Date(orden.creado_en);
  const fecha = Number.isNaN(fechaCreacion.getTime()) ? "" : FECHA.format(fechaCreacion);
  const metodo = orden.metodo_pago || "contra_entrega";
  const yaPagado = orden.estado === "pagado";

  const btnSecundario =
    "inline-flex items-center justify-center gap-2 rounded-xl border-2 border-black bg-white px-4 py-2 text-sm font-black text-black transition-all shadow-[2px_2px_0_0_#3f0791] hover:-translate-y-0.5 hover:bg-gray-50 active:translate-x-0.5 active:translate-y-0.5 active:shadow-none";

  return (
    <div className="mx-auto max-w-2xl px-2 sm:px-0">
      {nuevo && (
        <div
          role="status"
          className="mb-6 rounded-3xl border-3 border-black bg-[#ffcc00] p-6 text-center shadow-[6px_6px_0_0_#3f0791] print:hidden"
        >
          <div
            aria-hidden="true"
            className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-2xl border-2 border-black bg-white text-3xl font-black text-[#3f0791] shadow-[3px_3px_0_0_#000000]"
          >
            ✓
          </div>
          <h1 className="text-3xl sm:text-4xl font-black leading-none tracking-tight text-black">
            ¡Pedido confirmado con éxito!
          </h1>
          <p className="mt-2 text-base font-bold text-black/80">
            Gracias por comprar en La Economía Aya, <span className="underline">{orden.cliente_nombre}</span>.
          </p>
        </div>
      )}

      {/* Tarjeta de Ticket Neo-Pop */}
      <article
        aria-label="Ticket del pedido"
        className="overflow-hidden rounded-3xl border-3 border-black bg-white shadow-[8px_8px_0_0_#3f0791]"
      >
        {/* Cabecera del ticket */}
        <div className="bg-gradient-to-r from-[#3f0791] via-[#5b0cb5] to-[#e30ba6] px-6 py-5 text-white border-b-3 border-black">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-widest bg-[#ffcc00] text-black px-2.5 py-0.5 rounded-full border border-black shadow-[1px_1px_0_0_#000000]">
              Ticket Oficial de Compra
            </span>
            <span
              className={`rounded-full px-3 py-1 text-xs font-black border-2 border-black shadow-[2px_2px_0_0_#000000] ${
                yaPagado
                  ? "bg-emerald-300 text-emerald-950"
                  : "bg-amber-300 text-amber-950"
              }`}
            >
              {yaPagado ? "✓ PAGADO" : etiquetaEstado(orden.estado).toUpperCase()}
            </span>
          </div>

          <div className="mt-3 flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="text-3xl font-black tracking-tight text-white">Pedido #{codigo}</h2>
            <span className="text-xs font-mono font-bold text-white/80">{fecha}</span>
          </div>
        </div>

        {/* Metadatos del cliente y entrega */}
        <dl className="grid gap-3 p-6 text-sm sm:grid-cols-2 bg-[#faf7ff] border-b-2 border-black/10">
          <div className="rounded-xl border border-black/10 bg-white p-3 shadow-sm">
            <dt className="text-xs font-black uppercase tracking-wider text-[#3f0791]">Cliente</dt>
            <dd className="mt-0.5 font-bold text-black">{orden.cliente_nombre}</dd>
          </div>
          <div className="rounded-xl border border-black/10 bg-white p-3 shadow-sm">
            <dt className="text-xs font-black uppercase tracking-wider text-[#3f0791]">Sede despachadora</dt>
            <dd className="mt-0.5 font-bold text-black">{nombreSede(orden.sede_id)}</dd>
          </div>
          <div className="rounded-xl border border-black/10 bg-white p-3 shadow-sm">
            <dt className="text-xs font-black uppercase tracking-wider text-[#3f0791]">Método de pago</dt>
            <dd className="mt-0.5 font-bold text-black capitalize">
              {metodo === "wompi" ? "💳 Wompi (En línea)" : metodo === "bre_b" ? "⚡ Bre-B (Interbancario)" : "🚚 Contra Entrega"}
            </dd>
          </div>
        </dl>

        {/* UUID completo para rastreo */}
        <div className="border-b-2 border-dashed border-black/20 p-5 bg-white">
          <p className="text-xs font-black uppercase tracking-wider text-[#3f0791]">ID completo del pedido</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <code className="break-all rounded-xl border border-black/20 bg-[#faf7ff] px-3 py-2 text-xs font-mono font-bold text-black shadow-inner">
              {orden.id}
            </code>
            <button
              type="button"
              onClick={() => copiarTexto(orden.id, "id")}
              className={`${btnSecundario} text-xs py-1.5 print:hidden`}
            >
              <Copy size={14} />
              <span>{copiadoId ? "¡Copiado! ✓" : "Copiar ID"}</span>
            </button>
          </div>
        </div>

        {/* ============================================================ */}
        {/* SECCIÓN FLEXIBLE DE PAGO (BRE-B / WOMPI / CONTRA ENTREGA)   */}
        {/* ============================================================ */}
        <div className="p-6 border-b-2 border-black/10">
          {metodo === "bre_b" && (
            <div className="rounded-2xl border-3 border-black bg-gradient-to-br from-[#faf7ff] to-[#fff0fa] p-5 shadow-[4px_4px_0_0_#3f0791]">
              <div className="flex items-center justify-between border-b-2 border-black/10 pb-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border-2 border-black bg-[#ffcc00] shadow-[2px_2px_0_0_#000000]">
                    <QrCode className="h-5 w-5 text-black" />
                  </div>
                  <div>
                    <h3 className="font-black text-black text-base flex items-center gap-2">
                      Pago Inmediato con Bre-B
                      <span className="text-[10px] font-black uppercase bg-[#3f0791] text-white px-2 py-0.5 rounded-full">
                        Banco de la República
                      </span>
                    </h3>
                    <p className="text-xs text-gray-600 font-medium">Interoperabilidad 100% entre todos los bancos</p>
                  </div>
                </div>
              </div>

              <div className="mt-4 space-y-3">
                <p className="text-xs font-bold text-gray-700">
                  Usa cualquiera de las llaves registradas de <strong>La Economía Aya</strong> en tu app bancaria (Bancolombia, Nequi, Daviplata, Scotiabank, BBVA, Dale!, etc.):
                </p>

                {/* Llave 1: Celular */}
                <div className="flex items-center justify-between rounded-xl border-2 border-black bg-white p-3 shadow-[2px_2px_0_0_#000000]">
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-wider text-gray-500">Llave Celular Bre-B</span>
                    <p className="font-mono text-base font-black text-black">310 123 4567</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => copiarTexto("3101234567", "llave", "celular")}
                    className="rounded-lg border-2 border-black bg-[#ffcc00] px-3 py-1.5 text-xs font-black text-black transition-all hover:bg-amber-300 shadow-[1px_1px_0_0_#000000]"
                  >
                    {copiadoLlave === "celular" ? "¡Copiado! ✓" : "Copiar"}
                  </button>
                </div>

                {/* Llave 2: Alfanumérica / Comercio */}
                <div className="flex items-center justify-between rounded-xl border-2 border-black bg-white p-3 shadow-[2px_2px_0_0_#000000]">
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-wider text-gray-500">Llave Comercio Bre-B</span>
                    <p className="font-mono text-base font-black text-[#3f0791]">ECONOMIA-AYA-NEIVA</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => copiarTexto("ECONOMIA-AYA-NEIVA", "llave", "comercio")}
                    className="rounded-lg border-2 border-black bg-[#ffcc00] px-3 py-1.5 text-xs font-black text-black transition-all hover:bg-amber-300 shadow-[1px_1px_0_0_#000000]"
                  >
                    {copiadoLlave === "comercio" ? "¡Copiado! ✓" : "Copiar"}
                  </button>
                </div>

                {/* Monto exacto */}
                <div className="rounded-xl border border-black/10 bg-white/80 p-3 text-xs">
                  <span className="font-bold text-gray-600">Monto exacto a transferir: </span>
                  <span className="font-black text-lg text-[#3f0791]">{COP.format(Number(orden.total))}</span>
                </div>
              </div>
            </div>
          )}

          {metodo === "wompi" && (
            <div className="rounded-2xl border-3 border-black bg-white p-5 shadow-[4px_4px_0_0_#3f0791]">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border-2 border-black bg-[#3f0791] text-white shadow-[2px_2px_0_0_#000000]">
                  <CreditCard className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <h3 className="font-black text-black text-base flex items-center gap-2">
                    Pasarela Wompi Colombia
                    {yaPagado ? (
                      <span className="text-xs font-black bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded border border-black">
                        PAGO APROBADO ✓
                      </span>
                    ) : (
                      <span className="text-xs font-black bg-amber-100 text-amber-800 px-2 py-0.5 rounded border border-black">
                        PENDIENTE
                      </span>
                    )}
                  </h3>
                  <p className="text-xs text-gray-600 font-medium">Tarjeta de crédito/débito, PSE, Nequi y Bancolombia</p>
                </div>
              </div>

              {!yaPagado && (
                <div className="mt-4 pt-3 border-t border-black/10 space-y-3">
                  <p className="text-xs text-gray-700 font-medium">
                    Tu pedido está guardado. Completa el pago en línea para iniciar inmediatamente el alistamiento.
                  </p>
                  {errorWompi && (
                    <p className="text-xs font-bold text-red-600 bg-red-50 p-2 rounded-lg border border-red-200">
                      {errorWompi}
                    </p>
                  )}
                  <button
                    type="button"
                    onClick={pagarConWompi}
                    disabled={pagandoWompi}
                    className="w-full rounded-xl border-2 border-black bg-[#3f0791] px-4 py-3 font-black text-white text-sm transition-all shadow-[3px_3px_0_0_#e30ba6] hover:bg-[#320575] disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {pagandoWompi ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" /> Conectando con Wompi...
                      </>
                    ) : (
                      <>
                        <span>Pagar ahora {COP.format(Number(orden.total))}</span>
                        <ExternalLink size={16} />
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          )}

          {metodo === "contra_entrega" && (
            <div className="rounded-2xl border-3 border-black bg-white p-5 shadow-[4px_4px_0_0_#3f0791]">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl border-2 border-black bg-[#ffcc00] shadow-[2px_2px_0_0_#000000]">
                  <Truck className="h-6 w-6 text-black" />
                </div>
                <div>
                  <h3 className="font-black text-black text-base">Pago Contra Entrega en Neiva</h3>
                  <p className="text-xs text-gray-600 font-medium">Pagas cuando el domiciliario llegue a tu dirección</p>
                </div>
              </div>
              <p className="mt-3 text-xs text-gray-700 font-medium bg-[#faf7ff] p-3 rounded-xl border border-black/10">
                Aceptamos efectivo con cambio exacto, código QR Nequi y Daviplata en el momento de la entrega.
              </p>
            </div>
          )}
        </div>

        {/* Lista de productos comprados */}
        <div className="p-6">
          <h3 className="text-xs font-black uppercase tracking-wider text-[#3f0791] mb-3">
            Productos ({orden.items.length})
          </h3>
          <ul className="divide-y-2 divide-black/10">
            {orden.items.map((it, i) => (
              <li key={`${it.nombre}-${i}`} className="flex items-center gap-3 py-3">
                <SafeProductImage
                  src={it.imagen_url}
                  alt={it.nombre}
                  width={52}
                  height={52}
                  className="rounded-xl border-2 border-black object-cover shadow-[2px_2px_0_0_#000000]"
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-black text-black">{it.nombre}</p>
                  <p className="text-xs font-bold text-gray-600">
                    {it.cantidad} × {COP.format(Number(it.precio_unitario))}
                  </p>
                </div>
                <p className="text-sm font-black text-[#3f0791]">{COP.format(Number(it.subtotal))}</p>
              </li>
            ))}
          </ul>

          <div className="mt-4 flex items-center justify-between border-t-3 border-black pt-4">
            <div>
              <span className="text-xs font-black uppercase tracking-wider text-gray-500">Total a pagar</span>
              <p className="text-xs text-gray-500 font-medium">Impuestos incluidos</p>
            </div>
            <span className="text-3xl font-black tracking-tight text-[#3f0791]">
              {COP.format(Number(orden.total))}
            </span>
          </div>
        </div>
      </article>

      {/* Botones de acción inferiores */}
      <div className="mt-6 flex flex-wrap justify-center gap-3 print:hidden">
        <button type="button" onClick={() => window.print()} className={btnSecundario}>
          <Printer size={16} />
          <span>Imprimir ticket</span>
        </button>
        <Link href="/pedidos" className={btnSecundario}>
          <span>Consultar otro pedido</span>
        </Link>
        <Link
          href="/"
          className="inline-flex items-center justify-center gap-2 rounded-xl border-2 border-black bg-[#3f0791] px-5 py-2 text-sm font-black text-white transition-all shadow-[3px_3px_0_0_#e30ba6] hover:-translate-y-0.5 hover:bg-[#320575] active:translate-x-0.5 active:translate-y-0.5 active:shadow-none"
        >
          <ShoppingBag size={16} />
          <span>Seguir comprando</span>
        </Link>
      </div>
    </div>
  );
}
