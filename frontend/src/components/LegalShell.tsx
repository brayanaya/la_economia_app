import type { ReactNode } from "react";
import Link from "next/link";

interface LegalShellProps {
  titulo: string;
  ultimaActualizacion?: string;
  children: ReactNode;
}

export function Pendiente({ children }: { children: ReactNode }) {
  return (
    <mark className="rounded-[8px] bg-[#C8102E]/15 px-1.5 py-0.5 font-bold text-[#6B1020] ring-1 ring-[#C8102E]/40">
      [PENDIENTE: {children}]
    </mark>
  );
}

export default function LegalShell({ titulo, ultimaActualizacion, children }: LegalShellProps) {
  return (
    <main className="min-h-screen bg-[#F3E6D9] px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <Link
          href="/"
          className="mb-6 inline-flex items-center gap-1 rounded-[52px] border-2 border-[#6B1020] bg-white px-4 py-1.5 text-sm font-black text-[#6B1020] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#6B1020] hover:text-white active:scale-95"
        >
          ← Volver a la tienda
        </Link>

        <div className="rounded-[25px] border-2 border-[#6B1020] bg-white p-8 shadow-xl sm:p-10">
          <header className="mb-6 border-b-2 border-[#F3E6D9] pb-6">
            <h1 className="text-4xl font-black leading-none tracking-tight text-[#6B1020] sm:text-5xl">{titulo}</h1>
            {ultimaActualizacion && (
              <p className="mt-3 text-sm font-semibold text-[#6B1020]/70">Última actualización: {ultimaActualizacion}</p>
            )}
          </header>

          <div
            role="note"
            className="mb-8 rounded-[18px] border-2 border-[#6B1020]/30 bg-[#F3E6D9]/50 px-4 py-3 text-sm text-[#6B1020]"
          >
            <strong>Documento en borrador.</strong> Este texto debe ser revisado por un profesional jurídico antes
            de su publicación definitiva. Los campos marcados como{" "}
            <Pendiente>dato por completar</Pendiente> requieren información real del responsable.
          </div>

          <div className="space-y-8 text-[15px] leading-relaxed text-[#6B1020]/90 [&_a]:font-bold [&_h2]:mb-3 [&_h2]:text-2xl [&_h2]:font-black [&_h2]:leading-none [&_h2]:tracking-tight [&_h2]:text-[#6B1020] [&_li]:ml-5 [&_li]:list-disc [&_ul]:space-y-1.5">
            {children}
          </div>
        </div>
      </div>
    </main>
  );
}
