"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import BuscadorSemantico from "@/components/BuscadorSemantico";
import ProductoCard from "@/components/ProductoCard";
import ProductoSkeleton from "@/components/ProductoSkeleton";
import ChatAgente from "@/components/ChatAgente";
import FooterCompliance from "@/components/FooterCompliance";
import { SEDES, buscarSemantica, type Producto } from "@/lib/api";
import { useCarrito } from "@/context/CarritoContext";
import { mostrarAviso } from "@/lib/aviso";

const CONSULTA_INICIAL = "productos de la canasta familiar";

function EstadoVacio({
  titulo,
  detalle,
  accion,
}: {
  titulo: string;
  detalle: string;
  accion?: { texto: string; onClick: () => void };
}) {
  return (
    <div className="flex flex-col items-center rounded-2xl border border-dashed border-gray-300 bg-white px-6 py-14 text-center">
      <svg viewBox="0 0 120 120" className="mb-4 h-28 w-28" aria-hidden="true">
        <circle cx="60" cy="60" r="56" fill="#FFC72C" fillOpacity="0.25" />
        <path
          d="M30 48h60l-7 36a6 6 0 0 1-6 5H43a6 6 0 0 1-6-5l-7-36Z"
          fill="#FFFFFF"
          stroke="#111111"
          strokeWidth="3"
          strokeLinejoin="round"
        />
        <path d="M44 48l10-16M76 48L66 32" fill="none" stroke="#111111" strokeWidth="3" strokeLinecap="round" />
        <circle cx="52" cy="67" r="3" fill="#111111" />
        <circle cx="68" cy="67" r="3" fill="#111111" />
        <path d="M53 79q7-6 14 0" fill="none" stroke="#C8102E" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <h2 className="text-lg font-bold text-brand-dark">{titulo}</h2>
      <p className="mt-1 max-w-sm text-sm text-gray-600">{detalle}</p>
      {accion && (
        <button
          type="button"
          onClick={accion.onClick}
          className="mt-5 rounded-xl bg-brand-red px-5 py-2.5 text-sm font-bold text-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-brand-red/90 hover:shadow-md active:scale-95"
        >
          {accion.texto}
        </button>
      )}
    </div>
  );
}

export default function Home() {
  const { agregar, abrir, totalItems: carrito } = useCarrito();
  const [sede, setSede] = useState(SEDES[1]);
  const [consulta, setConsulta] = useState(CONSULTA_INICIAL);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [intento, setIntento] = useState(0);

  useEffect(() => {
    let cancelado = false;
    async function cargar() {
      setCargando(true);
      setError(null);
      try {
        const res = await buscarSemantica(consulta, sede.id, 8);
        if (!cancelado) setProductos(res);
      } catch {
        if (!cancelado) {
          setProductos([]);
          setError("No pudimos conectar con el catálogo. Verifica que la API esté corriendo.");
        }
      } finally {
        if (!cancelado) setCargando(false);
      }
    }
    cargar();
    return () => {
      cancelado = true;
    };
  }, [consulta, sede.id, intento]);

  function agregarProducto(p: Producto): boolean {
    if (sede.id === null) {
      mostrarAviso("Elige una sede para agregar productos al carrito.");
      return false;
    }
    agregar({
      productoId: String(p.id),
      nombre: p.nombre,
      precio: p.precio,
      sedeId: sede.id,
      sedeNombre: sede.nombre,
      imagen: p.imagen,
    });
    return true;
  }

  const esInicial = consulta === CONSULTA_INICIAL;

  return (
    <div className="min-h-screen bg-brand-bg">
      <Navbar
        sede={sede.nombre}
        onSedeChange={(n) => setSede(SEDES.find((s) => s.nombre === n) ?? SEDES[0])}
        cartCount={carrito}
        onCartClick={abrir}
      />

      <main className="mx-auto max-w-7xl px-4 py-8">
        <BuscadorSemantico cargando={cargando} onBuscar={(q) => setConsulta(q.trim() || CONSULTA_INICIAL)} />

        <h1 className="mb-1 mt-8 text-2xl font-extrabold text-brand-dark">
          {esInicial ? "Catálogo" : `Resultados para "${consulta}"`}
        </h1>
        <p className="mb-6 text-sm text-gray-600">
          {sede.id === null ? "Todas las sedes" : `Sede ${sede.nombre}`}
        </p>

        {error && (
          <EstadoVacio
            titulo="No pudimos cargar el catálogo"
            detalle={error}
            accion={{ texto: "Reintentar", onClick: () => setIntento((n) => n + 1) }}
          />
        )}

        {!error && cargando && (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }, (_, i) => (
              <ProductoSkeleton key={i} />
            ))}
          </div>
        )}

        {!cargando && !error && productos.length === 0 && (
          <EstadoVacio
            titulo="No encontramos productos"
            detalle="Prueba con otras palabras, por ejemplo el tipo de producto o para qué lo necesitas."
            accion={esInicial ? undefined : { texto: "Ver catálogo", onClick: () => setConsulta(CONSULTA_INICIAL) }}
          />
        )}

        {!cargando && !error && productos.length > 0 && (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {productos.map((p, i) => (
              <ProductoCard
                key={`${p.id}-${i}`}
                nombre={p.nombre}
                precio={p.precio}
                stock={p.stock}
                imagen={p.imagen}
                sede={p.sede ?? (sede.id === null ? "todas las sedes" : sede.nombre)}
                similitud={esInicial ? undefined : p.similitud}
                onAgregar={() => agregarProducto(p)}
              />
            ))}
          </div>
        )}
      </main>

      <FooterCompliance />
      <ChatAgente sedeId={sede.id} />
    </div>
  );
}


