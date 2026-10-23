import type { ReactNode } from "react";
import Link from "next/link";
import FooterCompliance from "@/components/FooterCompliance";

export default function ShellPagina({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b-4 border-[#8B1E2D] bg-[#6B1020] print:hidden">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-2 px-4 py-3">
          <Link href="/" className="flex min-w-0 items-center gap-2 sm:gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="La Economía Aya" className="h-8 w-auto sm:h-10" />
            <span className="hidden text-lg font-black tracking-tight text-white sm:inline">La Economía Aya</span>
          </Link>
          <Link
            href="/"
            className="shrink-0 whitespace-nowrap rounded-[52px] border-2 border-white/80 px-3 py-1.5 text-xs font-black text-white transition-all duration-200 hover:bg-white hover:text-[#6B1020] active:scale-95 sm:px-4 sm:text-sm"
          >
            ← Volver a la tienda
          </Link>
        </div>
      </header>

      <main className="bg-[#F3E6D9]">
        <div className="mx-auto max-w-5xl px-4 py-10">{children}</div>
      </main>

      <div className="print:hidden">
        <FooterCompliance />
      </div>
    </div>
  );
}
