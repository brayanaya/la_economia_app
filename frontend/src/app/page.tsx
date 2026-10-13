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

const BENEFICIOS = [
  { icono: "🚚", titulo: "Envío rápido en Neiva", detalle: "Pedidos con entrega ágil dentro de la ciudad." },
  { icono: "⚡", titulo: "Domicilios el mismo día", detalle: "Elige tu sede y recibe tu pedido el mismo día." },
  { icono: "🤖", titulo: "Asistente con IA", detalle: "Pide recomendaciones con tus propias palabras." },
];

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
    <div className="flex flex-col items-center rounded-[25px] border-2 border-[#3f0791] bg-white px-6 py-14 text-center">
      <svg viewBox="0 0 120 120" className="mb-4 h-28 w-28" aria-hidden="true">
        <circle cx="60" cy="60" r="56" fill="#dad9ff" />
        <path
          d="M30 48h60l-7 36a6 6 0 0 1-6 5H43a6 6 0 0 1-6-5l-7-36Z"
          fill="#FFFFFF"
          stroke="#3f0791"
          strokeWidth="3"
          strokeLinejoin="round"
        />
        <path d="M44 48l10-16M76 48L66 32" fill="none" stroke="#3f0791" strokeWidth="3" strokeLinecap="round" />
        <circle cx="52" cy="67" r="3" fill="#3f0791" />
        <circle cx="68" cy="67" r="3" fill="#3f0791" />
        <path d="M53 79q7-6 14 0" fill="none" stroke="#e30ba6" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <h2 className="text-2xl font-black leading-none tracking-tight text-[#3f0791]">{titulo}</h2>
      <p className="mt-2 max-w-sm text-sm font-medium text-[#3f0791]/80">{detalle}</p>
      {accion && (
        <button
          type="button"
          onClick={accion.onClick}
          className="mt-5 rounded-[52px] border-2 border-[#3f0791] bg-[#3f0791] px-6 py-2.5 text-sm font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#5b00ed] active:scale-95"
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
  const etiquetaSede = sede.id === null ? "Todas las sedes" : `Sede ${sede.nombre}`;

  return (
    <div className="min-h-screen bg-white">
      <Navbar
        sede={sede.nombre}
        onSedeChange={(n) => setSede(SEDES.find((s) => s.nombre === n) ?? SEDES[0])}
        cartCount={carrito}
        onCartClick={abrir}
      />

      <section className="bg-gradient-to-tr from-[#e30ba6] to-[#5b00ed]">
        <div className="mx-auto max-w-7xl px-4 py-14 sm:py-20">
          <p className="mb-4 inline-block rounded-[52px] border-2 border-white/80 px-4 py-1 text-xs font-black uppercase tracking-widest text-white">
            Neiva, Huila · {etiquetaSede}
          </p>
          <h1 className="max-w-3xl text-5xl font-black leading-none tracking-tight text-white sm:text-7xl">
            Tu mercado, a un clic.
          </h1>
          <p className="mt-5 max-w-xl text-lg font-medium text-white/90">
            Cuéntanos qué necesitas y nuestra IA encuentra los productos por ti.
          </p>
          <div className="mt-8 max-w-3xl">
            <BuscadorSemantico cargando={cargando} onBuscar={(q) => setConsulta(q.trim() || CONSULTA_INICIAL)} />
          </div>
        </div>
      </section>

      <section className="bg-[#dad9ff]">
        <div className="mx-auto max-w-7xl px-4 py-12">
          <h2 className="text-3xl font-black leading-none tracking-tight text-[#3f0791] sm:text-4xl">
            {esInicial ? "Catálogo" : `Resultados para "${consulta}"`}
          </h2>
          <p className="mb-8 mt-2 text-sm font-semibold text-[#3f0791]/70">{etiquetaSede}</p>

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
        </div>
      </section>

      <section className="bg-white">
        <div className="mx-auto grid max-w-7xl gap-4 px-4 py-12 sm:grid-cols-3">
          {BENEFICIOS.map((b) => (
            <div
              key={b.titulo}
              className="rounded-[25px] border-2 border-[#3f0791] p-6 transition-all duration-300 ease-out hover:-translate-y-1 hover:shadow-[6px_6px_0_0_#3f0791]"
            >
              <p className="text-3xl" aria-hidden="true">{b.icono}</p>
              <h3 className="mt-3 text-xl font-black leading-none tracking-tight text-[#3f0791]">{b.titulo}</h3>
              <p className="mt-2 text-sm font-medium text-[#3f0791]/80">{b.detalle}</p>
            </div>
          ))}
        </div>
      </section>

      <FooterCompliance />
      <ChatAgente sedeId={sede.id} />
    </div>
  );
}
