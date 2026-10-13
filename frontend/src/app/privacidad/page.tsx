import type { Metadata } from "next";
import LegalShell, { Pendiente } from "@/components/LegalShell";

export const metadata: Metadata = {
  title: "Política de Tratamiento de Datos Personales | La Economía Aya",
};

export default function PrivacidadPage() {
  return (
    <LegalShell titulo="Política de Tratamiento de Datos Personales" ultimaActualizacion="octubre de 2026">
      <section>
        <h2>1. Marco legal</h2>
        <p>
          Esta política se expide en cumplimiento del artículo 15 de la Constitución Política de Colombia, la Ley
          1581 de 2012 (Régimen General de Protección de Datos Personales), el Decreto 1377 de 2013 y las demás
          normas que los modifiquen, reglamenten o complementen (compiladas en el Decreto 1074 de 2015).
        </p>
      </section>

      <section>
        <h2>2. Responsable del tratamiento</h2>
        <ul>
          <li>Razón social: La Economía Aya</li>
          <li>NIT: <Pendiente>número de NIT</Pendiente></li>
          <li>Domicilio: Neiva, Huila, Colombia</li>
          <li>Correo para asuntos de datos personales: <Pendiente>correo de contacto</Pendiente></li>
          <li>Teléfono: <Pendiente>teléfono de contacto</Pendiente></li>
        </ul>
      </section>

      <section>
        <h2>3. Datos personales que se recolectan</h2>
        <ul>
          <li>Datos de identificación y contacto: nombre, teléfono y notas del pedido.</li>
          <li>Datos transaccionales: productos seleccionados, sede, historial y estado de las órdenes.</li>
          <li>Datos de uso: consultas realizadas al asistente de compras y datos técnicos básicos de navegación.</li>
        </ul>
        <p>
          La plataforma no solicita datos sensibles. Si en algún caso se recolectaran, su suministro será
          facultativo y requerirá autorización expresa del titular.
        </p>
      </section>

      <section>
        <h2>4. Finalidades del tratamiento</h2>
        <ul>
          <li>Gestionar las órdenes de compra, la entrega y la atención de solicitudes.</li>
          <li>Mostrar disponibilidad y precios por sede y recomendar productos mediante el asistente de búsqueda.</li>
          <li>Enviar comunicaciones relacionadas con el estado de los pedidos.</li>
          <li>Cumplir obligaciones legales, contables y tributarias.</li>
          <li>Mejorar la experiencia y la seguridad de la plataforma.</li>
          <li><Pendiente>finalidades comerciales o de mercadeo, si aplican</Pendiente></li>
        </ul>
      </section>

      <section>
        <h2>5. Autorización</h2>
        <p>
          El tratamiento de datos personales requiere la autorización previa, expresa e informada del titular, que
          se obtiene al marcar la casilla de autorización al finalizar la compra. El titular puede revocar la
          autorización en cualquier momento, salvo cuando exista un deber legal o contractual de conservar la
          información.
        </p>
      </section>

      <section>
        <h2>6. Derechos del titular</h2>
        <p>De acuerdo con el artículo 8 de la Ley 1581 de 2012, el titular tiene derecho a:</p>
        <ul>
          <li>Conocer, actualizar y rectificar sus datos personales.</li>
          <li>Solicitar prueba de la autorización otorgada.</li>
          <li>Ser informado sobre el uso que se ha dado a sus datos.</li>
          <li>Presentar quejas ante la Superintendencia de Industria y Comercio (SIC) por infracciones a la ley.</li>
          <li>Revocar la autorización y/o solicitar la supresión del dato cuando no se respeten los principios y garantías legales.</li>
          <li>Acceder de forma gratuita a sus datos personales objeto de tratamiento.</li>
        </ul>
      </section>

      <section>
        <h2>7. Procedimiento para consultas y reclamos</h2>
        <p>
          Las consultas se atenderán en un máximo de diez (10) días hábiles contados desde su recibo, prorrogables
          por cinco (5) días hábiles más cuando no sea posible atenderlas en ese término, informando los motivos de
          la demora. Los reclamos de rectificación, actualización o supresión se resolverán en un máximo de quince
          (15) días hábiles, prorrogables por ocho (8) días hábiles más. Las solicitudes deben enviarse a{" "}
          <Pendiente>correo de contacto</Pendiente> indicando nombre completo, documento de identidad, descripción
          de la solicitud y datos de contacto.
        </p>
      </section>

      <section>
        <h2>8. Seguridad y conservación</h2>
        <p>
          Se adoptan medidas técnicas, humanas y administrativas razonables para proteger los datos contra
          pérdida, acceso no autorizado o uso fraudulento. Los datos se conservarán durante el tiempo necesario
          para cumplir las finalidades descritas y las obligaciones legales aplicables.
        </p>
      </section>

      <section>
        <h2>9. Transferencia y transmisión de datos</h2>
        <p>
          Los datos podrán ser transmitidos a encargados que presten servicios de infraestructura, pago o
          logística, bajo obligaciones de confidencialidad y seguridad. <Pendiente>listar proveedores y países de
          destino, si hay transferencias internacionales</Pendiente>.
        </p>
      </section>

      <section>
        <h2>10. Menores de edad</h2>
        <p>
          La plataforma no está dirigida a menores de 18 años y no recolecta intencionalmente sus datos. Si se
          detecta tratamiento de datos de un menor sin autorización de su representante legal, se suprimirán.
        </p>
      </section>

      <section>
        <h2>11. Vigencia y cambios</h2>
        <p>
          Esta política rige desde su publicación. Cualquier modificación sustancial será comunicada a través de
          la plataforma.
        </p>
      </section>
    </LegalShell>
  );
}
