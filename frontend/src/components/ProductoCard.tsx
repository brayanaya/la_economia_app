type Props = {
  nombre: string;
  precio: number;
  imagen?: string;
  sede: string;
  stock: number;
  /** Similitud pgvector, 0 a 1. Solo en resultados RAG. */
  similitud?: number;
  onAgregar?: () => void;
};

const cop = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

export default function ProductoCard({ nombre, precio, imagen, sede, stock, similitud, onAgregar }: Props) {
  const disponible = stock > 0;

  return (
    <article className="relative flex flex-col rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:shadow-md">
      {similitud !== undefined && (
        <span className="absolute left-3 top-3 z-10 rounded-full bg-brand-yellow px-2 py-1 text-[11px] font-bold text-brand-dark">
          🎯 {Math.round(similitud * 100)}% coincidencia
        </span>
      )}

      <div className="mb-3 flex h-40 items-center justify-center overflow-hidden rounded-lg bg-brand-bg">
        {imagen ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={imagen} alt={nombre} className="h-full w-full object-contain" />
        ) : (
          <span className="text-4xl">🛒</span>
        )}
      </div>

      <h3 className="line-clamp-2 min-h-10 text-sm font-semibold text-brand-dark">{nombre}</h3>
      <p className="mt-2 text-xl font-extrabold text-brand-red">{cop.format(precio)}</p>

      <p className={`mt-1 text-xs font-medium ${disponible ? "text-brand-green" : "text-brand-red"}`}>
        {disponible ? `● ${stock} disponibles en ${sede}` : `● Agotado en ${sede}`}
      </p>

      <button
        onClick={onAgregar}
        disabled={!disponible}
        className="mt-3 w-full rounded-lg bg-brand-green py-2 text-sm font-bold text-white transition hover:bg-brand-green-dark disabled:cursor-not-allowed disabled:bg-gray-300"
      >
        Agregar al carrito
      </button>
    </article>
  );
}