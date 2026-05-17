"use client";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="rounded-md border border-danger/40 bg-danger/10 p-6">
      <h1 className="text-lg font-semibold text-danger">Something went wrong</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">{error.message || "The app could not load this view. Confirm the backend is running and try again."}</p>
      <button onClick={reset} className="mt-4 bg-panelSoft px-4 py-2 text-sm text-ink hover:bg-border">Try again</button>
    </div>
  );
}
