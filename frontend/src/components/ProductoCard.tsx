import { ProductoRecuperado } from '@/lib/api';

function formatearCOP(valor: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(valor);
}

export default function ProductoCard({ producto }: { producto: ProductoRecuperado }) {
  const sinStock = producto.stock_sede !== null && producto.stock_sede <= 0;

  return (
    <div className='bg-white border border-gray-200 rounded-2xl p-5 flex flex-col gap-3 shadow-sm hover:shadow-md transition-shadow'>
      <div className='flex items-start justify-between'>
        <div className='w-12 h-12 rounded-xl bg-red-50 text-brand-red font-black text-lg flex items-center justify-center border border-red-100'>
          {producto.nombre.charAt(0)}
        </div>
        {sinStock ? (
          <span className='bg-red-100 text-red-700 text-[11px] font-bold px-3 py-1 rounded-full'>Agotado</span>
        ) : (
          <span className='bg-emerald-100 text-emerald-800 text-[11px] font-bold px-3 py-1 rounded-full'>En stock</span>
        )}
      </div>

      <div>
        <span className='text-[11px] text-gray-400 uppercase tracking-wider font-semibold'>
          {producto.categoria_nombre || 'Abarrotes'}
        </span>
        <h3 className='font-bold text-gray-900 text-base leading-snug mt-0.5'>{producto.nombre}</h3>
      </div>

      <div className='text-[11px] bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md w-max font-medium'>
        Similitud RAG: {(producto.similitud * 100).toFixed(1)}%
      </div>

      <div className='flex items-center justify-between mt-auto pt-3 border-t border-gray-100'>
        <div>
          <span className='text-xs text-gray-400 block leading-none'>Precio</span>
          <span className='text-xl font-extrabold text-brand-red'>{formatearCOP(producto.precio)}</span>
        </div>
        <button
          disabled={sinStock}
          className='px-4 py-2.5 rounded-xl bg-brand-green hover:bg-brand-green-dark disabled:bg-gray-200 disabled:text-gray-400 text-white text-xs font-bold shadow-sm transition-transform active:scale-95'
        >
          Agregar
        </button>
      </div>
    </div>
  );
}
