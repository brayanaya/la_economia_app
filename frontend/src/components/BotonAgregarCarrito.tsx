// carrito-v1
"use client";

import { useState } from "react";
import { useCarrito } from "@/context/CarritoContext";

interface Props {
  productoId: string | number;
  nombre: string;
  precio: number;
  sedeId: string;
  sedeNombre?: string;
  imagen?: string;
  className?: string;
}

export default function BotonAgregarCarrito({
  productoId, nombre, precio, sedeId, sedeNombre, imagen, className,
}: Props) {
  const { agregar } = useCarrito();
  const [agregado, setAgregado] = useState(false);

  const onClick = () => {
    agregar({ productoId: String(productoId), nombre, precio, sedeId, sedeNombre, imagen });
    setAgregado(true);
    window.setTimeout(() => setAgregado(false), 1200);
  };

  return (
    <button
      type="button"
      onClick={onClick}
      className={className ?? "rounded-lg bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-700"}
    >
      {agregado ? "Agregado ✓" : "Agregar al carrito"}
    </button>
  );
}
