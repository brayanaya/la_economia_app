import Link from "next/link";

const ANIO = 2026;

export default function FooterCompliance() {
  return (
    <footer className="mt-12 bg-brand-dark text-gray-300">
      <div className="mx-auto max-w-7xl space-y-4 px-4 py-8 text-sm">
        <div>
          <p className="font-bold text-brand-yellow">Supermercado y Distribuciones La Economía Aya</p>
          <p>Neiva, Huila - Colombia</p>
          {/* TODO: reemplazar por el NIT real antes de publicar */}
          <p>NIT: [PENDIENTE - completar con el NIT real]</p>
        </div>

        <nav aria-label="Información legal" className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <Link href="/privacidad" className="transition-colors hover:text-brand-yellow">
            Política de privacidad
          </Link>
          <span aria-hidden className="text-white/20">|</span>
          <Link href="/terminos" className="transition-colors hover:text-brand-yellow">
            Términos y condiciones
          </Link>
        </nav>

        <p className="rounded-lg border border-white/10 p-3 text-xs">
          🤖 <strong>Aviso de transparencia:</strong> las recomendaciones del asistente son generadas por
          inteligencia artificial y pueden contener errores. Verifica precio y disponibilidad antes de comprar.
        </p>

        <p className="text-xs text-gray-400">
          Tratamiento de datos personales conforme a la Ley 1581 de 2012 (Habeas Data). © {ANIO} La Economía
          Aya. Todos los derechos reservados.
        </p>
      </div>
    </footer>
  );
}
