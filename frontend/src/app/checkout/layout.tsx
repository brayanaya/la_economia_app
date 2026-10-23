import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Finalizar compra | La Economía Aya",
};

export default function CheckoutLayout({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
