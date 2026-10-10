import type { ReactNode } from "react";

interface LegalShellProps {
  titulo: string;
  ultimaActualizacion?: string;
  children: ReactNode;
}

export function Pendiente({ children }: { children: ReactNode }) {
  return (
    <mark className="rounded-md bg-brand-yellow/40 px-1.5 py-0.5 font-medium text-brand-dark">
      [PENDIENTE: {children}]
    </mark>
  );
}

export default function LegalShell({ titulo, ultimaActualizacion, children }: LegalShellProps) {
  return (
    <main className="min-h-screen bg-brand-bg px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <a
          href="/"
          className="mb-6 inline-flex items-center gap-1 text-sm font-medium text-brand-dark/70 transition-colors hover:text-brand-red"
        >
          ← Volver a la tienda
        </a>

        <div className="rounded-2xl border border-black/5 bg-white p-6 shadow-sm sm:p-10">
          <header className="mb-6 border-b border-gray-200/80 pb-6">
            <h1 className="text-3xl font-bold text-brand-dark">{titulo}</h1>
            {ultimaActualizacion && (
              <p className="mt-2 text-sm text-brand-dark/60">Última actualización: {ultimaActualizacion}</p>
            )}
          </header>

          <div
            role="note"
            className="mb-8 rounded-xl border border-brand-yellow/60 bg-brand-yellow/15 px-4 py-3 text-sm text-brand-dark"
          >
            <strong>Documento en borrador.</strong> Este texto debe ser revisado por un profesional jurídico antes
            de su publicación definitiva. Los campos marcados como{" "}
            <Pendiente>dato por completar</Pendiente> requieren información real del responsable.
          </div>

          <div className="space-y-8 text-[15px] leading-relaxed text-brand-dark/90 [&_h2]:mb-3 [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-brand-dark [&_li]:ml-5 [&_li]:list-disc [&_ul]:space-y-1.5">
            {children}
          </div>
        </div>
      </div>
    </main>
  );
}
