"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

export default function SplashScreen() {
  const [leaving, setLeaving] = useState(false);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const leaveTimer = window.setTimeout(() => setLeaving(true), 3000);
    const removeTimer = window.setTimeout(() => setVisible(false), 3600);
    return () => {
      window.clearTimeout(leaveTimer);
      window.clearTimeout(removeTimer);
    };
  }, []);

  if (!visible) return null;

  return (
    <div
      aria-label="Cargando La Economía Aya"
      role="status"
      className={`fixed inset-0 z-[100] flex items-center justify-center bg-black transition-opacity duration-500 ease-out ${leaving ? "pointer-events-none opacity-0" : "opacity-100"}`}
    >
      <div className={`flex flex-col items-center transition-transform duration-500 ease-out ${leaving ? "scale-95" : "scale-100"}`}>
        <Image
          src="/logo.png"
          alt="La Economía Aya"
          width={280}
          height={280}
          priority
          className="h-auto w-48 animate-soft-pulse object-contain sm:w-56"
        />
        <span className="mt-8 text-[10px] font-medium uppercase tracking-[0.3em] text-white/55">Preparando tu mercado</span>
      </div>
    </div>
  );
}
