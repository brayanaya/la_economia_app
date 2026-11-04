"use client";

import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useState, type FormEvent, useEffect } from "react";
import { Eye, EyeOff, ShieldCheck, QrCode, Mail, Smartphone, Download, Trash2, AlertCircle, CheckCircle, Loader2, Settings } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { COP } from "@/lib/formato";
import { SafeImage } from "@/components/SafeImage";

function safeReturnTo(value: string | null) {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\")) return "/";
  try { const url = new URL(value, window.location.origin); return url.origin === window.location.origin ? `${url.pathname}${url.search}${url.hash}` : "/"; }
  catch { return "/"; }
}

// --- Google OAuth helper ---
declare global {
  interface Window {
    google: {
      accounts: {
        id: {
          initialize: (config: { client_id: string; callback: (response: { credential: string }) => void; auto_select?: boolean; cancel_on_tap_outside?: boolean }) => void;
          renderButton: (parent: HTMLElement, options: { theme?: string; size?: string; type?: string; text?: string; shape?: string; logo_alignment?: string; width?: string }) => void;
          prompt: (momentListener?: (notification: { isNotDisplayed: () => boolean; isSkippedMoment: () => boolean }) => void) => void;
          disableAutoSelect: () => void;
        };
      };
    };
  }
}

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

