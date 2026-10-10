import type { Metadata } from "next";
import LegalShell, { Pendiente } from "@/components/LegalShell";

export const metadata: Metadata = {
  title: "Términos y Condiciones | La Economía Aya",
};

export default function TerminosPage() {
  return (
    <LegalShell titulo="Términos y Condiciones de Uso" ultimaActualizacion="octubre de 2026">
      <section>
        <h2>1. Aceptación</h2>
        <p>
          El acceso y uso de la plataforma web de La Economía Aya implica la aceptación de estos términos y de la
          Política de Tratamiento de Datos Personales. Si no está de acuerdo, absténgase de usar el sitio.
        </p>
      </section>

      <section>
        <h2>2. Identificación del vendedor</h2>
        <ul>
          <li>Razón social: La Economía Aya</li>
          <li>NIT: <Pendiente>número de NIT</Pendiente></li>
          <li>Domicilio: Neiva, Huila, Colombia</li>
          <li>Contacto: <Pendiente>correo y teléfono de atención al cliente</Pendiente></li>
        </ul>
      </section>

      <section>
        <h2>3. Productos, precios y disponibilidad</h2>
        <p>
          Los productos, precios y existencias se muestran por sede y pueden variar sin previo aviso. La
          disponibilidad se confirma al procesar la orden; si un producto se agota, se informará al cliente y se
          ofrecerán alternativas o la anulación de ese ítem. Los precios se expresan en pesos colombianos (COP) e
          incluyen los impuestos aplicables, salvo indicación contraria.
        </p>
      </section>

      <section>
        <h2>4. Carrito y órdenes de compra</h2>
        <p>
          Para agregar productos al carrito es necesario seleccionar una sede. Si el carrito contiene productos de
          varias sedes, se genera una orden por cada sede. La orden se entiende formalizada cuando el sistema
          confirma su registro. El cliente es responsable de verificar los productos, las cantidades y los datos
          suministrados antes de confirmar.
        </p>
      </section>

      <section>
        <h2>5. Pagos y entregas</h2>
        <p>
          Medios de pago: <Pendiente>medios de pago habilitados</Pendiente>. Modalidades de entrega y costos:{" "}
          <Pendiente>domicilio y/o recogida en sede, tarifas y tiempos</Pendiente>.
        </p>
      </section>

      <section>
        <h2>6. Derecho de retracto, cambios y garantías</h2>
        <p>
          En compras realizadas a distancia, el consumidor puede ejercer el derecho de retracto dentro de los
          cinco (5) días hábiles siguientes a la entrega, conforme a la Ley 1480 de 2011 (Estatuto del Consumidor),
          salvo las excepciones legales. Los productos con garantía legal se rigen por la misma norma.{" "}
          <Pendiente>procedimiento y condiciones para devoluciones, productos perecederos incluidos</Pendiente>.
        </p>
      </section>

      <section>
        <h2>7. Asistente de compras con inteligencia artificial</h2>
        <p>
          La plataforma ofrece un asistente que recomienda productos a partir de las consultas del usuario. Sus
          respuestas son orientativas y pueden contener imprecisiones; el precio y la disponibilidad válidos son
          los mostrados en el catálogo al momento de la compra.
        </p>
      </section>

      <section>
        <h2>8. Uso adecuado</h2>
        <ul>
          <li>No usar la plataforma con fines ilícitos o fraudulentos.</li>
          <li>No intentar acceder sin autorización a sistemas, cuentas o datos de terceros.</li>
          <li>No alterar, copiar o extraer masivamente el contenido del sitio sin autorización.</li>
        </ul>
      </section>

      <section>
        <h2>9. Propiedad intelectual</h2>
        <p>
          Las marcas, logotipos, diseños y contenidos de la plataforma son de La Economía Aya o de sus
          licenciantes y están protegidos por la normativa de propiedad intelectual aplicable.
        </p>
      </section>

      <section>
        <h2>10. Limitación de responsabilidad</h2>
        <p>
          La Economía Aya no será responsable por interrupciones del servicio ajenas a su control, por el uso
          indebido de la plataforma ni por daños indirectos, en la medida permitida por la ley y sin perjuicio de
          los derechos irrenunciables del consumidor.
        </p>
      </section>

      <section>
        <h2>11. Protección de datos</h2>
        <p>
          El tratamiento de datos personales se rige por la{" "}
          <a href="/privacidad" className="font-medium text-brand-red underline underline-offset-2">
            Política de Tratamiento de Datos Personales
          </a>
          , expedida conforme a la Ley 1581 de 2012.
        </p>
      </section>

      <section>
        <h2>12. Modificaciones, ley aplicable y reclamaciones</h2>
        <p>
          Estos términos pueden modificarse; la versión vigente será la publicada en el sitio. Se rigen por las
          leyes de la República de Colombia. Los consumidores pueden presentar quejas ante la Superintendencia de
          Industria y Comercio (SIC). Jurisdicción competente: Neiva, Huila.
        </p>
      </section>
    </LegalShell>
  );
}
