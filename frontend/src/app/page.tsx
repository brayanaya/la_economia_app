'use client';

import { useState } from 'react';
import Navbar from '@/components/Navbar';
import BuscadorSemantico from '@/components/BuscadorSemantico';
import ProductoCard from '@/components/ProductoCard';
import ChatAgente from '@/components/ChatAgente';
import FooterCompliance from '@/components/FooterCompliance';
import CookieBanner from '@/components/CookieBanner';
import { ProductoRecuperado } from '@/lib/api';

export default function HomePage() {
  const [resultados, setResultados] = useState<ProductoRecuperado[]>([]);
  const [consultaActual, setConsultaActual] = useState<string | null>(null);

  function handleResultados(nuevos: ProductoRecuperado[], consulta: string) {
    setResultados(nuevos);
    setConsultaActual(consulta);
  }

  return (
    <div className='min-h-screen bg-brand-bg flex flex-col'>
      <Navbar />

      <main className='flex-1 max-w-6xl w-full mx-auto px-6 py-8'>
        <div className='mb-8'>
          <h1 className='text-2xl font-bold text-brand-dark mb-1'>Encuentra lo que necesitas</h1>
          <p className='text-gray-500 text-sm mb-4'>
            Busca por nombre o describe lo que buscas, nuestro asistente entiende lenguaje natural.
          </p>
          <BuscadorSemantico onResultados={handleResultados} />
        </div>

        {consultaActual && (
          <p className='text-sm text-gray-500 mb-4'>Resultados para &quot;{consultaActual}&quot;</p>
        )}

        {resultados.length > 0 ? (
          <div className='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5'>
            {resultados.map((p) => (
              <ProductoCard key={p.producto_id} producto={p} />
            ))}
          </div>
        ) : (
          consultaActual && <p className='text-gray-500 text-sm'>No encontramos productos relevantes para esa busqueda.</p>
        )}
      </main>

      <FooterCompliance />
      <ChatAgente />
      <CookieBanner />
    </div>
  );
}
