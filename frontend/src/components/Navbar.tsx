"use client";

import Image from "next/image";
import Link from "next/link";
import { ShoppingCart, UserRound } from "lucide-react";

type Props = {
  cartCount?: number;
  onCartClick?: () => void;
  onAccountClick?: () => void;
};

export default function Navbar({ cartCount = 0, onCartClick, onAccountClick }: Props) {
  return (
    <header className="fixed left-1/2 top-4 z-50 w-[95%] max-w-7xl -translate-x-1/2 text-white">
      <div className="mx-auto flex w-full flex-wrap items-center justify-between gap-x-5 gap-y-3 rounded-2xl bg-[#570008]/85 px-4 py-3 shadow-[0_12px_40px_rgba(35,0,5,0.28)] backdrop-blur-xl sm:px-7 sm:py-4">
        <a href="#inicio" aria-label="La Economía Aya, inicio" className="flex shrink-0 items-center transition-all duration-300 ease-in-out hover:-translate-y-1 hover:opacity-90">
          <Image src="/logo.png" alt="La Economía Aya" width={150} height={50} priority className="h-12 w-auto object-contain sm:h-14" />
        </a>

        <nav aria-label="Navegación principal" className="order-3 flex w-full items-center justify-center gap-5 overflow-x-auto text-sm font-semibold text-white/85 sm:order-none sm:w-auto sm:gap-7 sm:text-base">
          <a href="#inicio" className="whitespace-nowrap transition-all duration-300 ease-in-out hover:-translate-y-1 hover:text-amber-300">Inicio</a>
          <a href="#catalogo" className="whitespace-nowrap transition-all duration-300 ease-in-out hover:-translate-y-1 hover:text-amber-300">Catálogo</a>
          <a href="#quienes-somos" className="whitespace-nowrap transition-all duration-300 ease-in-out hover:-translate-y-1 hover:text-amber-300">Quiénes Somos</a>
          <a href="#ubicanos" className="whitespace-nowrap transition-all duration-300 ease-in-out hover:-translate-y-1 hover:text-amber-300">Ubícanos</a>
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/cuenta"
            onClick={onAccountClick}
            className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-2 text-sm font-semibold text-white transition-all duration-300 ease-in-out hover:-translate-y-1 hover:bg-white/20 hover:shadow-[0_8px_30px_rgb(0,0,0,0.18)] sm:px-4"
          >
            <UserRound className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">Mi Cuenta</span>
          </Link>
          <button
            type="button"
            onClick={onCartClick}
            className="relative inline-flex items-center gap-2 rounded-full bg-amber-400 px-3 py-2 text-sm font-bold text-[#32100D] transition-all duration-300 ease-in-out hover:-translate-y-1 hover:bg-amber-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.18)] sm:px-4"
            aria-label={`Abrir carrito, ${cartCount} artículos`}
          >
            <ShoppingCart className="h-4 w-4" aria-hidden="true" />
            <span className="hidden sm:inline">Carrito</span>
              <span
                key={cartCount}
                className="absolute -right-2 -top-2 flex h-6 min-w-6 animate-pulse items-center justify-center rounded-full bg-brand-dark px-1 text-xs font-bold text-white"
              >
                {cartCount}
              </span>
          </button>
        </div>
      </div>
    </header>
  );
}


