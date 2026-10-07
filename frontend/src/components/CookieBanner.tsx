"use client";

import { useEffect, useState } from "react";

const KEY = "habeas_data_consent";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (!localStorage.getItem(KEY)) setVisible(true);
    } catch {
      setVisible(true);
    }
  }, []);

  function responder(valor: "aceptado" | "rechazado") {
    try {
      localStorage.setItem(KEY, valor);
    } catch {}
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t-4 border-brand-yellow bg-brand-dark p-4 text-white shadow-2xl">
      <div className="mx-auto flex max-w-7xl flex-col items-start gap-3 md:flex-row md:items-center">
        <p className="flex-1 text-xs md:text-sm">
          En cumplimiento de la <strong>Ley 1581 de 2012 (Habeas Data)</strong>, usamos tus datos personales y
          cookies para mejorar tu experiencia y personalizar las recomendaciones. Puedes aceptar o rechazar su uso.
        </p>
        <div className="flex gap-2">
          <button
            onClick={() => responder("rechazado")}
            className="rounded-lg border border-white/40 px-4 py-2 text-sm hover:bg-white/10"
          >
            Rechazar
          </button>
          <button
            onClick={() => responder("aceptado")}
            className="rounded-lg bg-brand-yellow px-4 py-2 text-sm font-bold text-brand-dark hover:bg-brand-yellow-dark"
          >
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}