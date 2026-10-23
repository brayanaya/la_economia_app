export default function ProductoSkeleton() {
  return (
    <div
      aria-hidden="true"
      className="flex animate-pulse flex-col rounded-[25px] border-2 border-[#6B1020]/20 bg-white p-4"
    >
      <div className="mb-3 h-40 rounded-[18px] bg-[#F3E6D9]/70" />
      <div className="h-4 w-4/5 rounded-full bg-[#F3E6D9]" />
      <div className="mt-2 h-4 w-3/5 rounded-full bg-[#F3E6D9]" />
      <div className="mt-4 h-6 w-2/5 rounded-full bg-[#F3E6D9]" />
      <div className="mt-2 h-3 w-1/2 rounded-full bg-[#F3E6D9]" />
      <div className="mt-4 h-10 w-full rounded-[52px] bg-[#F3E6D9]" />
    </div>
  );
}
