'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader2, Bot } from 'lucide-react';
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
        { autor: 'agente', texto: 'No pude conectarme al catalogo. Verifica que la API este corriendo.' },
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
        aria-label={abierto ? 'Cerrar asistente' : 'Abrir asistente de IA'}
        className='fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-brand-red hover:bg-brand-red-dark text-white shadow-xl flex items-center justify-center transition-transform hover:scale-105 border-2 border-brand-yellow'
      >
        {abierto ? <X size={24} /> : <Bot size={26} />}
      </button>

      {abierto && (
        <div className='fixed bottom-24 right-6 z-40 w-[360px] max-w-[92vw] h-[520px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden'>
          <div className='bg-brand-dark text-white px-4 py-3.5 flex items-center justify-between border-b-2 border-brand-yellow'>
            <div className='flex items-center gap-2.5'>
              <div className='w-8 h-8 rounded-lg bg-brand-red flex items-center justify-center text-white'>
                <Bot size={18} />
              </div>
              <div>
                <p className='font-bold text-sm leading-none text-white'>Asistente La Economia</p>
                <p className='text-[10px] text-brand-yellow font-semibold mt-0.5'>RAG + Ollama local</p>
              </div>
            </div>
          </div>

          <div className='flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3 bg-slate-50'>
            {mensajes.map((m, i) => (
              <div key={i} className={m.autor === 'usuario' ? 'self-end max-w-[85%]' : 'self-start max-w-[90%]'}>
                <div
                  className={
                    m.autor === 'usuario'
                      ? 'bg-brand-red text-white text-xs font-medium px-3.5 py-2.5 rounded-2xl rounded-br-none shadow-sm'
                      : 'bg-white border border-gray-200 text-gray-800 text-xs px-3.5 py-2.5 rounded-2xl rounded-bl-none shadow-sm'
                  }
                >
                  {m.texto}
                </div>

                {m.productos && m.productos.length > 0 && (
                  <div className='mt-2 flex flex-col gap-1.5'>
                    {m.productos.map((p) => (
                      <div key={p.producto_id} className='bg-white border border-gray-200 rounded-xl p-2.5 flex justify-between items-center shadow-xs'>
                        <div>
                          <p className='text-xs font-bold text-gray-900'>{p.nombre}</p>
                          <span className='text-[10px] text-gray-500'>{p.categoria_nombre || 'Abarrotes'}</span>
                        </div>
                        <span className='text-xs font-extrabold text-brand-red ml-2'>{formatearCOP(p.precio)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {consultando && (
              <div className='self-start flex items-center gap-2 text-xs text-gray-500 bg-white border border-gray-200 px-3 py-2 rounded-xl shadow-xs'>
                <Loader2 className='animate-spin text-brand-red' size={14} />
                <span>Consultando inventario...</span>
              </div>
            )}
            <div ref={finRef} />
          </div>

          <form onSubmit={enviar} className='border-t border-gray-200 p-3 bg-white flex gap-2'>
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder='Pregunta por un producto...'
              aria-label='Escribe tu mensaje'
              className='flex-1 border border-gray-300 rounded-xl px-3.5 py-2 text-xs text-gray-900 bg-gray-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-red'
            />
            <button
              type='submit'
              aria-label='Enviar mensaje'
              disabled={consultando}
              className='w-9 h-9 rounded-xl bg-brand-yellow hover:bg-brand-yellow-dark text-brand-dark flex items-center justify-center disabled:opacity-50 font-bold shadow-xs'
            >
              <Send size={15} />
            </button>
          </form>
        </div>
      )}
    </>
  );
}
