"use client";

import Link from "next/link";

type Accion = { texto: string; onClick?: () => void; href?: string };

const claseBoton =
  "mt-5 rounded-[52px] border-2 border-[#3f0791] bg-[#3f0791] px-6 py-2.5 text-sm font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#5b00ed] active:scale-95";

export default function EstadoVacio({
  titulo,
  detalle,
  accion,
}: {
  titulo: string;
  detalle: string;
  accion?: Accion;
}) {
  return (
    <div className="flex flex-col items-center rounded-[25px] border-2 border-[#3f0791] bg-white px-6 py-14 text-center">
      <svg viewBox="0 0 120 120" className="mb-4 h-28 w-28" aria-hidden="true">
        <circle cx="60" cy="60" r="56" fill="#dad9ff" />
        <path
          d="M30 48h60l-7 36a6 6 0 0 1-6 5H43a6 6 0 0 1-6-5l-7-36Z"
          fill="#FFFFFF"
          stroke="#3f0791"
          strokeWidth="3"
          strokeLinejoin="round"
        />
        <path d="M44 48l10-16M76 48L66 32" fill="none" stroke="#3f0791" strokeWidth="3" strokeLinecap="round" />
        <circle cx="52" cy="67" r="3" fill="#3f0791" />
        <circle cx="68" cy="67" r="3" fill="#3f0791" />
        <path d="M53 79q7-6 14 0" fill="none" stroke="#e30ba6" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <h2 className="text-2xl font-black leading-none tracking-tight text-[#3f0791]">{titulo}</h2>
      <p className="mt-2 max-w-sm text-sm font-medium text-[#3f0791]/80">{detalle}</p>
      {accion &&
        (accion.href ? (
          <Link href={accion.href} className={`inline-block ${claseBoton}`}>
            {accion.texto}
          </Link>
        ) : (
          <button type="button" onClick={accion.onClick} className={claseBoton}>
            {accion.texto}
          </button>
        ))}
    </div>
  );
}
