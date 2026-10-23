"use client";

import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import EstadoVacio from "@/components/EstadoVacio";
import ShellPagina from "@/components/ShellPagina";
import TicketPedido from "@/components/TicketPedido";
import {
  consultarOrden,
  esIdPedidoValido,
  PedidoNoEncontradoError,
  type OrdenConsulta,
} from "@/lib/ordenes";

type Estado =
  | { tipo: "cargando" }
  | { tipo: "ok"; orden: OrdenConsulta }
  | { tipo: "no-encontrado" }
  | { tipo: "error" };

function Esqueleto() {
  return <div aria-busy="true" className="mx-auto h-96 max-w-2xl animate-pulse rounded-[25px] bg-white/60" />;
}

function Contenido() {
  const params = useParams<{ id: string }>();
  const nuevo = useSearchParams()?.get("nuevo") === "1";
  const id = String(params?.id ?? "").trim();
  const valido = esIdPedidoValido(id);

  const [estado, setEstado] = useState<Estado>({ tipo: "cargando" });
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    if (!valido) return;
    const control = new AbortController();
    consultarOrden(id, control.signal)
      .then((orden) => setEstado({ tipo: "ok", orden }))
      .catch((err: unknown) => {
        if (control.signal.aborted) return;
        setEstado(err instanceof PedidoNoEncontradoError ? { tipo: "no-encontrado" } : { tipo: "error" });
      });
    return () => control.abort();
  }, [id, valido, intento]);

  function reintentar() {
    setEstado({ tipo: "cargando" });
    setIntento((n) => n + 1);
  }

  if (!valido) {
    return (
      <EstadoVacio
        titulo="Número de pedido no válido"
        detalle="El número debe tener 36 caracteres con guiones, por ejemplo 3f2a9c1e-7b4d-4e0a-9c55-2d1f8a6b7e90."
        accion={{ texto: "Consultar otro pedido", href: "/pedidos" }}
      />
    );
  }
  if (estado.tipo === "cargando") return <Esqueleto />;
  if (estado.tipo === "no-encontrado") {
    return (
      <EstadoVacio
        titulo="Pedido no encontrado"
        detalle="Revisa que el número esté completo y escrito tal como lo recibiste."
        accion={{ texto: "Consultar otro pedido", href: "/pedidos" }}
      />
    );
  }
  if (estado.tipo === "error") {
    return (
      <EstadoVacio
        titulo="No pudimos consultar tu pedido"
        detalle="Verifica tu conexión e inténtalo de nuevo."
        accion={{ texto: "Reintentar", onClick: reintentar }}
      />
    );
  }
  return <TicketPedido orden={estado.orden} nuevo={nuevo} />;
}

export default function PedidoPage() {
  return (
    <ShellPagina>
      <Suspense fallback={<Esqueleto />}>
        <Contenido />
      </Suspense>
    </ShellPagina>
  );
}
