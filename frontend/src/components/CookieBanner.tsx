"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const CLAVE = "la_economia_cookies_v1";
const EVENTO = "la-economia:cookies";

interface Preferencias {
  analiticas: boolean;
  fecha: string;
}

function leer(): Preferencias | null {
  try {
    const raw = window.localStorage.getItem(CLAVE);
    if (!raw) return null;
    const d = JSON.parse(raw) as Partial<Preferencias>;
    if (typeof d.analiticas !== "boolean") return null;
    return { analiticas: d.analiticas, fecha: String(d.fecha ?? "") };
  } catch {
    return null;
  }
}

function guardar(analiticas: boolean) {
  try {
    const datos: Preferencias = { analiticas, fecha: new Date().toISOString() };
    window.localStorage.setItem(CLAVE, JSON.stringify(datos));
  } catch {
    /* almacenamiento no disponible */
  }
}

const enlace = "font-bold underline underline-offset-2 transition-colors duration-200 hover:text-[#8B1E2D]";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);
  const [animado, setAnimado] = useState(false);
  const [configurando, setConfigurando] = useState(false);
  const [analiticas, setAnaliticas] = useState(false);

  useEffect(() => {
    const previa = leer();
    if (previa === null) setVisible(true);
    else setAnaliticas(previa.analiticas);

    function reabrir() {
      setAnaliticas(leer()?.analiticas ?? false);
      setConfigurando(true);
      setVisible(true);
    }
    window.addEventListener(EVENTO, reabrir);
    return () => window.removeEventListener(EVENTO, reabrir);
  }, []);

  useEffect(() => {
    if (!visible) {
      setAnimado(false);
      return;
    }
    const id = requestAnimationFrame(() => setAnimado(true));
    return () => cancelAnimationFrame(id);
  }, [visible]);

  function decidir(valor: boolean) {
    guardar(valor);
    setVisible(false);
    setConfigurando(false);
  }

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-label="Preferencias de cookies"
      className={`fixed inset-x-4 bottom-4 z-[80] mx-auto max-w-3xl rounded-[25px] border-2 border-[#6B1020] bg-white/95 p-6 text-sm text-[#6B1020] shadow-[6px_6px_0_0_#6B1020] backdrop-blur-md transition-all duration-300 ease-out ${
        animado ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
      }`}
    >
      <p className="text-xl font-black leading-none tracking-tight">🍪 Tu privacidad importa</p>
      <p className="mt-3 leading-relaxed text-[#6B1020]/90">
        Usamos cookies y almacenamiento local funcionales para recordar tu carrito y mantener tu sesión. Tus datos
        personales se tratan conforme a la Ley 1581 de 2012 (Habeas Data). Consulta la{" "}
        <Link href="/privacidad" className={enlace}>política de privacidad</Link>, los{" "}
        <Link href="/terminos" className={enlace}>términos y condiciones</Link> y la{" "}
        <Link href="/cookies" className={enlace}>política de cookies</Link>.
      </p>

      {configurando && (
        <div className="mt-4 space-y-3 rounded-[18px] bg-[#F3E6D9]/60 p-4">
          <label className="flex items-start gap-3 opacity-80">
            <input type="checkbox" checked disabled className="mt-1 h-4 w-4 accent-[#6B1020]" />
            <span>
              <strong>Necesarias</strong>
              <span className="block text-xs text-[#6B1020]/80">
                Carrito, sede y registro de tu decisión. Siempre activas.
              </span>
            </span>
          </label>
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={analiticas}
              onChange={(e) => setAnaliticas(e.target.checked)}
              className="mt-1 h-4 w-4 accent-[#6B1020]"
            />
            <span>
              <strong>Analíticas y mejora del servicio</strong>
              <span className="block text-xs text-[#6B1020]/80">
                Opcionales. Nos ayudan a entender qué se busca para mejorar el catálogo.
              </span>
            </span>
          </label>
        </div>
      )}

      <div className="mt-5 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => decidir(true)}
          className="rounded-[52px] border-2 border-[#6B1020] bg-[#6B1020] px-6 py-2.5 font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#8B1E2D] active:scale-95"
        >
          Aceptar todas
        </button>
        {configurando ? (
          <>
            <button
              type="button"
              onClick={() => decidir(analiticas)}
              className="rounded-[52px] border-2 border-[#6B1020] px-6 py-2.5 font-black text-[#6B1020] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#F3E6D9] active:scale-95"
            >
              Guardar selección
            </button>
            <button
              type="button"
              onClick={() => decidir(false)}
              className="rounded-[52px] px-4 py-2.5 font-bold text-[#6B1020]/80 transition-all duration-200 hover:text-[#6B1020] active:scale-95"
            >
              Solo necesarias
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => setConfigurando(true)}
            className="rounded-[52px] border-2 border-[#6B1020] px-6 py-2.5 font-black text-[#6B1020] transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#F3E6D9] active:scale-95"
          >
            Configurar
          </button>
        )}
      </div>
    </div>
  );
}
