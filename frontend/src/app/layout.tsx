import CookieBanner from "@/components/CookieBanner";
import AvisoGlobal from "@/components/AvisoGlobal";
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { CarritoProvider } from "@/context/CarritoContext";
import CarritoDrawer from "@/components/CarritoDrawer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "La Economía Aya | Supermercado & Distribuciones",
  description: "Supermercado y distribuciones en Neiva, Huila. Busca productos con IA y elige tu sede.",
  icons: { icon: "/logo.png" },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
<CarritoProvider>{children}<CarritoDrawer />
</CarritoProvider>
<CookieBanner />
        <AvisoGlobal />
      </body>
    </html>
  );
}



