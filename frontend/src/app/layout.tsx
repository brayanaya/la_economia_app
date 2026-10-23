import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { CarritoProvider } from "@/context/CarritoContext";
import { AuthProvider } from "@/context/AuthContext";
import CarritoDrawer from "@/components/CarritoDrawer";
import CookieBanner from "@/components/CookieBanner";
import AvisoGlobal from "@/components/AvisoGlobal";

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
  description: "Tu mercado a un clic en Neiva, Huila.",
  icons: { icon: "/logo.png" },
};

export default function RootLayout({ children }: { children: import("react").ReactNode }) {
  return (
    <html lang="es" className={`${geistSans.variable} ${geistMono.variable} h-full scroll-smooth antialiased`}>
      <body className="min-h-full flex flex-col">
        <AuthProvider>
          <CarritoProvider>
            {children}
            <CarritoDrawer />
          </CarritoProvider>
        </AuthProvider>
        <CookieBanner />
        <AvisoGlobal />
      </body>
    </html>
  );
}

