export default function ProductoSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="flex animate-pulse flex-col rounded-2xl border border-black/5 bg-white p-4 shadow-sm"
    >
      <div className="mb-3 h-40 rounded-xl bg-gray-200/70" />
      <div className="h-4 w-4/5 rounded bg-gray-200/70" />
      <div className="mt-2 h-4 w-3/5 rounded bg-gray-200/70" />
      <div className="mt-4 h-6 w-2/5 rounded bg-gray-200/70" />
      <div className="mt-2 h-3 w-1/2 rounded bg-gray-200/70" />
      <div className="mt-4 h-9 w-full rounded-xl bg-gray-200/70" />
    </div>
  );
}
