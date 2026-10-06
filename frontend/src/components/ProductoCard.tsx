import { ProductoRecuperado } from '@/lib/api';

function formatearCOP(valor: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(valor);
}

export default function ProductoCard({ producto }: { producto: ProductoRecuperado }) {
  const sinStock = producto.stock_sede !== null && producto.stock_sede <= 0;

  return (
    <div className='bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-3 shadow-sm'>
      <div className='flex items-start justify-between'>
        <div className='w-12 h-12 rounded-lg bg-brand-dark flex items-center justify-center text-brand-yellow font-bold'>
          {producto.nombre.charAt(0)}
        </div>
        {sinStock ? (
          <span className='bg-red-100 text-brand-red-dark text-[11px] font-bold px-2.5 py-1 rounded-full'>Agotado</span>
        ) : (
          <span className='bg-emerald-100 text-brand-green-dark text-[11px] font-bold px-2.5 py-1 rounded-full'>Disponible</span>
        )}
      </div>

      <h3 className='font-semibold text-brand-dark text-sm leading-snug'>{producto.nombre}</h3>
      {producto.categoria_nombre && <p className='text-xs text-gray-500'>{producto.categoria_nombre}</p>}

      <div className='flex items-center justify-between mt-auto pt-1'>
        <span className='text-lg font-bold text-brand-red'>{formatearCOP(producto.precio)}</span>
        <button
          disabled={sinStock}
          className='px-3 py-2 rounded-lg bg-brand-green hover:bg-brand-green-dark disabled:bg-gray-200 disabled:text-gray-400 text-white text-xs font-bold'
        >
          Agregar
        </button>
      </div>
    </div>
  );
}
