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
      className={`fixed inset-x-4 bottom-4 z-[80] mx-auto max-w-3xl rounded-2xl border border-white/10 bg-brand-dark/95 p-5 text-sm text-gray-200 shadow-2xl backdrop-blur-md transition-all duration-300 ${
        animado ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
      }`}
    >
      <p className="font-bold text-brand-yellow">🍪 Tu privacidad importa</p>
      <p className="mt-1 leading-relaxed text-gray-300">
        Usamos cookies y almacenamiento local funcionales para recordar tu carrito y mantener tu sesión. Tus datos
        personales se tratan conforme a la Ley 1581 de 2012 (Habeas Data). Consulta la{" "}
        <Link href="/privacidad" className="font-medium text-brand-yellow underline underline-offset-2">
          política de privacidad
        </Link>
        , los{" "}
        <Link href="/terminos" className="font-medium text-brand-yellow underline underline-offset-2">
          términos y condiciones
        </Link>{" "}
        y la{" "}
        <Link href="/cookies" className="font-medium text-brand-yellow underline underline-offset-2">
          política de cookies
        </Link>
        .
      </p>

      {configurando && (
        <div className="mt-4 space-y-3 rounded-xl border border-white/10 bg-white/5 p-4">
          <label className="flex items-start gap-3 opacity-80">
            <input type="checkbox" checked disabled className="mt-1 h-4 w-4 accent-[#FFC72C]" />
            <span>
              <strong className="text-white">Necesarias</strong>
              <span className="block text-xs text-gray-400">
                Carrito, sede y registro de tu decisión. Siempre activas.
              </span>
            </span>
          </label>
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={analiticas}
              onChange={(e) => setAnaliticas(e.target.checked)}
              className="mt-1 h-4 w-4 accent-[#FFC72C]"
            />
            <span>
              <strong className="text-white">Analíticas y mejora del servicio</strong>
              <span className="block text-xs text-gray-400">
                Opcionales. Nos ayudan a entender qué se busca para mejorar el catálogo.
              </span>
            </span>
          </label>
        </div>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => decidir(true)}
          className="rounded-xl bg-brand-yellow px-4 py-2 font-bold text-brand-dark transition-all duration-200 hover:brightness-95 active:scale-95"
        >
          Aceptar todas
        </button>
        {configurando ? (
          <>
            <button
              type="button"
              onClick={() => decidir(analiticas)}
              className="rounded-xl border border-white/20 px-4 py-2 font-semibold text-white transition-all duration-200 hover:bg-white/10 active:scale-95"
            >
              Guardar selección
            </button>
            <button
              type="button"
              onClick={() => decidir(false)}
              className="rounded-xl px-4 py-2 font-semibold text-gray-300 transition-all duration-200 hover:text-white active:scale-95"
            >
              Solo necesarias
            </button>
          </>
        ) : (
          <button
            type="button"
            onClick={() => setConfigurando(true)}
            className="rounded-xl border border-white/20 px-4 py-2 font-semibold text-white transition-all duration-200 hover:bg-white/10 active:scale-95"
          >
            Configurar
          </button>
        )}
      </div>
    </div>
  );
}
