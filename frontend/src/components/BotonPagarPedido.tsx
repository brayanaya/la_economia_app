"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

type PagoRespuesta = {
  orden_id: string;
  estado: string;
  ticket_id: string;
  total: string;
};

const RAW = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API = RAW.replace(/\/+$/, "").replace(/\/api\/v1$/, "") + "/api/v1";

export default function BotonPagarPedido({
  ordenId,
  estado,
}: {
  ordenId: string;
  estado: string;
}) {
  const router = useRouter();
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (estado.toLowerCase() !== "pendiente") return null;

  async function pagar() {
    if (procesando) return;

    setProcesando(true);
    setError(null);

    try {
      const respuesta = await fetch(`${API}/pagos/procesar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orden_id: ordenId }),
      });

      const datos = (await respuesta.json()) as PagoRespuesta | { detail?: string };

      if (!respuesta.ok) {
        const mensaje =
          "detail" in datos && typeof datos.detail === "string"
            ? datos.detail
            : "No se pudo procesar el pago.";
        throw new Error(mensaje);
      }

      const pago = datos as PagoRespuesta;
      const query = new URLSearchParams({ ticket_id: pago.ticket_id });
      router.push(
        `/checkout/success/${encodeURIComponent(pago.orden_id)}?${query.toString()}`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo procesar el pago.");
      setProcesando(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={pagar}
        disabled={procesando}
        className="rounded-[52px] border-2 border-black bg-[#FFD700] px-5 py-2 text-sm font-black text-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-transform hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] disabled:cursor-wait disabled:opacity-70"
      >
        {procesando ? "PROCESANDO…" : "SIMULAR PAGO"}
      </button>
      {error && (
        <p role="alert" className="max-w-xs text-center text-sm font-bold text-[#b3087f]">
          {error}
        </p>
      )}
    </div>
  );
}
