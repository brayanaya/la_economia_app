import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Tu pedido | La Economía Aya",
  robots: { index: false, follow: false },
};

export default function PedidosLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
