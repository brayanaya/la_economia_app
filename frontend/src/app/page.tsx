"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import BuscadorSemantico from "@/components/BuscadorSemantico";
import ProductoCard from "@/components/ProductoCard";
import ChatAgente from "@/components/ChatAgente";
import FooterCompliance from "@/components/FooterCompliance";
import CookieBanner from "@/components/CookieBanner";
import { SEDES, buscarSemantica, type Producto } from "@/lib/api";
import { useCarrito } from "@/context/CarritoContext";
import { mostrarAviso } from "@/lib/aviso";

const CONSULTA_INICIAL = "productos de la canasta familiar";

export default function Home() {
  const { agregar, totalItems: carrito } = useCarrito();
  const [sede, setSede] = useState(SEDES[1]);
  const [consulta, setConsulta] = useState(CONSULTA_INICIAL);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
  }, [consulta, sede.id]);

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
      />

      <main className="mx-auto max-w-7xl px-4 py-8">
        <BuscadorSemantico cargando={cargando} onBuscar={setConsulta} />

        <h1 className="mb-1 mt-6 text-2xl font-extrabold text-brand-dark">
          {esInicial ? "Catálogo" : `Resultados para "${consulta}"`}
        </h1>
        <p className="mb-6 text-sm text-gray-600">
          {sede.id === null ? "Todas las sedes" : `Sede ${sede.nombre}`}
        </p>

        {error && (
          <p className="mb-4 rounded-lg border border-brand-red/30 bg-white p-3 text-sm text-brand-red">{error}</p>
        )}

        {!cargando && !error && productos.length === 0 && (
          <p className="text-sm text-gray-600">No encontramos productos para esa búsqueda.</p>
        )}

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
      </main>

      <FooterCompliance />
      <ChatAgente sedeId={sede.id} />
      <CookieBanner />
    </div>
  );
}
