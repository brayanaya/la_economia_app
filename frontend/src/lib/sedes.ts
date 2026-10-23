import { SEDES } from "@/lib/api";

/** Nombre legible de una sede: el que trae el item, o el del catálogo de sedes. */
export function nombreSede(sedeId: string, preferido?: string): string {
  return preferido ?? SEDES.find((s) => s.id === sedeId)?.nombre ?? "Sede";
}
