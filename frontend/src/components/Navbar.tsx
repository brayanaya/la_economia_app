import { ShoppingCart } from 'lucide-react';

export default function Navbar() {
  return (
    <header className='bg-brand-red text-white border-b-4 border-brand-yellow'>
      <div className='max-w-6xl mx-auto px-6 py-3 flex items-center justify-between'>
        <div className='flex items-center gap-3'>
          <div className='w-10 h-10 rounded-xl bg-white text-brand-red font-black flex items-center justify-center text-lg shadow'>
            LE
          </div>
          <div>
            <span className='font-extrabold text-xl tracking-tight block leading-none'>LA ECONOMIA</span>
            <span className='text-[10px] text-brand-yellow font-semibold tracking-wider uppercase'>Supermercado Inteligente</span>
          </div>
        </div>

        <nav className='hidden md:flex items-center gap-6 text-sm font-medium'>
          <a href='#' className='hover:text-brand-yellow transition-colors'>Catalogo</a>
          <a href='#' className='hover:text-brand-yellow transition-colors'>Ofertas</a>
          <a href='#' className='hover:text-brand-yellow transition-colors'>Mis pedidos</a>
        </nav>

        <button className='bg-brand-yellow hover:bg-brand-yellow-dark text-brand-dark font-bold text-sm px-4 py-2 rounded-xl flex items-center gap-2 shadow-sm transition-transform active:scale-95'>
          <ShoppingCart size={18} />
          <span>Carrito</span>
          <span className='bg-brand-red text-white text-xs px-2 py-0.5 rounded-full ml-1'>0</span>
        </button>
      </div>
    </header>
  );
}
