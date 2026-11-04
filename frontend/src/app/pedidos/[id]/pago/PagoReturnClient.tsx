"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle, XCircle, AlertCircle, Loader2, CreditCard, Truck, QrCode } from "lucide-react";
import { consultarEstadoPago, type InicioPagoWompi } from "@/lib/ordenes";
import { COP } from "@/lib/formato";
import { consultarOrden, type OrdenConsulta, PedidoNoEncontradoError } from "@/lib/ordenes";

type EstadoPago = "verificando" | "aprobado" | "pendiente" | "declinado" | "error" | "no_encontrado";

interface PagoReturnClientProps {
  ordenId: string;
  initialSearchParams: {
    transaction_id?: string | null;
    reference?: string | null;
    status?: string | null;
  };
}

export function PagoReturnClient({ ordenId, initialSearchParams }: PagoReturnClientProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [estado, setEstado] = useState<EstadoPago>("verificando");
  const [orden, setOrden] = useState<OrdenConsulta | null>(null);
  const [pagoInfo, setPagoInfo] = useState<{
    estado: string;
    referencia: string;
    monto: number;
    transaccion_id?: string | null;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reintentos, setReintentos] = useState(0);
  const maxReintentos = 10;

  useEffect(() => {
    if (!ordenId) {
      setEstado("no_encontrado");
      setError("ID de pedido inválido");
      return;
    }

    const transactionId = initialSearchParams.transaction_id ?? searchParams.get("transaction_id");
    const reference = initialSearchParams.reference ?? searchParams.get("reference");
    const status = initialSearchParams.status ?? searchParams.get("status");

    const verificarEstado = async () => {
      try {
        const [ordenData, pagoData] = await Promise.all([
          consultarOrden(ordenId),
          consultarEstadoPago(ordenId),
        ]);
        setOrden(ordenData);
        if (pagoData.pago) {
          setPagoInfo({
            estado: pagoData.pago.estado,
            referencia: pagoData.pago.referencia,
            monto: pagoData.pago.monto_centavos / 100,
            transaccion_id: pagoData.pago.transaccion_id,
          });
        }

        // Determine overall state
        if (pagoData.pago) {
          switch (pagoData.pago.estado) {
            case "aprobado":
              setEstado("aprobado");
              break;
            case "pendiente":
              setEstado("pendiente");
              break;
            case "declinado":
              setEstado("declinado");
              break;
            case "anulado":
              setEstado("declinado");
              break;
            case "error":
              setEstado("error");
              break;
            default:
              setEstado("pendiente");
          }
        } else if (ordenData.estado === "pagado") {
          setEstado("aprobado");
        } else {
          setEstado("pendiente");
        }
      } catch (err) {
        if (err instanceof PedidoNoEncontradoError) {
          setEstado("no_encontrado");
          setError("Pedido no encontrado");
        } else {
          setError("Error al consultar el estado del pago");
        }
      }
    };

    // Initial check
    verificarEstado();

    // If payment is pending, poll for updates
    if (estado === "pendiente" || estado === "verificando") {
      const interval = setInterval(async () => {
        if (reintentos >= maxReintentos) {
          clearInterval(interval);
          return;
        }
        setReintentos(r => r + 1);
        await verificarEstado();
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [ordenId, searchParams, reintentos, initialSearchParams]);

  // Re-run verification when reintentos changes
  useEffect(() => {
    if (reintentos > 0) {
      const verificarEstado = async () => {
        try {
          const [ordenData, pagoData] = await Promise.all([
            consultarOrden(ordenId),
            consultarEstadoPago(ordenId),
          ]);
          setOrden(ordenData);
          if (pagoData.pago) {
            setPagoInfo({
              estado: pagoData.pago.estado,
              referencia: pagoData.pago.referencia,
              monto: pagoData.pago.monto_centavos / 100,
              transaccion_id: pagoData.pago.transaccion_id,
            });
          }

          if (pagoData.pago) {
            switch (pagoData.pago.estado) {
              case "aprobado":
                setEstado("aprobado");
                break;
              case "pendiente":
                setEstado("pendiente");
                break;
              case "declinado":
              case "anulado":
                setEstado("declinado");
                break;
              case "error":
                setEstado("error");
                break;
            }
          } else if (ordenData.estado === "pagado") {
            setEstado("aprobado");
          }
        } catch {
          // Ignore errors during polling
        }
      };
      verificarEstado();
    }
  }, [reintentos, ordenId]);

  const iconos = {
    aprobado: <CheckCircle className="w-16 h-16 text-green-600" />,
    pendiente: <Loader2 className="w-16 h-16 text-yellow-600 animate-spin" />,
    declinado: <XCircle className="w-16 h-16 text-red-600" />,
    error: <AlertCircle className="w-16 h-16 text-red-600" />,
    no_encontrado: <AlertCircle className="w-16 h-16 text-gray-600" />,
    verificando: <Loader2 className="w-16 h-16 text-blue-600 animate-spin" />,
  };

  const textos = {
    aprobado: { titulo: "¡Pago aprobado!", subtitulo: "Tu pedido ha sido confirmado y está siendo preparado." },
    pendiente: { titulo: "Pago pendiente", subtitulo: "Estamos verificando el estado de tu pago. Esto puede tomar unos segundos..." },
    declinado: { titulo: "Pago no aprobado", subtitulo: "La transacción no pudo completarse. Puedes intentarlo de nuevo con otro método." },
    error: { titulo: "Error en el pago", subtitulo: "Ocurrió un problema al procesar el pago. Por favor, inténtalo de nuevo." },
    no_encontrado: { titulo: "Pedido no encontrado", subtitulo: "No pudimos localizar este pedido. Verifica el ID e inténtalo de nuevo." },
    verificando: { titulo: "Verificando pago…", subtitulo: "Consultando el estado de tu transacción con Wompi." },
  };

  const metodoIcono = (metodo?: string | null) => {
    switch (metodo) {
      case "wompi": return <CreditCard className="w-5 h-5" />;
      case "contra_entrega": return <Truck className="w-5 h-5" />;
      case "bre_b": return <QrCode className="w-5 h-5" />;
      default: return <CreditCard className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
          <div className={`px-6 py-8 text-center ${estado === "aprobado" ? "bg-green-50" : estado === "declinado" || estado === "error" ? "bg-red-50" : "bg-blue-50"}`}>
            {iconos[estado]}
            <h1 className="mt-4 text-2xl font-black text-gray-900">{textos[estado].titulo}</h1>
            <p className="mt-2 text-gray-600">{textos[estado].subtitulo}</p>
          </div>

          {orden && (
            <div className="p-6 border-t border-gray-100">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm font-medium text-gray-500">Pedido</span>
                <span className="font-mono font-bold text-gray-900">#{orden.id.slice(0, 8).toUpperCase()}</span>
              </div>

              {pagoInfo && (
                <div className="mb-4 p-4 rounded-xl bg-gray-50 border border-gray-100">
                  <div className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                    {metodoIcono(orden.metodo_pago ?? null)} <span>Método: {orden.metodo_pago?.replace("_", " ").toUpperCase()}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><span className="text-gray-500">Referencia</span><br /><span className="font-mono font-bold">{pagoInfo.referencia}</span></div>
                    <div><span className="text-gray-500">Monto</span><br /><span className="font-bold text-gray-900">{COP.format(pagoInfo.monto)}</span></div>
                    {pagoInfo.transaccion_id && (
                      <div className="col-span-2"><span className="text-gray-500">Transacción</span><br /><span className="font-mono text-xs">{pagoInfo.transaccion_id}</span></div>
                    )}
                    <div className="col-span-2"><span className="text-gray-500">Estado</span><br /><span className={`font-bold capitalize ${pagoInfo.estado === "aprobado" ? "text-green-600" : pagoInfo.estado === "pendiente" ? "text-yellow-600" : "text-red-600"}`}>{pagoInfo.estado}</span></div>
                  </div>
                </div>
              )}

              <div className="mb-4 p-4 rounded-xl bg-gray-50 border border-gray-100">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-500">Total</span>
                  <span className="font-black text-xl text-gray-900">{COP.format(Number(orden.total))}</span>
                </div>
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>Estado del pedido</span>
                  <span className={`font-bold capitalize ${orden.estado === "pagado" ? "text-green-600" : orden.estado === "pendiente" ? "text-yellow-600" : "text-gray-600"}`}>{orden.estado}</span>
                </div>
              </div>

              <div className="space-y-3">
                {estado === "aprobado" && (
                  <Link href={`/pedidos/${orden.id}`} className="block w-full rounded-xl bg-[#6B1020] px-6 py-3.5 font-black text-white text-center hover:bg-[#8B1E2D] transition-colors">
                    Ver mi pedido
                  </Link>
                )}
                {estado === "declinado" && (
                  <Link href="/checkout" className="block w-full rounded-xl bg-[#6B1020] px-6 py-3.5 font-black text-white text-center hover:bg-[#8B1E2D] transition-colors">
                    Volver al checkout
                  </Link>
                )}
                {(estado === "pendiente" || estado === "verificando") && (
                  <button className="block w-full rounded-xl border-2 border-gray-200 px-6 py-3.5 font-bold text-gray-700 text-center" disabled>
                    Verificando automáticamente…
                  </button>
                )}
                <Link href="/" className="block w-full rounded-xl border-2 border-[#6B1020] bg-white px-6 py-3.5 font-bold text-[#6B1020] text-center hover:bg-[#F3E6D9] transition-colors mt-2">
                  Seguir comprando
                </Link>
              </div>
            </div>
          )}

          {error && !orden && (
            <div className="p-6 text-center text-red-600">
              <AlertCircle className="w-12 h-12 mx-auto mb-3" />
              <h2 className="text-xl font-black">No se encontró el pedido</h2>
              <p className="mt-2 text-gray-600">{error}</p>
              <Link href="/" className="mt-4 inline-block rounded-xl border-2 border-[#6B1020] bg-[#6B1020] px-6 py-3 font-black text-white hover:bg-[#8B1E2D] transition-colors">
                Volver al inicio
              </Link>
            </div>
          )}
        </div>

        {estado === "verificando" || estado === "pendiente" ? (
          <p className="mt-4 text-center text-sm text-gray-500">Esta página se actualiza automáticamente cada 3 segundos.</p>
        ) : null}
      </div>
    </div>
  );
}