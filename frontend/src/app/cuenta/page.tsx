"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState, type FormEvent } from "react";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

function safeReturnTo(value: string | null) {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return "/";
  try { const url = new URL(value, window.location.origin); return url.origin === window.location.origin ? `${url.pathname}${url.search}${url.hash}` : "/"; }
  catch { return "/"; }
}
function CuentaForm() {
  const router = useRouter(); const params = useSearchParams(); const { user, loading, login, register } = useAuth();
  const [modo, setModo] = useState<"login" | "register">("login");
  const [nombre, setNombre] = useState(""); const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false); const [enviando, setEnviando] = useState(false); const [error, setError] = useState("");
  const destino = safeReturnTo(params.get("returnTo"));
  if (user && !loading) { router.replace(destino); return <div className="p-10 text-center text-[#6B1020]">Abriendo tu cuenta…</div>; }
  async function enviar(e: FormEvent) {
    e.preventDefault(); setError("");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) { setError("Ingresa un correo electrónico válido."); return; }
    if (password.length < 8) { setError("La contraseña debe tener al menos 8 caracteres."); return; }
    if (modo === "register" && nombre.trim().length < 2) { setError("Escribe tu nombre para crear la cuenta."); return; }
    setEnviando(true);
    try { if (modo === "login") await login(email.trim(), password); else await register(email.trim(), password, nombre.trim()); router.replace(destino); }
    catch (err) { setError(err instanceof Error ? err.message : "No pudimos iniciar sesión. Inténtalo de nuevo."); }
    finally { setEnviando(false); }
  }
  const input = "h-12 w-full rounded-xl border border-[#6B1020]/20 bg-white px-4 text-[#3D1017] outline-none focus:border-[#8B1E2D] focus:ring-4 focus:ring-[#6B1020]/10";
  return <main className="flex min-h-screen items-center justify-center bg-[#F5EEE8] px-4 py-12 text-[#3D1017]">
    <section className="w-full max-w-md overflow-hidden rounded-[28px] border border-[#6B1020]/10 bg-white shadow-[0_24px_80px_rgba(75,8,18,.14)]">
      <div className="bg-gradient-to-br from-[#8B1E2D] to-[#4A1018] px-8 py-8 text-white"><button type="button" onClick={() => { if (window.history.length > 1) router.back(); else router.replace("/"); }} className="text-sm font-bold text-white/75 transition hover:text-white">← Volver a la página anterior</button><p className="mt-7 text-xs font-bold uppercase tracking-[.2em] text-amber-300">La Economía Aya</p><h1 className="mt-2 text-3xl font-black">{modo === "login" ? "Qué bueno verte" : "Crea tu cuenta"}</h1><p className="mt-2 text-sm text-white/75">{modo === "login" ? "Ingresa para continuar con tu compra." : "Regístrate y compra con confianza."}</p></div>
      <div className="p-7 sm:p-8">
        <div className="mb-6 grid grid-cols-2 rounded-xl bg-[#F5EEE8] p-1" role="tablist" aria-label="Acceso a cuenta">
          {(["login", "register"] as const).map((tab) => <button key={tab} type="button" role="tab" aria-selected={modo === tab} onClick={() => { setModo(tab); setError(""); }} className={`rounded-lg py-2.5 text-sm font-bold transition ${modo === tab ? "bg-white text-[#6B1020] shadow-sm" : "text-[#6B1020]/60"}`}>{tab === "login" ? "Iniciar sesión" : "Crear cuenta"}</button>)}
        </div>
        <form onSubmit={enviar} className="space-y-4" noValidate>
          {modo === "register" && <div><label htmlFor="nombre" className="mb-1.5 block text-sm font-bold">Nombre</label><input id="nombre" className={input} autoComplete="name" value={nombre} onChange={e => setNombre(e.target.value)} required /></div>}
          <div><label htmlFor="email" className="mb-1.5 block text-sm font-bold">Correo electrónico</label><input id="email" className={input} type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required /></div>
          <div><label htmlFor="password" className="mb-1.5 block text-sm font-bold">Contraseña</label><div className="relative"><input id="password" className={`${input} pr-12`} type={visible ? "text" : "password"} autoComplete={modo === "login" ? "current-password" : "new-password"} value={password} onChange={e => setPassword(e.target.value)} minLength={8} required /><button type="button" onClick={() => setVisible(v => !v)} aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"} className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-[#6B1020]/70 hover:text-[#6B1020]">{visible ? <EyeOff size={19} /> : <Eye size={19} />}</button></div></div>
          {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm font-medium text-red-800">{error}</p>}
          <button type="submit" disabled={enviando || loading} className="w-full rounded-full bg-[#6B1020] px-5 py-3.5 font-bold text-white transition hover:bg-[#8B1E2D] disabled:cursor-wait disabled:opacity-60">{enviando ? "Un momento…" : modo === "login" ? "Iniciar sesión" : "Crear cuenta"}</button>
        </form>
        <p className="mt-5 flex items-start gap-2 text-xs leading-5 text-[#6B1020]/65"><ShieldCheck size={16} className="mt-0.5 shrink-0" aria-hidden="true" />Tu sesión se mantiene protegida. Nunca guardamos tu contraseña en este dispositivo.</p>
        <div className="mt-5 border-t border-[#6B1020]/10 pt-5">
          <button type="button" disabled title="El acceso con Google requiere configurar las credenciales OAuth del comercio." className="flex w-full cursor-not-allowed items-center justify-center gap-3 rounded-xl border border-[#6B1020]/15 bg-white px-4 py-3 font-semibold text-[#3D1017]/55 opacity-75">
            <span aria-hidden="true" className="text-lg font-black">G</span>Continuar con Google · Próximamente
          </button>
          <p className="mt-2 text-center text-xs leading-5 text-[#6B1020]/55">El inicio de sesión con Google aparecerá cuando se configure la cuenta OAuth del comercio.</p>
        </div>
      </div>
    </section>
  </main>;
}
export default function CuentaPage() { return <Suspense fallback={<div className="min-h-screen bg-[#F5EEE8]" />}><CuentaForm /></Suspense>; }
