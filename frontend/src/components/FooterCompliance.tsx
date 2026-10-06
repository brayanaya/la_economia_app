export default function FooterCompliance() {
  return (
    <footer className='bg-brand-dark text-gray-300 px-6 py-8 mt-12'>
      <div className='max-w-6xl mx-auto flex flex-col gap-4 text-xs'>
        <div className='flex flex-col sm:flex-row justify-between gap-4'>
          <div>
            <p className='text-white font-semibold text-sm mb-1'>Supermercado La Economia Aya</p>
            <p>NIT 900.XXX.XXX-X - Neiva, Huila, Colombia</p>
            <p>Sedes: Santa Isabel y Machines</p>
          </div>
          <div className='flex gap-6'>
            <a href='/terminos' className='hover:text-brand-yellow'>Terminos y condiciones</a>
            <a href='/politica-datos' className='hover:text-brand-yellow'>Tratamiento de datos personales</a>
          </div>
        </div>

        <div className='border-t border-gray-700 pt-4'>
          <p>
            Las recomendaciones de productos mostradas por el asistente virtual son generadas mediante
            inteligencia artificial a partir del catalogo disponible y pueden contener imprecisiones.
            Verifica siempre precio y disponibilidad antes de confirmar tu pedido.
          </p>
          <p className='mt-2'>
            El tratamiento de tus datos personales se realiza conforme a la Ley 1581 de 2012 (Habeas Data)
            de Colombia. Para conocer tus derechos y como ejercerlos, consulta nuestra politica de tratamiento de datos.
          </p>
        </div>

        <p className='text-gray-500'>&copy; {new Date().getFullYear()} La Economia Aya. Todos los derechos reservados.</p>
      </div>
    </footer>
  );
}
