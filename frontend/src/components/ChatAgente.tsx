'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader2 } from 'lucide-react';
import { enviarMensajeAgente, ProductoRecuperado } from '@/lib/api';

interface Mensaje {
  autor: 'usuario' | 'agente';
  texto: string;
  productos?: ProductoRecuperado[];
}

function formatearCOP(valor: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(valor);
}

export default function ChatAgente() {
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState<Mensaje[]>([
    { autor: 'agente', texto: 'Hola! Soy el asistente de La Economia. En que puedo ayudarte hoy?' },
  ]);
  const [texto, setTexto] = useState('');
  const [consultando, setConsultando] = useState(false);
  const finRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes, abierto]);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    const mensajeUsuario = texto.trim();
    if (!mensajeUsuario) return;

    setMensajes((prev) => [...prev, { autor: 'usuario', texto: mensajeUsuario }]);
    setTexto('');
    setConsultando(true);

    try {
      const data = await enviarMensajeAgente({ mensaje: mensajeUsuario });
      setMensajes((prev) => [
        ...prev,
        {
          autor: 'agente',
          texto: data.respuesta,
          productos: data.hubo_resultados_relevantes ? data.productos_recomendados : undefined,
        },
      ]);
    } catch (err) {
      setMensajes((prev) => [
        ...prev,
        { autor: 'agente', texto: 'Hubo un problema consultando el catalogo. Intenta de nuevo en un momento.' },
      ]);
      console.error(err);
    } finally {
      setConsultando(false);
    }
  }

  return (
    <>
      <button
        onClick={() => setAbierto((v) => !v)}
        aria-label={abierto ? 'Cerrar chat' : 'Abrir chat del asistente'}
        className='fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-brand-red hover:bg-brand-red-dark text-white shadow-lg flex items-center justify-center transition-transform hover:scale-105'
      >
        {abierto ? <X size={22} /> : <MessageCircle size={22} />}
      </button>

      {abierto && (
        <div className='fixed bottom-24 right-6 z-40 w-[340px] max-w-[90vw] h-[480px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden'>
          <div className='bg-brand-dark text-white px-4 py-3 flex items-center gap-2'>
            <MessageCircle size={18} className='text-brand-yellow' />
            <div>
              <p className='font-semibold text-sm leading-none'>Asistente La Economia</p>
              <p className='text-[11px] text-gray-300 mt-1'>Recomendaciones generadas por IA</p>
            </div>
          </div>

          <div className='flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3 bg-brand-bg'>
            {mensajes.map((m, i) => (
              <div key={i} className={m.autor === 'usuario' ? 'self-end max-w-[85%]' : 'self-start max-w-[90%]'}>
                <div
                  className={
                    m.autor === 'usuario'
                      ? 'bg-brand-red text-white text-sm px-3 py-2 rounded-2xl rounded-br-sm'
                      : 'bg-white border border-gray-200 text-brand-dark text-sm px-3 py-2 rounded-2xl rounded-bl-sm'
                  }
                >
                  {m.texto}
                </div>

                {m.productos && m.productos.length > 0 && (
                  <div className='mt-2 flex flex-col gap-1.5'>
                    {m.productos.map((p) => (
                      <div key={p.producto_id} className='bg-white border border-gray-200 rounded-lg px-3 py-2 flex justify-between items-center'>
                        <span className='text-xs text-brand-dark'>{p.nombre}</span>
                        <span className='text-xs font-bold text-brand-red'>{formatearCOP(p.precio)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {consultando && (
              <div className='self-start flex items-center gap-2 text-xs text-gray-500 px-1'>
                <Loader2 className='animate-spin' size={14} />
                Consultando inventario...
              </div>
            )}
            <div ref={finRef} />
          </div>

          <form onSubmit={enviar} className='border-t border-gray-200 p-3 flex gap-2'>
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder='Escribe tu mensaje...'
              aria-label='Escribe tu mensaje'
              className='flex-1 border border-gray-200 rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-red'
            />
            <button
              type='submit'
              aria-label='Enviar mensaje'
              disabled={consultando}
              className='w-9 h-9 rounded-full bg-brand-yellow hover:bg-brand-yellow-dark flex items-center justify-center disabled:opacity-60'
            >
              <Send size={15} className='text-brand-dark' />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
