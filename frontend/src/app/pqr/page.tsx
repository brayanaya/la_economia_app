import type { Metadata } from "next";
import LegalShell, { Pendiente } from "@/components/LegalShell";

export const metadata: Metadata = {
  title: "Canal de Atención PQR | La Economía Aya",
};

export default function PqrPage() {
  return (
    <LegalShell titulo="Canal de Atención PQR" ultimaActualizacion="octubre de 2026">
      <section>
        <h2>1. Qué es una PQR</h2>
        <p>
          Una PQR es una petición, queja o reclamo. Puedes usar este canal para consultar información, expresar
          inconformidad con un producto o servicio, o reclamar por una compra, una garantía o el tratamiento de tus
          datos personales.
        </p>
      </section>

      <section>
        <h2>2. Cómo radicar tu solicitud</h2>
        <ul>
          <li>Correo electrónico: <Pendiente>correo de atención PQR</Pendiente></li>
          <li>Teléfono / WhatsApp: <Pendiente>línea de atención</Pendiente></li>
          <li>Presencial: <Pendiente>dirección y horario de atención en cada sede</Pendiente></li>
        </ul>
        <p>
          Indica tu nombre, un medio de contacto, el número o la fecha de tu pedido (si aplica) y una descripción
          clara de tu solicitud.
        </p>
      </section>

      <section>
        <h2>3. Tiempos de respuesta</h2>
        <p>
          Responderemos dentro de los plazos legales aplicables.{" "}
          <Pendiente>confirmar con asesoría jurídica el plazo de respuesta para peticiones, quejas y reclamos</Pendiente>.
          Las consultas y reclamos sobre datos personales siguen los plazos indicados en la Política de
          Tratamiento de Datos Personales (Ley 1581 de 2012).
        </p>
      </section>

      <section>
        <h2>4. Si no estás conforme con la respuesta</h2>
        <p>
          Como consumidor puedes acudir a la Superintendencia de Industria y Comercio (SIC), autoridad de
          protección al consumidor y de protección de datos personales.
        </p>
      </section>
    </LegalShell>
  );
}
