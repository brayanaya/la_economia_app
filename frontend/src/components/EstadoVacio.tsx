import Link from "next/link";

interface AccionProps {
  texto: string;
  href?: string;
  onClick?: () => void;
}

export default function EstadoVacio({
  titulo,
  detalle,
  accion,
}: {
  titulo: string;
  detalle: string;
  accion?: AccionProps;
}) {
  return (
    <div className="mx-auto flex max-w-lg flex-col items-center justify-center rounded-[25px] border-4 border-[#6B1020] bg-white p-10 text-center shadow-[8px_8px_0px_0px_rgba(107,16,32,1)] print:border-none print:shadow-none">
      <div
        aria-hidden="true"
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border-4 border-[#6B1020] bg-[#F3E6D9] text-4xl print:hidden"
      >
        👀
      </div>
      <h2 className="mb-3 text-2xl font-black tracking-tight text-[#6B1020]">{titulo}</h2>
      <p className="mb-8 font-bold text-[#6B1020]/70">{detalle}</p>

      {accion && accion.href && (
        <Link
          href={accion.href}
          className="rounded-[52px] border-2 border-[#6B1020] bg-[#C8102E] px-8 py-3 text-sm font-black uppercase tracking-wide text-white transition-all hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(107,16,32,1)] active:translate-y-0 active:shadow-none print:hidden"
        >
          {accion.texto}
        </Link>
      )}

      {accion && accion.onClick && (
        <button
          onClick={accion.onClick}
          className="rounded-[52px] border-2 border-[#6B1020] bg-[#C8102E] px-8 py-3 text-sm font-black uppercase tracking-wide text-white transition-all hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(107,16,32,1)] active:translate-y-0 active:shadow-none print:hidden"
        >
          {accion.texto}
        </button>
      )}
    </div>
  );
}
