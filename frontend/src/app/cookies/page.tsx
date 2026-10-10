import type { Metadata } from "next";
import LegalShell, { Pendiente } from "@/components/LegalShell";

export const metadata: Metadata = {
  title: "Política de Cookies | La Economía Aya",
};

export default function CookiesPage() {
  return (
    <LegalShell titulo="Política de Cookies" ultimaActualizacion="octubre de 2026">
      <section>
        <h2>1. Qué usamos</h2>
        <p>
          Esta plataforma usa cookies y almacenamiento local del navegador (localStorage) para su funcionamiento.
          El tratamiento de los datos personales asociados se rige por la Política de Tratamiento de Datos
          Personales, expedida conforme a la Ley 1581 de 2012.
        </p>
      </section>

      <section>
        <h2>2. Almacenamiento necesario</h2>
        <ul>
          <li>Carrito de compras: guarda en tu navegador los productos que agregas para que no se pierdan al recargar.</li>
          <li>Preferencias de cookies: guarda la decisión que tomaste en el aviso de cookies.</li>
        </ul>
        <p>Este almacenamiento es indispensable para el servicio y no se desactiva desde el aviso de cookies.</p>
      </section>

      <section>
        <h2>3. Almacenamiento opcional</h2>
        <p>
          Analíticas y mejora del servicio: solo se activan si las aceptas.{" "}
          <Pendiente>confirmar qué herramientas de analítica se usarán, si alguna, y qué datos recolectan</Pendiente>.
        </p>
      </section>

      <section>
        <h2>4. Cómo cambiar tu decisión</h2>
        <p>
          Puedes modificar tus preferencias en cualquier momento con el enlace &quot;Configurar cookies&quot; del pie
          de página, o borrando los datos del sitio desde la configuración de tu navegador. Si borras el
          almacenamiento local, se perderá el contenido de tu carrito.
        </p>
      </section>
    </LegalShell>
  );
}
