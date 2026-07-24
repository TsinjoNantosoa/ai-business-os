/**
 * Lightweight page loader — CSS spinner only (keeps lucide out of the landing entry chunk).
 */
export function PageLoader() {
  return (
    <div
      className="flex min-h-[40vh] items-center justify-center"
      role="status"
      aria-label="Chargement"
    >
      <span
        className="inline-block h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"
        aria-hidden
      />
    </div>
  );
}
