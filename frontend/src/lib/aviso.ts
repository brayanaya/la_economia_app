export const EVENTO_AVISO = "la-economia:aviso";

export function mostrarAviso(mensaje: string): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<string>(EVENTO_AVISO, { detail: mensaje }));
}