function CuentaPageContent() {
  const router = useRouter(); const params = useSearchParams();
  const { user, loading, login, register, logout, refresh,
    loginWithGoogle, requestMagicLink, verifyMagicLink,
    setupTotp, verifyTotp, disableTotp, checkTotpStatus,
    updateProfile, getConsent, exportData, deleteAccount } = useAuth();

  const [modo, setModo] = useState<"login" | "register" | "magic-link" | "perfil" | "totp">("login");
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [telefono, setTelefono] = useState("");
  const [visible, setVisible] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState("");
  const [totpCode, setTotpCode] = useState("");
  const [totpSetup, setTotpSetup] = useState<{ secret: string; uri: string; qr_code_url: string } | null>(null);
  const [totpEnabled, setTotpEnabled] = useState(false);
  const [consentInfo, setConsentInfo] = useState<{ consentimiento_datos: boolean; consentimiento_marketing: boolean; consentimiento_fecha: string | null } | null>(null);
  const [googleLoaded, setGoogleLoaded] = useState(false);
  const [consentDatos, setConsentDatos] = useState(true);
  const [consentMarketing, setConsentMarketing] = useState(false);

  const destino = safeReturnTo(params.get("returnTo"));

  // Cargar estado de TOTP y consentimientos al entrar
  useEffect(() => {
    if (user && !loading) {
      checkTotpStatus().then(r => setTotpEnabled(r.enabled)).catch(() => {});
      getConsent().then(r => {
        setConsentInfo(r);
        setConsentDatos(r.consentimiento_datos);
        setConsentMarketing(r.consentimiento_marketing);
      }).catch(() => {});
    }
  }, [user, loading]);

  // Cargar script de Google
  useEffect(() => {
    if (GOOGLE_CLIENT_ID && !window.google) {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = () => {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleCallback,
          auto_select: false,
          cancel_on_tap_outside: true,
        });
        setGoogleLoaded(true);
      };
      document.head.appendChild(script);
    }
  }, []);

  if (user && !loading && modo !== "perfil" && modo !== "totp") {
    router.replace(destino);
    return <div className="p-10 text-center text-[#6B1020]">Abriendo tu cuenta…</div>;
  }

  async function handleGoogleCallback(response: { credential: string }) {
    setError(""); setEnviando(true);
    try {
      await loginWithGoogle(response.credential);
      router.replace(destino);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos iniciar sesión con Google. Inténtalo de nuevo.");
    } finally { setEnviando(false); }
  }

  async function enviar(e: FormEvent) {
    e.preventDefault(); setError(""); setExito("");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) { setError("Ingresa un correo electrónico válido."); return; }
    if (modo === "login" && password.length < 1) { setError("Ingresa tu contraseña."); return; }
    if (modo === "register" && password.length < 8) { setError("La contraseña debe tener al menos 8 caracteres."); return; }
    if (modo === "register" && nombre.trim().length < 2) { setError("Escribe tu nombre para crear la cuenta."); return; }
    if (modo === "magic-link" && !email.trim()) { setError("Ingresa tu correo para recibir el enlace mágico."); return; }
    setEnviando(true);
    try {
      if (modo === "login") {
        await login(email.trim(), password, totpCode || undefined);
        router.replace(destino);
      } else if (modo === "register") {
        await register(email.trim(), password, nombre.trim(), telefono.trim() || undefined);
        router.replace(destino);
      } else if (modo === "magic-link") {
        const res = await requestMagicLink(email.trim());
        setExito(res.mensaje + (res.dev_token ? ` (Token dev: ${res.dev_token})` : ""));
        setModo("login");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos completar la acción. Inténtalo de nuevo.");
    } finally { setEnviando(false); }
  }

  async function activarTotp() {
    setError(""); setEnviando(true);
    try {
      const res = await setupTotp();
      setTotpSetup(res);
      setModo("totp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos configurar 2FA. Inténtalo de nuevo.");
    } finally { setEnviando(false); }
  }

  async function verificarTotpSetup() {
    if (!totpCode || totpCode.length !== 6) { setError("Ingresa el código de 6 dígitos de Google Authenticator."); return; }
    setError(""); setEnviando(true);
    try {
      await verifyTotp(totpCode);
      setExito("¡2FA activado correctamente con Google Authenticator!");
      setTotpEnabled(true);
      setTotpSetup(null);
      setTotpCode("");
      setModo("perfil");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido. Inténtalo de nuevo.");
    } finally { setEnviando(false); }
  }

  async function desactivarTotpHandler() {
    if (!totpCode || totpCode.length !== 6) { setError("Ingresa el código actual de 6 dígitos para desactivar 2FA."); return; }
    setError(""); setEnviando(true);
    try {
      await disableTotp(totpCode);
      setExito("2FA desactivado correctamente.");
      setTotpEnabled(false);
      setTotpCode("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Código inválido. Inténtalo de nuevo.");
    } finally { setEnviando(false); }
  }

  async function guardarPerfil() {
    setError(""); setExito(""); setEnviando(true);
    try {
      await updateProfile({
        nombre: nombre.trim() || undefined,
        telefono: telefono.trim() || undefined,
        consentimiento_datos: consentDatos,
        consentimiento_marketing: consentMarketing,
      });
      setExito("Perfil actualizado correctamente.");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos guardar los cambios.");
    } finally { setEnviando(false); }
  }

  async function exportarMisDatos() {
    setError(""); setEnviando(true);
    try {
      const data = await exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mis-datos-la-economia-aya-${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setExito("Datos exportados correctamente.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos exportar tus datos.");
    } finally { setEnviando(false); }
  }

  async function eliminarMiCuenta() {
    if (!confirm("¿ESTÁS SEGURO? Esto eliminará tu cuenta y todos tus datos permanentemente (Ley 1581 - Derecho de supresión).")) return;
    setError(""); setEnviando(true);
    try {
      await deleteAccount();
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos eliminar la cuenta.");
    } finally { setEnviando(false); }
  }

  const input = "h-12 w-full rounded-xl border border-[#6B1020]/20 bg-white px-4 text-[#3D1017] outline-none focus:border-[#8B1E2D] focus:ring-4 focus:ring-[#6B1020]/10";
  const btnPrimario = "w-full rounded-full bg-[#6B1020] px-5 py-3.5 font-bold text-white transition hover:bg-[#8B1E2D] disabled:cursor-wait disabled:opacity-60";
  const btnSecundario = "w-full rounded-full border-2 border-[#6B1020]/15 bg-white px-4 py-3 font-semibold text-[#3D1017] transition hover:bg-[#F5EEE8]";

  if (loading) return <div className="min-h-screen bg-[#F5EEE8] flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#6B1020]" /></div>;

  return <main className="flex min-h-screen items-center justify-center bg-[#F5EEE8] px-4 py-12 text-[#3D1017]">
    <section className="w-full max-w-md overflow-hidden rounded-[28px] border border-[#6B1020]/10 bg-white shadow-[0_24px_80px_rgba(75,8,18,.14)]">
      <div className="bg-gradient-to-br from-[#8B1E2D] to-[#4A1018] px-8 py-8 text-white">
        <button type="button" onClick={() => { if (modo !== "login" && modo !== "register") { setModo("login"); setError(""); setExito(""); } else if (window.history.length > 1) router.back(); else router.replace("/"); }} className="text-sm font-bold text-white/75 transition hover:text-white">← Volver</button>
        <p className="mt-7 text-xs font-bold uppercase tracking-[.2em] text-amber-300">La Economía Aya</p>
        <h1 className="mt-2 text-3xl font-black">
          {modo === "login" ? "Qué bueno verte" :
           modo === "register" ? "Crea tu cuenta" :
           modo === "magic-link" ? "Enlace mágico" :
           modo === "totp" ? "Google Authenticator" :
           "Mi cuenta"}
        </h1>
        <p className="mt-2 text-sm text-white/75">
          {modo === "login" ? "Ingresa para continuar con tu compra." :
           modo === "register" ? "Regístrate y compra con confianza." :
           modo === "magic-link" ? "Recibe un enlace en tu correo para entrar sin contraseña." :
           modo === "totp" ? "Escanea el código QR con Google Authenticator." :
           "Gestiona tu perfil, seguridad y privacidad."}
        </p>
      </div>

      <div className="p-7 sm:p-8">
        {modo === "login" || modo === "register" ? (
          <>
            <div className="mb-6 grid grid-cols-2 rounded-xl bg-[#F5EEE8] p-1" role="tablist" aria-label="Acceso a cuenta">
              {(["login", "register"] as const).map((tab) => <button key={tab} type="button" role="tab" aria-selected={modo === tab} onClick={() => { setModo(tab); setError(""); setExito(""); }} className={`rounded-lg py-2.5 text-sm font-bold transition ${modo === tab ? "bg-white text-[#6B1020] shadow-sm" : "text-[#6B1020]/60"}`}>{tab === "login" ? "Iniciar sesión" : "Crear cuenta"}</button>)}
            </div>

            <form onSubmit={enviar} className="space-y-4" noValidate>
              {modo === "register" && (
                <div>
                  <label htmlFor="nombre" className="mb-1.5 block text-sm font-bold">Nombre</label>
                  <input id="nombre" className={input} autoComplete="name" value={nombre} onChange={e => setNombre(e.target.value)} required />
                </div>
              )}
              <div>
                <label htmlFor="email" className="mb-1.5 block text-sm font-bold">Correo electrónico</label>
                <input id="email" className={input} type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required />
              </div>
              <div>
                <label htmlFor="password" className="mb-1.5 block text-sm font-bold">Contraseña</label>
                <div className="relative">
                  <input id="password" className={`${input} pr-12`} type={visible ? "text" : "password"} autoComplete={modo === "login" ? "current-password" : "new-password"} value={password} onChange={e => setPassword(e.target.value)} minLength={8} required />
                  <button type="button" onClick={() => setVisible(v => !v)} aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"} className="absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-[#6B1020]/70 hover:text-[#6B1020]">{visible ? <EyeOff size={19} /> : <Eye size={19} />}</button>
                </div>
              </div>
              {modo === "register" && (
                <div>
                  <label htmlFor="telefono" className="mb-1.5 block text-sm font-bold">Teléfono (opcional)</label>
                  <input id="telefono" className={input} type="tel" autoComplete="tel" value={telefono} onChange={e => setTelefono(e.target.value)} placeholder="310 123 4567" />
                </div>
              )}

              {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm font-medium text-red-800">{error}</p>}
              {exito && <p role="status" className="rounded-xl border border-green-200 bg-green-50 px-3 py-2.5 text-sm font-medium text-green-800">{exito}</p>}

              <button type="submit" disabled={enviando || loading} className={btnPrimario}>{enviando ? "Un momento…" : modo === "login" ? "Iniciar sesión" : "Crear cuenta"}</button>
            </form>

            <p className="mt-5 flex items-start gap-2 text-xs leading-5 text-[#6B1020]/65"><ShieldCheck size={16} className="mt-0.5 shrink-0" aria-hidden="true" />Tu sesión se mantiene protegida. Nunca guardamos tu contraseña en este dispositivo.</p>

            <div className="mt-5 border-t border-[#6B1020]/10 pt-5 space-y-3">
              {GOOGLE_CLIENT_ID && googleLoaded && (
                <div id="google-btn" className="flex w-full items-center justify-center gap-3 rounded-xl border border-[#6B1020]/15 bg-white px-4 py-3 font-semibold text-[#3D1017] transition hover:bg-[#F5EEE8]" role="button" tabIndex={0} onClick={() => window.google?.accounts.id.prompt()} onKeyDown={e => e.key === "Enter" && window.google?.accounts.id.prompt()}>
                  <span aria-hidden="true" className="text-lg font-black">G</span>Continuar con Google
                </div>
              )}

              <button type="button" onClick={() => { setModo("magic-link"); setError(""); setExito(""); }} className="flex w-full items-center justify-center gap-3 rounded-xl border border-[#6B1020]/15 bg-white px-4 py-3 font-semibold text-[#3D1017] transition hover:bg-[#F5EEE8]">
                <Mail size={19} className="shrink-0" aria-hidden="true" />Enlace mágico (sin contraseña)
              </button>

              <p className="text-center text-xs leading-5 text-[#6B1020]/55">Al continuar, aceptas nuestros <Link href="/terminos" className="underline underline-offset-2">Términos</Link> y <Link href="/privacidad" className="underline underline-offset-2">Política de privacidad</Link> (Ley 1581).</p>
            </div>
          </>
        ) : modo === "magic-link" ? (
          <form onSubmit={enviar} className="space-y-4" noValidate>
            <div>
              <label htmlFor="email-magic" className="mb-1.5 block text-sm font-bold">Correo electrónico</label>
              <input id="email-magic" className={input} type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="tu@correo.com" />
            </div>
            {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm font-medium text-red-800">{error}</p>}
            {exito && <p role="status" className="rounded-xl border border-green-200 bg-green-50 px-3 py-2.5 text-sm font-medium text-green-800">{exito}</p>}
            <button type="submit" disabled={enviando || loading} className={btnPrimario}>{enviando ? "Enviando…" : "Enviar enlace mágico"}</button>
            <button type="button" onClick={() => { setModo("login"); setError(""); setExito(""); }} className={btnSecundario}>Volver a iniciar sesión</button>
          </form>
        ) : modo === "totp" ? (
          totpSetup ? (
            <div className="space-y-4">
              <p className="text-sm text-[#6B1020]/70 text-center">Escanea este código QR con <strong>Google Authenticator</strong> (o Authy, Microsoft Authenticator, etc.)</p>
              <div className="flex justify-center">
                <SafeImage
                  src={totpSetup.qr_code_url}
                  alt="Código QR para Google Authenticator"
                  width={192}
                  height={192}
                  className="w-48 h-48 rounded-xl border border-[#F3E6D9] bg-white p-2"
                  fallbackType="general"
                />
              </div>
              <div className="rounded-xl bg-[#F5EEE8] p-4 text-xs text-center text-[#6B1020]/70">
                <p className="font-bold mb-1">Tu clave secreta (guárdala segura):</p>
                <code className="font-mono tracking-wider">{totpSetup.secret}</code>
              </div>
              <div>
                <label htmlFor="totp-code" className="mb-1.5 block text-sm font-bold">Código de 6 dígitos</label>
                <input id="totp-code" className={input} type="text" inputMode="numeric" maxLength={6} value={totpCode} onChange={e => setTotpCode(e.target.value)} placeholder="123456" autoComplete="one-time-code" required />
              </div>
              {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm font-medium text-red-800">{error}</p>}
              <button type="button" onClick={verificarTotpSetup} disabled={enviando || !totpCode} className={btnPrimario}>{enviando ? "Verificando…" : "Activar 2FA"}</button>
              <button type="button" onClick={() => { setModo("perfil"); setTotpSetup(null); setError(""); }} className={btnSecundario}>Cancelar</button>
            </div>
          ) : (
            <div className="text-center py-8">
              <QrCode className="w-16 h-16 mx-auto text-[#6B1020]/30" />
              <h3 className="mt-4 text-lg font-black text-[#6B1020]">{totpEnabled ? "2FA Activado" : "Activar verificación en 2 pasos"}</h3>
              <p className="mt-2 text-sm text-[#6B1020]/60">Añade una capa extra de seguridad con Google Authenticator.</p>
              {totpEnabled ? (
                <>
                  <p className="mt-3 text-sm text-green-600 font-medium">✓ Tu cuenta está protegida con 2FA</p>
                  <div className="mt-4">
                    <label htmlFor="totp-disable" className="mb-1.5 block text-sm font-bold">Código actual para desactivar</label>
                    <input id="totp-disable" className={input} type="text" inputMode="numeric" maxLength={6} value={totpCode} onChange={e => setTotpCode(e.target.value)} placeholder="123456" autoComplete="one-time-code" />
                  </div>
                  {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm font-medium text-red-800">{error}</p>}
                  <button type="button" onClick={desactivarTotpHandler} disabled={enviando || !totpCode} className="mt-3 w-full rounded-full border-2 border-red-300 bg-white px-5 py-3.5 font-bold text-red-600 transition hover:bg-red-50">{enviando ? "Desactivando…" : "Desactivar 2FA"}</button>
                </>
              ) : (
                <button type="button" onClick={activarTotp} disabled={enviando} className="mt-4 w-full rounded-full bg-[#6B1020] px-5 py-3.5 font-bold text-white transition hover:bg-[#8B1E2D] disabled:cursor-wait disabled:opacity-60">{enviando ? "Configurando…" : "Configurar Google Authenticator"}</button>
              )}
              <button type="button" onClick={() => { setModo("perfil"); setError(""); setTotpSetup(null); }} className="mt-4 w-full rounded-full border-2 border-[#6B1020]/15 bg-white px-4 py-3 font-semibold text-[#3D1017] transition hover:bg-[#F5EEE8]">Volver a mi cuenta</button>
            </div>
          )
        ) : (
          // MODO PERFIL
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-black text-[#6B1020]">Mi perfil</h2>
            </div>

            <div className="rounded-xl border border-[#6B1020]/10 bg-[#F5EEE8] p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#6B1020]/10 text-[#6B1020] text-2xl font-black">{user?.nombre?.[0]?.toUpperCase()}</div>
                <div>
                  <p className="font-black text-[#3D1017]">{user?.nombre}</p>
                  <p className="text-sm text-[#6B1020]/60">{user?.email}</p>
                  {user?.google_linked && <span className="mt-1 inline-flex items-center gap-1 text-xs text-green-600 font-medium"><span className="text-lg">G</span>Cuenta vinculada con Google</span>}
                </div>
              </div>
            </div>

            <form onSubmit={e => { e.preventDefault(); guardarPerfil(); }} className="space-y-4">
              <div>
                <label htmlFor="nombre-perfil" className="mb-1.5 block text-sm font-bold">Nombre</label>
                <input id="nombre-perfil" className={input} value={nombre || user?.nombre || ""} onChange={e => setNombre(e.target.value)} />
              </div>
              <div>
                <label htmlFor="telefono-perfil" className="mb-1.5 block text-sm font-bold">Teléfono</label>
                <input id="telefono-perfil" className={input} type="tel" value={telefono || user?.telefono || ""} onChange={e => setTelefono(e.target.value)} placeholder="310 123 4567" />
              </div>

              <fieldset className="rounded-xl border border-[#6B1020]/10 bg-white p-4">
                <legend className="text-sm font-bold text-[#6B1020]">Privacidad y consentimientos (Ley 1581)</legend>
                <div className="mt-3 space-y-3">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input type="checkbox" checked={consentDatos} onChange={e => setConsentDatos(e.target.checked)} className="mt-1 h-4 w-4 accent-[#6B1020] border-2 border-[#6B1020]/30" required />
                    <div>
                      <p className="font-medium text-[#3D1017]">Tratamiento de datos personales (obligatorio)</p>
                      <p className="text-xs text-[#6B1020]/60">Autorizo a La Economía Aya para usar mis datos para gestionar pedidos, entregas y atención al cliente.</p>
                    </div>
                  </label>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input type="checkbox" checked={consentMarketing} onChange={e => setConsentMarketing(e.target.checked)} className="mt-1 h-4 w-4 accent-[#6B1020] border-2 border-[#6B1020]/30" />
                    <div>
                      <p className="font-medium text-[#3D1017]">Comunicaciones comerciales (opcional)</p>
                      <p className="text-xs text-[#6B1020]/60">Recibir ofertas, novedades y promociones por correo o WhatsApp.</p>
                    </div>
                  </label>
                </div>
                {consentInfo?.consentimiento_fecha && <p className="mt-2 text-xs text-[#6B1020]/50">Última actualización: {new Date(consentInfo.consentimiento_fecha).toLocaleDateString("es-CO")}</p>}
              </fieldset>

              {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm font-medium text-red-800">{error}</p>}
              {exito && <p role="status" className="rounded-xl border border-green-200 bg-green-50 px-3 py-2.5 text-sm font-medium text-green-800">{exito}</p>}

              <button type="submit" disabled={enviando} className={btnPrimario}>{enviando ? "Guardando…" : "Guardar cambios"}</button>
            </form>

            <div className="border-t border-[#6B1020]/10 pt-5 space-y-3">
              <h3 className="text-sm font-bold text-[#6B1020] flex items-center gap-2"><Settings size={18} /> Seguridad</h3>

              <button type="button" onClick={() => setModo("totp")} className="flex w-full items-center justify-between gap-3 rounded-xl border border-[#6B1020]/15 bg-white px-4 py-3 font-semibold text-[#3D1017] transition hover:bg-[#F5EEE8]">
                <div className="flex items-center gap-3"><ShieldCheck size={19} aria-hidden="true" /><span>Verificación en 2 pasos (Google Authenticator)</span></div>
                <span className={`text-sm font-medium ${totpEnabled ? "text-green-600" : "text-[#6B1020]/50"}`}>{totpEnabled ? "Activado ✓" : "Desactivado"}</span>
              </button>

              <button type="button" onClick={() => router.push("/cuenta?cambiar=password")} className="flex w-full items-center justify-between gap-3 rounded-xl border border-[#6B1020]/15 bg-white px-4 py-3 font-semibold text-[#3D1017] transition hover:bg-[#F5EEE8]">
                <div className="flex items-center gap-3"><ShieldCheck size={19} aria-hidden="true" /><span>Cambiar contraseña</span></div>
              </button>
            </div>

            <div className="border-t border-[#6B1020]/10 pt-5 space-y-3">
              <h3 className="text-sm font-bold text-[#6B1020] flex items-center gap-2"><Download size={18} /> Mis datos</h3>
              <button type="button" onClick={exportarMisDatos} disabled={enviando} className="flex w-full items-center justify-between gap-3 rounded-xl border border-[#6B1020]/15 bg-white px-4 py-3 font-semibold text-[#3D1017] transition hover:bg-[#F5EEE8] disabled:opacity-50">
                <div className="flex items-center gap-3"><Download size={19} aria-hidden="true" /><span>Exportar mis datos (JSON)</span></div>
              </button>
              <p className="text-xs text-[#6B1020]/50">Descarga una copia de tu perfil, pedidos y consentimientos (Derecho de acceso - Ley 1581).</p>
            </div>

            <div className="border-t border-red-200 pt-5 space-y-3">
              <h3 className="text-sm font-bold text-red-600 flex items-center gap-2"><Trash2 size={18} /> Zona de peligro</h3>
              <button type="button" onClick={eliminarMiCuenta} disabled={enviando} className="flex w-full items-center justify-between gap-3 rounded-xl border-2 border-red-200 bg-red-50 px-4 py-3 font-semibold text-red-600 transition hover:bg-red-100 disabled:opacity-50">
                <div className="flex items-center gap-3"><Trash2 size={19} aria-hidden="true" /><span>Eliminar mi cuenta permanentemente</span></div>
              </button>
              <p className="text-xs text-red-500">Esta acción no se puede deshacer. Se suprimirán todos tus datos según Ley 1581 (Derecho de supresión).</p>
            </div>

            <div className="border-t border-[#6B1020]/10 pt-5">
              <button type="button" onClick={logout} className={btnSecundario}>Cerrar sesión</button>
            </div>
          </div>
        )}

        <p className="mt-5 text-center text-xs leading-5 text-[#6B1020]/55">¿Necesitas ayuda? Escríbenos a <a href="mailto:soporte@laeconomiaaya.com" className="underline underline-offset-2">soporte@laeconomiaaya.com</a></p>
      </div>
    </section>
  </main>;
}

export default function CuentaPage() {
  return <Suspense fallback={<div className="min-h-screen bg-[#F5EEE8] flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-[#6B1020]" /></div>}><CuentaPageContent /></Suspense>;
}