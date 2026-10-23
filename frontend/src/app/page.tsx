"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import BuscadorSemantico from "@/components/BuscadorSemantico";
import ProductoCard from "@/components/ProductoCard";
import ProductoSkeleton from "@/components/ProductoSkeleton";
import ChatAgente from "@/components/ChatAgente";
import FooterCompliance from "@/components/FooterCompliance";
import { SEDES, buscarProductos, buscarSemantica, type Producto } from "@/lib/api";
import { useCarrito } from "@/context/CarritoContext";
import { ArrowUpRight, Compass, MapPin, Phone, Search, Store } from "lucide-react";
import SplashScreen from "@/components/SplashScreen";

const CONSULTA_INICIAL = "productos de la canasta familiar";
const CATEGORIAS = [
  { nombre: "Ofertas", consulta: "ofertas y promociones supermercado" },
  { nombre: "Cárnicos", consulta: "carnes pollo res cerdo cárnicos" },
  { nombre: "Granos", consulta: "granos arroz fríjoles lentejas" },
  { nombre: "Aseo", consulta: "productos de aseo hogar limpieza" },
  { nombre: "Aceites", consulta: "aceites de cocina" },
  { nombre: "Droguería", consulta: "productos de droguería cuidado personal" },
  { nombre: "Licor", consulta: "licores bebidas alcohólicas" },
  { nombre: "Fruver", consulta: "frutas verduras hortalizas tubérculos" },
  { nombre: "Lácteos", consulta: "leche queso yogur lácteos" },
  { nombre: "Bebidas", consulta: "bebidas jugos gaseosas agua" },
  { nombre: "Despensa", consulta: "productos de despensa enlatados salsas" },
  { nombre: "Panadería", consulta: "panadería panes galletas" },
  { nombre: "Congelados", consulta: "productos congelados" },
];

const BENEFICIOS = [
  { icono: <Store className="h-6 w-6" aria-hidden="true" />, titulo: "Dos sedes en Neiva", detalle: "Santa Isabel y Palmas, con catálogo seleccionado por ubicación." },
  { icono: <Search className="h-6 w-6" aria-hidden="true" />, titulo: "Búsqueda sencilla", detalle: "Encuentra productos por nombre o cuéntanos qué necesitas." },
  { icono: <Phone className="h-6 w-6" aria-hidden="true" />, titulo: "Atención cercana", detalle: "Comunícate directamente con nuestro equipo en Neiva." },
];

const UBICACIONES = [
  { nombre: "Santa Isabel", desde: "2019", direccion: "Calle 10 Sur 21-92", busqueda: "Calle 10 Sur 21-92, Santa Isabel, Neiva, Huila, Colombia" },
  { nombre: "Palmas", desde: "2021", direccion: "Cra. 52 #26A-13", busqueda: "Carrera 52 #26A-13, Neiva, Huila, Colombia" },
];

const SEDE_SANTA_ISABEL = SEDES.find((s) => s.nombre === "Santa Isabel")!;
const SEDE_PALMAS = SEDES.find((s) => s.nombre === "Palmas")!;

