import Link from "next/link";

type SuccessPageProps = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ ticket_id?: string }>;
};

export default async function SuccessPage({
  params,
  searchParams,
}: SuccessPageProps) {
  const [{ id: ordenId }, { ticket_id: ticketId }] = await Promise.all([
    params,
    searchParams,
  ]);

  return (
    <main className="min-h-screen bg-[#fff8e7] px-5 py-12 text-black">
      <section className="mx-auto w-full max-w-2xl border-4 border-black bg-white p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] sm:p-10">
        <div className="mb-8 inline-block -rotate-2 border-4 border-black bg-[#FFD700] px-4 py-2">
          <p className="text-sm font-black uppercase tracking-[0.2em]">
            La Economía Aya
          </p>
        </div>

        <div className="mb-8 text-center">
          <div
            aria-hidden="true"
            className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-full border-4 border-black bg-[#e30ba6] text-4xl font-black text-white"
          >
            ✓
          </div>
          <h1 className="text-3xl font-black uppercase leading-tight sm:text-5xl">
            ¡Pago exitoso!
          </h1>
          <p className="mt-3 text-lg font-bold">
            Tu pago fue procesado. Gracias por comprar en La Economía Aya.
          </p>
        </div>

        <div className="mb-5 border-4 border-dashed border-black bg-[#FFD700] p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em]">
            Número de pedido
          </p>
          <p className="mt-2 break-all text-lg font-black">{ordenId}</p>
        </div>

        <div className="mb-8 border-4 border-dashed border-black bg-white p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em]">
            Ticket de pago
          </p>
          <p className="mt-2 break-all text-xl font-black">
            {ticketId || ordenId}
          </p>
        </div>

        <aside
          aria-label="Información sobre el derecho de retracto"
          className="mb-8 border-4 border-black bg-[#e30ba6] p-5 text-white shadow-[5px_5px_0px_0px_rgba(0,0,0,1)]"
        >
          <h2 className="mb-2 text-lg font-black uppercase">
            Derecho de retracto
          </h2>
          <p className="font-semibold leading-relaxed">
            De acuerdo con la Ley 1480 de 2011 (Estatuto del Consumidor), tienes derecho al retracto de esta compra dentro de los 5 días hábiles siguientes a la entrega del producto.
          </p>
        </aside>

        <Link
          href="/"
          className="block w-full border-4 border-black bg-[#FFD700] px-6 py-4 text-center text-lg font-black uppercase shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] transition-transform hover:translate-x-1 hover:translate-y-1 hover:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-4 focus-visible:outline-[#e30ba6]"
        >
          Volver al inicio
        </Link>
      </section>
    </main>
  );
}
