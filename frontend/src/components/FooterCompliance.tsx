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

        <p className="rounded-lg border border-white/10 p-3 text-xs">
          🤖 <strong>Aviso de transparencia:</strong> las recomendaciones del asistente son generadas por
          inteligencia artificial y pueden contener errores. Verifica precio y disponibilidad antes de comprar.
        </p>

        <p className="text-xs text-gray-400">
          Tratamiento de datos personales conforme a la Ley 1581 de 2012 (Habeas Data). ©{" "}
          {new Date().getFullYear()} La Economía Aya. Todos los derechos reservados.
        </p>
      </div>
    </footer>
  );
}