function normalizarTexto(texto: string) {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function esConsultaFruver(texto: string) {
  return /\b(fruver|frutas?|verduras?|hortalizas|vegetales|tuberculos|aguacate|bananos?|platanos?|tomates?|cebollas?|papas?|yuca|zanahoria|lechuga|cilantro|limon|manzana|papaya|mango)\b/.test(normalizarTexto(texto));
}

function esProductoFruver(producto: Producto) {
  return esConsultaFruver(`${producto.categoria ?? ""} ${producto.nombre}`);
}

function EstadoVacio({
  titulo,
  detalle,
  accion,
}: {
  titulo: string;
  detalle: string;
  accion?: { texto: string; onClick: () => void };
}) {
  return (
    <div className="flex flex-col items-center rounded-[25px] border-2 border-[#6B1020] bg-white px-6 py-14 text-center">
      <svg viewBox="0 0 120 120" className="mb-4 h-28 w-28" aria-hidden="true">
        <circle cx="60" cy="60" r="56" fill="#F3E6D9" />
        <path
          d="M30 48h60l-7 36a6 6 0 0 1-6 5H43a6 6 0 0 1-6-5l-7-36Z"
          fill="#FFFFFF"
          stroke="#6B1020"
          strokeWidth="3"
          strokeLinejoin="round"
        />
        <path d="M44 48l10-16M76 48L66 32" fill="none" stroke="#6B1020" strokeWidth="3" strokeLinecap="round" />
        <circle cx="52" cy="67" r="3" fill="#6B1020" />
        <circle cx="68" cy="67" r="3" fill="#6B1020" />
        <path d="M53 79q7-6 14 0" fill="none" stroke="#C8102E" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <h2 className="text-2xl font-black leading-none tracking-tight text-[#6B1020]">{titulo}</h2>
      <p className="mt-2 max-w-sm text-sm font-medium text-[#6B1020]/80">{detalle}</p>
      {accion && (
        <button
          type="button"
          onClick={accion.onClick}
          className="mt-5 rounded-[52px] border-2 border-[#6B1020] bg-[#6B1020] px-6 py-2.5 text-sm font-black text-white transition-all duration-200 hover:-translate-y-0.5 hover:bg-[#8B1E2D] active:scale-95"
        >
          {accion.texto}
        </button>
      )}
    </div>
  );
}

export default function Home() {
  const { agregar, abrir, totalItems: carrito, items: itemsCarrito, reasignarTodos } = useCarrito();
  const [sede, setSede] = useState(SEDE_SANTA_ISABEL);
  const [categoriaActiva, setCategoriaActiva] = useState<string | null>(null);
  const [consulta, setConsulta] = useState(CONSULTA_INICIAL);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [intento, setIntento] = useState(0);
  const [ubicacionActiva, setUbicacionActiva] = useState(UBICACIONES[0]);

  useEffect(() => {
    let cancelado = false;
    async function cargar() {
      setCargando(true);
      setError(null);
      try {
        const res = consulta === CONSULTA_INICIAL || categoriaActiva !== null
          ? await buscarSemantica(consulta, sede.id, 8)
          : await buscarProductos(consulta, sede.id);
        if (!cancelado) setProductos(res);
      } catch {
        if (!cancelado) {
          setProductos([]);
          setError("No pudimos conectar con el catálogo. Verifica que la API esté corriendo.");
        }
      } finally {
        if (!cancelado) setCargando(false);
      }
    }
    cargar();
    return () => {
      cancelado = true;
    };
  }, [consulta, sede.id, categoriaActiva, intento]);

  function buscarCatalogo(texto: string, categoria: string | null = null) {
    const siguienteConsulta = texto.trim() || CONSULTA_INICIAL;
    const contieneFruver = esConsultaFruver(siguienteConsulta);
    const carritoTieneFruver = itemsCarrito.some((item) => esConsultaFruver(`${item.categoria ?? ""} ${item.nombre}`));
    const destino = contieneFruver || carritoTieneFruver ? SEDE_PALMAS : SEDE_SANTA_ISABEL;
    setSede(destino);
    setCategoriaActiva(categoria);
    if (itemsCarrito.length > 0 && destino.id) reasignarTodos(destino.id, destino.nombre);
    setConsulta(siguienteConsulta);
  }

  function agregarProducto(p: Producto): boolean {
    const productoFruver = esProductoFruver(p) || categoriaActiva === "Fruver";
    const carritoTieneFruver = itemsCarrito.some((item) => esConsultaFruver(`${item.categoria ?? ""} ${item.nombre}`));
    const destino = productoFruver || carritoTieneFruver ? SEDE_PALMAS : SEDE_SANTA_ISABEL;
    if (!destino.id) return false;

    if (productoFruver || carritoTieneFruver) reasignarTodos(destino.id, destino.nombre);
    setSede(destino);
    agregar({
      productoId: String(p.id),
      nombre: p.nombre,
      precio: p.precio,
      sedeId: destino.id,
      sedeNombre: destino.nombre,
      imagen: p.imagen,
      categoria: p.categoria ?? (productoFruver ? "Fruver" : undefined),
    });
    return true;
  }

  function manejarRecomendacionChat(p: Producto) {
    const carritoTieneFruver = itemsCarrito.some((item) => esConsultaFruver(`${item.categoria ?? ""} ${item.nombre}`));
    if (esProductoFruver(p) || carritoTieneFruver) {
      setSede(SEDE_PALMAS);
      if (SEDE_PALMAS.id) reasignarTodos(SEDE_PALMAS.id, SEDE_PALMAS.nombre);
    }
  }

  const esInicial = consulta === CONSULTA_INICIAL;

  return (
    <div className="min-h-screen bg-slate-50">
      <SplashScreen />
      <Navbar
        cartCount={carrito}
        onCartClick={abrir}
      />

      <section id="inicio" className="scroll-mt-24 relative isolate min-h-[calc(100vh-5rem)] overflow-hidden bg-[linear-gradient(180deg,#B20D1D_0%,#830815_46%,#180307_100%)] pt-24 text-white sm:pt-20">
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(255,199,44,0.14),transparent_38%)]" />
        <div className="relative mx-auto max-w-3xl px-5 pb-16 pt-12 sm:px-8 sm:pb-24 sm:pt-16 lg:pb-28">
          <p className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-white/85 shadow-sm backdrop-blur-md sm:text-sm">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" aria-hidden="true" />
            Neiva, Huila · Catálogo unificado
          </p>
          <h1 className="max-w-[660px] text-5xl font-bold leading-[1.04] tracking-[-0.045em] text-white sm:text-6xl lg:text-7xl">
            Tu mercado<br />de <span className="text-amber-400">confianza</span>
          </h1>
          <p className="mt-6 max-w-2xl text-base font-medium leading-7 text-white/75 sm:text-lg sm:leading-8">
            Busca por nombre, marca o varios términos; el asistente de compras está disponible para recomendaciones y recetas.
          </p>
          <div className="mt-8 max-w-3xl">
            <BuscadorSemantico cargando={cargando} onBuscar={buscarCatalogo} />
          </div>
          <div className="mt-10 flex flex-wrap gap-x-7 gap-y-3 text-sm font-medium text-white/75">
            <span className="inline-flex items-center gap-2"><Store className="h-4 w-4 text-amber-400" aria-hidden="true" /> Dos sedes en Neiva</span>
            <span className="inline-flex items-center gap-2"><Search className="h-4 w-4 text-amber-400" aria-hidden="true" /> Búsqueda por producto y marca</span>
            <span className="inline-flex items-center gap-2"><Phone className="h-4 w-4 text-amber-400" aria-hidden="true" /> Atención telefónica directa</span>
          </div>
        </div>
      </section>

      <section id="catalogo" className="scroll-mt-28 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12">
          <h2 className="text-3xl font-black leading-none tracking-tight text-[#6B1020] sm:text-4xl">
            {esInicial ? "Catálogo" : categoriaActiva ?? `Resultados para "${consulta}"`}
          </h2>
          <div className="mb-8 mt-5 -mx-1 overflow-x-auto px-1 pb-2">
            <nav aria-label="Categorías del catálogo" className="flex min-w-max gap-2">
              {CATEGORIAS.map((categoria) => (
                <button
                  key={categoria.nombre}
                  type="button"
                  onClick={() => buscarCatalogo(categoria.consulta, categoria.nombre)}
                  aria-pressed={categoriaActiva === categoria.nombre}
                  className={`whitespace-nowrap rounded-full px-4 py-2.5 text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 ${categoriaActiva === categoria.nombre ? "bg-[#4A1018] text-white" : "bg-[#FAF8F6] text-[#4A1018] ring-1 ring-black/10 hover:bg-red-50"}`}
                >
                  {categoria.nombre}
                </button>
              ))}
            </nav>
          </div>

          {error && (
            <EstadoVacio
              titulo="No pudimos cargar el catálogo"
              detalle={error}
              accion={{ texto: "Reintentar", onClick: () => setIntento((n) => n + 1) }}
            />
          )}

          {!error && cargando && (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
              {Array.from({ length: 8 }, (_, i) => (
                <ProductoSkeleton key={i} />
              ))}
            </div>
          )}

          {!cargando && !error && productos.length === 0 && (
            <EstadoVacio
              titulo="No encontramos productos"
              detalle="Prueba con otras palabras, por ejemplo el tipo de producto o para qué lo necesitas."
              accion={esInicial ? undefined : { texto: "Ver catálogo", onClick: () => setConsulta(CONSULTA_INICIAL) }}
            />
          )}

          {!cargando && !error && productos.length > 0 && (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
              {productos.map((p, i) => (
                <ProductoCard
                  key={`${p.id}-${i}`}
                  nombre={p.nombre}
                  precio={p.precio}
                  stock={p.stock}
                  imagen={p.imagen}
                  similitud={esInicial ? undefined : p.similitud}
                  onAgregar={() => agregarProducto(p)}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      <section id="quienes-somos" className="scroll-mt-28 bg-[#FAF8F6]">
        <div className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:py-28">
          <div className="grid gap-12 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.22em] text-red-700">Nuestra historia · Neiva</p>
              <h2 className="mt-4 max-w-lg text-4xl font-bold leading-tight tracking-tight text-[#351016] sm:text-5xl">
                Crecemos junto a los hogares de nuestra ciudad.
              </h2>
              <p className="mt-6 max-w-xl text-base leading-7 text-slate-600">
                La Economía Aya es un supermercado y distribuidora de Neiva. Nuestra historia se cuenta a través de las sedes y de las familias que nos eligen para hacer su mercado.
              </p>
              <a href="#ubicanos" className="mt-7 inline-flex items-center gap-2 rounded-full bg-[#8E1020] px-5 py-3 text-sm font-semibold text-white transition-all duration-300 ease-in-out hover:-translate-y-1 hover:bg-[#740B18]">
                Conoce nuestras sedes <ArrowUpRight className="h-4 w-4" aria-hidden="true" />
              </a>
            </div>

            <div className="space-y-8">
              <div className="rounded-3xl bg-white p-6 shadow-[0_12px_40px_rgba(52,16,22,0.07)] ring-1 ring-black/[0.04] sm:p-8">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-red-700">Dos momentos de nuestra historia</p>
                <div className="mt-6 grid gap-6 sm:grid-cols-2">
                  {UBICACIONES.map((ubicacion) => (
                    <div key={ubicacion.nombre} className="relative rounded-2xl bg-[#FAF8F6] p-5">
                      <span className="text-3xl font-bold tracking-tight text-[#8E1020]">{ubicacion.desde}</span>
                      <h3 className="mt-2 text-lg font-bold text-[#351016]">Sede {ubicacion.nombre}</h3>
                      <p className="mt-1 text-sm leading-6 text-slate-600">Desde {ubicacion.desde}, creciendo con Neiva.</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <article className="rounded-3xl bg-[#4A1018] p-6 text-white sm:p-7">
                  <span className="text-xs font-bold uppercase tracking-[0.2em] text-amber-300">Nuestra misión</span>
                  <p className="mt-4 text-lg font-medium leading-7">Acercar a las familias de Neiva los productos que necesitan para su hogar, con variedad, atención cercana y una compra sencilla.</p>
                </article>
                <article className="rounded-3xl bg-white p-6 shadow-[0_12px_40px_rgba(52,16,22,0.07)] ring-1 ring-black/[0.04] sm:p-7">
                  <span className="text-xs font-bold uppercase tracking-[0.2em] text-red-700">Nuestra visión</span>
                  <p className="mt-4 text-lg font-medium leading-7 text-[#351016]">Ser el supermercado de confianza de más hogares en Neiva, creciendo con nuestras comunidades sin perder la cercanía que nos distingue.</p>
                </article>
              </div>
            </div>
          </div>

          <div className="mt-14 grid gap-4 sm:grid-cols-3">
            {BENEFICIOS.map((b) => (
              <article key={b.titulo} className="rounded-2xl bg-white p-6 shadow-[0_12px_40px_rgba(52,16,22,0.05)] ring-1 ring-black/[0.04] transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-[0_16px_45px_rgba(52,16,22,0.1)]">
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-red-50 text-red-800">{b.icono}</span>
                <h3 className="mt-5 text-base font-bold text-[#351016]">{b.titulo}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600">{b.detalle}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="ubicanos" className="scroll-mt-28 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:py-28">
          <div className="mb-10 max-w-2xl">
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-red-700">Estamos para ayudarte</p>
            <h2 className="mt-4 text-4xl font-bold tracking-tight text-[#351016] sm:text-5xl">Ubícanos en Neiva</h2>
            <p className="mt-4 text-base leading-7 text-slate-600">Consulta la dirección de cada sede y abre la ruta en Google Maps para llegar.</p>
          </div>
          <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
            <div className="space-y-4">
              {UBICACIONES.map((ubicacion) => (
                <button
                  key={ubicacion.nombre}
                  type="button"
                  onClick={() => setUbicacionActiva(ubicacion)}
                  aria-pressed={ubicacionActiva.nombre === ubicacion.nombre}
                  className={`group flex w-full items-center justify-between rounded-2xl p-5 text-left ring-1 transition-all duration-300 ease-in-out hover:-translate-y-1 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] ${ubicacionActiva.nombre === ubicacion.nombre ? "bg-[#4A1018] text-white ring-[#4A1018]" : "bg-[#FAF8F6] text-[#351016] ring-black/[0.04]"}`}
                >
                  <span className="flex items-center gap-4">
                    <span className={`flex h-12 w-12 items-center justify-center rounded-full shadow-sm ${ubicacionActiva.nombre === ubicacion.nombre ? "bg-white/10 text-amber-300" : "bg-white text-red-800"}`}><MapPin className="h-5 w-5" aria-hidden="true" /></span>
                    <span><span className={`block text-xs font-medium ${ubicacionActiva.nombre === ubicacion.nombre ? "text-white/65" : "text-slate-500"}`}>Desde {ubicacion.desde}</span><span className="mt-1 block text-lg font-bold">Sede {ubicacion.nombre}</span><span className={`mt-1 block text-sm ${ubicacionActiva.nombre === ubicacion.nombre ? "text-white/75" : "text-slate-600"}`}>{ubicacion.direccion}, Neiva</span></span>
                  </span>
                  <ArrowUpRight className={`h-5 w-5 transition-transform duration-300 group-hover:-translate-y-1 group-hover:translate-x-1 ${ubicacionActiva.nombre === ubicacion.nombre ? "text-amber-300" : "text-red-700"}`} aria-hidden="true" />
                </button>
              ))}
              <div className="rounded-2xl bg-[#FAF8F6] p-5 ring-1 ring-black/[0.04]">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Líneas de atención</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {["315 340 0962", "322 693 7375"].map((telefono) => (
                    <a key={telefono} href={`tel:+57${telefono.replaceAll(" ", "")}`} className="inline-flex items-center gap-2 rounded-full bg-white px-4 py-2.5 text-sm font-bold text-[#351016] shadow-sm transition-all duration-300 ease-in-out hover:-translate-y-1 hover:text-red-700">
                      <Phone className="h-4 w-4 text-red-700" aria-hidden="true" />{telefono}
                    </a>
                  ))}
                </div>
              </div>
            </div>

            <div className="overflow-hidden rounded-3xl bg-slate-100 shadow-[0_16px_50px_rgba(52,16,22,0.12)] ring-1 ring-black/[0.06]">
              <div className="flex flex-wrap items-center justify-between gap-3 bg-white px-5 py-4 sm:px-6">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Mapa de sede</p>
                  <h3 className="mt-1 text-lg font-bold text-[#351016]">{ubicacionActiva.nombre} · Neiva</h3>
                </div>
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${ubicacionActiva.direccion}, Neiva, Huila, Colombia`)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-full bg-[#8E1020] px-4 py-2.5 text-sm font-semibold text-white transition-all duration-300 ease-in-out hover:-translate-y-1 hover:bg-[#740B18]"
                >
                  Cómo llegar <Compass className="h-4 w-4" aria-hidden="true" />
                </a>
              </div>
              <iframe
                key={ubicacionActiva.nombre}
                title={`Mapa de la sede ${ubicacionActiva.nombre}, ${ubicacionActiva.direccion}, Neiva`}
                src={`https://maps.google.com/maps?q=${encodeURIComponent(ubicacionActiva.busqueda)}&output=embed`}
                className="h-72 w-full border-0 sm:h-96"
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                allowFullScreen
              />
              <p className="bg-white px-5 py-3 text-xs leading-5 text-slate-500 sm:px-6">El mapa muestra la dirección indicada para esta sede. Confirma el punto en Google Maps antes de desplazarte.</p>
            </div>
          </div>
        </div>
      </section>

      <FooterCompliance />
      <ChatAgente sedeId={sede.id} onAgregar={manejarRecomendacionChat} />
    </div>
  );
}


