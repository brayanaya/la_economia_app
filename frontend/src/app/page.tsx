"use client";

import { useState } from "react";
import Navbar from "@/components/Navbar";
import ProductoCard from "@/components/ProductoCard";
import ChatAgente from "@/components/ChatAgente";
import FooterCompliance from "@/components/FooterCompliance";
import CookieBanner from "@/components/CookieBanner";

// TODO: reemplazar por la llamada real a tu API de búsqueda RAG
const DEMO = [
  { id: 1, nombre: "Arroz Diana x 500 g", precio: 2800, stock: 40, similitud: 0.94 },
  { id: 2, nombre: "Aceite Gourmet 1 L", precio: 11900, stock: 12, similitud: 0.88 },
  { id: 3, nombre: "Leche Alquería entera 1 L", precio: 4600, stock: 0, similitud: 0.81 },
  { id: 4, nombre: "Panela cuadrada x 500 g", precio: 3500, stock: 25 },
];

export default function Home() {
  const [sede, setSede] = useState("Santa Isabel");
  const [carrito, setCarrito] = useState(0);

  return (
    <div className="min-h-screen bg-brand-bg">
      <Navbar cartCount={carrito} onSedeChange={setSede} />

      <main className="mx-auto max-w-7xl px-4 py-8">
        <h1 className="mb-1 text-2xl font-extrabold text-brand-dark">Ofertas de la semana</h1>
        <p className="mb-6 text-sm text-gray-600">Productos disponibles en la sede {sede}</p>

        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {DEMO.map((p) => (
            <ProductoCard
              key={p.id}
              nombre={p.nombre}
              precio={p.precio}
              stock={p.stock}
              sede={sede}
              similitud={p.similitud}
              onAgregar={() => setCarrito((c) => c + 1)}
            />
          ))}
        </div>
      </main>

      <FooterCompliance />
      <ChatAgente />
      <CookieBanner />
    </div>
  );
}