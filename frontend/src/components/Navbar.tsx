"use client";

import { SEDES } from "@/lib/api";

type Props = {
  sede: string;
  onSedeChange: (nombre: string) => void;
  cartCount?: number;
  onCartClick?: () => void;
  onAccountClick?: () => void;
};

export default function Navbar({ sede, onSedeChange, cartCount = 0, onCartClick, onAccountClick }: Props) {
  return (
    <header className="w-full">
      <div className="bg-brand-dark text-white text-xs">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-2">
          <div className="flex items-center gap-2">
            <span className="text-brand-yellow">📍 Sede:</span>
            <select
              value={sede}
              onChange={(e) => onSedeChange(e.target.value)}
              className="rounded bg-brand-dark px-2 py-1 text-white outline-none ring-1 ring-white/30 focus:ring-brand-yellow"
            >
              {SEDES.map((s) => (
                <option key={s.nombre} value={s.nombre}>{s.nombre}</option>
              ))}
            </select>
          </div>
          <div className="hidden gap-4 sm:flex">
            <span>🚚 Envío rápido en Neiva</span>
            <span className="text-brand-yellow">⚡ Domicilios el mismo día</span>
          </div>
        </div>
      </div>

      <div className="border-b-4 border-brand-yellow bg-brand-red">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3">
          <a href="/" className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="La Economía Aya" className="h-12 w-auto" />
            <span className="hidden text-lg font-extrabold text-white md:block">
              La Economía <span className="text-brand-yellow">Aya</span>
            </span>
          </a>

          <div className="flex items-center gap-3">
            <button
              onClick={onAccountClick}
              className="rounded-full bg-white px-4 py-2 text-sm font-bold text-brand-red transition hover:bg-brand-yellow hover:text-brand-dark"
            >
              👤 Mi Cuenta
            </button>
            <button
              onClick={onCartClick}
              className="relative rounded-full bg-brand-yellow px-4 py-2 text-sm font-bold text-brand-dark transition hover:bg-brand-yellow-dark"
              aria-label="Carrito"
            >
              🛒 Carrito
              <span className="absolute -right-2 -top-2 flex h-6 min-w-6 items-center justify-center rounded-full bg-brand-dark px-1 text-xs font-bold text-white">
                {cartCount}
              </span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}