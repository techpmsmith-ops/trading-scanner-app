export default function Loading() {
  return (
    <div className="space-y-4">
      <div className="h-8 w-64 animate-pulse rounded-md bg-panelSoft" />
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <div key={item} className="h-24 animate-pulse rounded-md border border-border bg-panel" />
        ))}
      </div>
      <div className="h-80 animate-pulse rounded-md border border-border bg-panel" />
    </div>
  );
}
