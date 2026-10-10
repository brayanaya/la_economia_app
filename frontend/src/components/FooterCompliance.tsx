"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const ANIO = 2026;

function Sello({ d, titulo, detalle }: { d: string; titulo: string; detalle: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 p-3 transition-colors duration-200 hover:bg-white/10">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-7 w-7 shrink-0 text-brand-yellow" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d={d} />
      </svg>
      <div>
        <p className="text-xs font-bold text-white">{titulo}</p>
        <p className="text-[11px] text-gray-400">{detalle}</p>
      </div>
    </div>
  );
}

const ICONO_ESCUDO =
  "M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z";
const ICONO_CHECK = "M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z";
const ICONO_CANDADO =
  "M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z";

const enlace = "transition-colors duration-200 hover:text-brand-yellow";

export default function FooterCompliance() {
  const [https, setHttps] = useState(false);

  useEffect(() => {
    setHttps(window.location.protocol === "https:");
  }, []);

  function abrirCookies() {
    window.dispatchEvent(new Event("la-economia:cookies"));
  }

  return (
    <footer className="mt-12 bg-brand-dark text-gray-300">
      <div className="mx-auto max-w-7xl space-y-6 px-4 py-10 text-sm">
        <div>
          <p className="font-bold text-brand-yellow">Supermercado y Distribuciones La Economía Aya</p>
          <p>Neiva, Huila - Colombia</p>
          {/* TODO: reemplazar por el NIT real antes de publicar */}
          <p>NIT: [PENDIENTE - completar con el NIT real]</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Sello d={ICONO_ESCUDO} titulo="Compra protegida" detalle="Garantía legal · Ley 1480 de 2011" />
          <Sello d={ICONO_CHECK} titulo="Habeas Data" detalle="Datos personales · Ley 1581 de 2012" />
          {https && <Sello d={ICONO_CANDADO} titulo="Conexión cifrada" detalle="SSL/TLS (HTTPS)" />}
        </div>

        <nav aria-label="Información legal y atención" className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <Link href="/privacidad" className={enlace}>Política de privacidad</Link>
          <Link href="/terminos" className={enlace}>Términos y condiciones</Link>
          <Link href="/cookies" className={enlace}>Política de cookies</Link>
          <Link href="/pqr" className={enlace}>Canal de atención PQR</Link>
          <button type="button" onClick={abrirCookies} className={enlace}>Configurar cookies</button>
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
