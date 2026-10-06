import { ShoppingCart } from 'lucide-react';

export default function Navbar() {
  return (
    <header className='bg-brand-dark text-white px-6 py-4 flex items-center justify-between'>
      <div className='flex items-center gap-3'>
        <div className='w-8 h-8 rounded-md bg-brand-red flex items-center justify-center font-bold text-sm'>LE</div>
        <span className='font-bold text-lg'>La Economia</span>
      </div>

      <nav className='hidden sm:flex items-center gap-6 text-sm'>
        <a href='#' className='hover:text-brand-yellow'>Catalogo</a>
        <a href='#' className='hover:text-brand-yellow'>Ofertas</a>
        <a href='#' className='hover:text-brand-yellow'>Mis pedidos</a>
      </nav>

      <button className='bg-brand-yellow text-brand-dark font-bold text-sm px-4 py-2 rounded-lg flex items-center gap-2'>
        <ShoppingCart size={16} />
        Carrito - 0
      </button>
    </header>
  );
}
