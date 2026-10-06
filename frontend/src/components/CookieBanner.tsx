'use client';

import { useEffect, useState } from 'react';

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const aceptado = localStorage.getItem('cookies_aceptadas');
    if (!aceptado) setVisible(true);
  }, []);

  function aceptar() {
    localStorage.setItem('cookies_aceptadas', 'true');
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className='fixed bottom-0 left-0 right-0 z-50 bg-brand-dark text-white px-6 py-4 flex flex-col sm:flex-row items-center gap-3 justify-between text-sm'>
      <p className='text-gray-200'>
        Usamos cookies para mejorar tu experiencia de compra y personalizar recomendaciones. Al continuar navegando aceptas nuestra{' '}
        <a href='/politica-datos' className='underline text-brand-yellow'>Politica de tratamiento de datos (Ley 1581)</a>.
      </p>
      <button onClick={aceptar} className='bg-brand-yellow text-brand-dark font-bold px-4 py-2 rounded-lg whitespace-nowrap'>
        Entendido
      </button>
    </div>
  );
}
