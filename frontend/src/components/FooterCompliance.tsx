"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const ANIO = 2026;

function Sello({ d, titulo, detalle }: { d: string; titulo: string; detalle: string }) {
  return (
    <div className="flex items-center gap-3 rounded-[25px] border-2 border-white/20 bg-white/5 p-4 transition-all duration-300 ease-out hover:-translate-y-0.5 hover:border-[#dad9ff] hover:bg-white/10">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-8 w-8 shrink-0 text-[#dad9ff]" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d={d} />
      </svg>
      <div>
        <p className="text-sm font-black leading-tight text-white">{titulo}</p>
        <p className="text-xs text-white/70">{detalle}</p>
      </div>
    </div>
  );
}

const ICONO_ESCUDO =
  "M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z";
const ICONO_CHECK = "M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z";
const ICONO_CANDADO =
  "M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z";

const enlace = "text-white/80 underline-offset-4 transition-colors duration-200 hover:text-[#dad9ff] hover:underline";

export default function FooterCompliance() {
  const [https, setHttps] = useState(false);

  useEffect(() => {
    setHttps(window.location.protocol === "https:");
  }, []);

  function abrirCookies() {
    window.dispatchEvent(new Event("la-economia:cookies"));
  }

  return (
    <footer className="border-t-4 border-[#5b00ed] bg-black text-white">
      <div className="mx-auto max-w-7xl space-y-8 px-4 py-12 text-sm">
        <div>
          <p className="text-2xl font-black leading-none tracking-tight text-white">La Economía Aya</p>
          <p className="mt-2 text-white/80">Supermercado y Distribuciones · Neiva, Huila - Colombia</p>
          {/* TODO: reemplazar por el NIT real antes de publicar */}
          <p className="text-white/80">NIT: [PENDIENTE - completar con el NIT real]</p>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <Sello d={ICONO_ESCUDO} titulo="Compra protegida" detalle="Estatuto del Consumidor · Ley 1480 de 2011" />
          <Sello d={ICONO_CHECK} titulo="Habeas Data" detalle="Datos personales · Ley 1581 de 2012" />
          {https && <Sello d={ICONO_CANDADO} titulo="Conexión cifrada" detalle="SSL/TLS (HTTPS)" />}
        </div>

        <nav aria-label="Información legal y atención" className="flex flex-wrap items-center gap-x-6 gap-y-2">
          <Link href="/privacidad" className={enlace}>Política de privacidad</Link>
          <Link href="/terminos" className={enlace}>Términos y condiciones</Link>
          <Link href="/cookies" className={enlace}>Política de cookies</Link>
          <Link href="/pqr" className={enlace}>Canal de atención PQR</Link>
          <button type="button" onClick={abrirCookies} className={enlace}>Configurar cookies</button>
        </nav>

        <p className="rounded-[18px] border-2 border-white/20 p-4 text-xs leading-relaxed text-white/80">
          🤖 <strong className="text-white">Aviso de transparencia:</strong> las recomendaciones del asistente son
          generadas por inteligencia artificial y pueden contener errores. Verifica precio y disponibilidad antes de
          comprar.
        </p>

        <p className="text-xs leading-relaxed text-white/70">
          Tratamiento de datos personales conforme a la Ley 1581 de 2012 (Habeas Data). Derechos del consumidor
          conforme a la Ley 1480 de 2011 (Estatuto del Consumidor). © {ANIO} La Economía Aya. Todos los derechos
          reservados.
        </p>
      </div>
    </footer>
  );
}
