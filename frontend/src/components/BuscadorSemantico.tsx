'use client';

import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { buscarProductos, ProductoRecuperado } from '@/lib/api';

const SEDES = [
  { id: 'a0000000-0000-0000-0000-000000000001', nombre: 'Santa Isabel' },
  { id: 'a0000000-0000-0000-0000-000000000002', nombre: 'Machines' },
];

interface Props {
  onResultados: (resultados: ProductoRecuperado[], consulta: string) => void;
}

export default function BuscadorSemantico({ onResultados }: Props) {
  const [consulta, setConsulta] = useState('');
  const [sedeId, setSedeId] = useState<string>('');
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleBuscar(e: React.FormEvent) {
    e.preventDefault();
    if (consulta.trim().length < 2) return;

    setCargando(true);
    setError(null);
    try {
      const data = await buscarProductos({
        consulta,
        sede_id: sedeId || null,
        top_k: 8,
        limite_resultados: 6,
      });
      onResultados(data.resultados, data.consulta);
    } catch (err) {
      setError('No pudimos conectar con el catalogo. Intenta de nuevo.');
      console.error(err);
    } finally {
      setCargando(false);
    }
  }

  return (
    <form onSubmit={handleBuscar} className='flex flex-col sm:flex-row gap-3 w-full'>
      <div className='relative flex-1'>
        <Search className='absolute left-4 top-1/2 -translate-y-1/2 text-gray-400' size={18} aria-hidden />
        <input
          type='text'
          value={consulta}
          onChange={(e) => setConsulta(e.target.value)}
          placeholder='Que estas buscando hoy? Ej: cafe molido, leche, arroz...'
          aria-label='Buscar productos'
          className='w-full pl-11 pr-4 py-3 rounded-lg border border-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-red'
        />
      </div>

      <select
        value={sedeId}
        onChange={(e) => setSedeId(e.target.value)}
        aria-label='Seleccionar sede'
        className='px-4 py-3 rounded-lg border border-gray-200 bg-white text-sm'
      >
        <option value=''>Todas las sedes</option>
        {SEDES.map((s) => (
          <option key={s.id} value={s.id}>Sede: {s.nombre}</option>
        ))}
      </select>

      <button
        type='submit'
        disabled={cargando}
        className='px-6 py-3 rounded-lg bg-brand-red hover:bg-brand-red-dark text-white font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-60'
      >
        {cargando ? <Loader2 className='animate-spin' size={16} /> : null}
        Buscar
      </button>

      {error && <p role='alert' className='text-brand-red-dark text-xs sm:ml-2 self-center'>{error}</p>}
    </form>
  );
}
