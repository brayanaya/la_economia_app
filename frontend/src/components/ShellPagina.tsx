import type { ReactNode } from "react";
import Link from "next/link";
import FooterCompliance from "@/components/FooterCompliance";

export default function ShellPagina({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b-4 border-[#5b00ed] bg-[#3f0791] print:hidden">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link href="/" className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo.png" alt="La Economía Aya" className="h-10 w-auto" />
            <span className="text-lg font-black tracking-tight text-white">La Economía Aya</span>
          </Link>
          <Link
            href="/"
            className="rounded-[52px] border-2 border-white/80 px-4 py-1.5 text-sm font-black text-white transition-all duration-200 hover:bg-white hover:text-[#3f0791] active:scale-95"
          >
            ← Volver a la tienda
          </Link>
        </div>
      </header>

      <main className="bg-[#dad9ff]">
        <div className="mx-auto max-w-5xl px-4 py-10">{children}</div>
      </main>

      <div className="print:hidden">
        <FooterCompliance />
      </div>
    </div>
  );
}
