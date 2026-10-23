"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import ShellPagina from "@/components/ShellPagina";
import { esIdPedidoValido } from "@/lib/ordenes";

export default function ConsultaPedidoPage() {
  const router = useRouter();
  const [id, setId] = useState("");
  const [error, setError] = useState<string | null>(null);

  function consultar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const limpio = id.trim();
    if (!esIdPedidoValido(limpio)) {
      setError("Ingresa el número completo de tu pedido: 36 caracteres con guiones.");
      return;
    }
    setError(null);
    router.push(`/pedidos/${limpio.toLowerCase()}`);
  }

  return (
    <ShellPagina>
      <div className="mx-auto max-w-2xl">
        <h1 className="text-4xl font-black leading-none tracking-tight text-[#6B1020] sm:text-5xl">
          Consulta tu pedido
        </h1>
        <p className="mt-3 font-semibold text-[#6B1020]/70">
          Ingresa el número que recibiste al confirmar tu compra para ver el estado de tu pedido.
        </p>

        <form
          onSubmit={consultar}
          noValidate
          aria-label="Consulta de pedido"
          className="mt-8 space-y-4 rounded-[25px] border-2 border-[#6B1020] bg-white p-6 shadow-xl sm:p-8"
        >
          <div>
            <label htmlFor="pedido-id" className="mb-1.5 block text-sm font-black text-[#6B1020]">
              Número de pedido
            </label>
            <input
              id="pedido-id"
              value={id}
              onChange={(ev) => setId(ev.target.value)}
              placeholder="3f2a9c1e-7b4d-4e0a-9c55-2d1f8a6b7e90"
              autoComplete="off"
              spellCheck={false}
              aria-invalid={Boolean(error)}
              aria-describedby={error ? "pedido-id-error" : undefined}
              className={`h-12 w-full rounded-[18px] border-2 bg-white px-4 text-[#6B1020] outline-none transition-all duration-200 placeholder:text-[#6B1020]/50 focus:ring-4 focus:ring-[#6B1020]/20 ${
                error ? "border-[#B42335]" : "border-[#6B1020]"
              }`}
            />
            {error && (
              <p id="pedido-id-error" role="alert" className="mt-1.5 text-sm font-bold text-[#B42335]">
                {error}
              </p>
            )}
          </div>
          <button
            type="submit"
            className="h-14 w-full rounded-[52px] border-2 border-[#6B1020] bg-[#6B1020] text-lg font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#8B1E2D] active:scale-95"
          >
            Consultar pedido
          </button>
        </form>
      </div>
    </ShellPagina>
  );
}
