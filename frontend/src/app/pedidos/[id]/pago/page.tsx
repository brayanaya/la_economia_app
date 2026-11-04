import { Suspense } from "react";
import { PagoReturnClient } from "./PagoReturnClient";

interface PageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ transaction_id?: string; reference?: string; status?: string }>;
}

export default async function PagoReturnPage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const resolvedSearchParams = await searchParams;

  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
            <div className="px-6 py-8 text-center bg-blue-50">
              <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto" />
              <h1 className="mt-4 text-2xl font-black text-gray-900">Verificando pago…</h1>
              <p className="mt-2 text-gray-600">Consultando el estado de tu transacción con Wompi.</p>
            </div>
          </div>
        </div>
      </div>
    }>
      <PagoReturnClient ordenId={id} initialSearchParams={resolvedSearchParams} />
    </Suspense>
  );
}