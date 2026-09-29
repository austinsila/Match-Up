import Link from "next/link";

// Court-line mark: a top-down half court with the net line and centre line.
export function LogoMark({ className = "h-8 w-8" }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="hsl(var(--primary))" />
      <g fill="none" stroke="hsl(var(--primary-foreground))" strokeWidth="1.6" strokeLinecap="round">
        <rect x="7" y="7" width="18" height="18" rx="1" />
        <path d="M7 16h18M16 16v9" />
      </g>
      <circle cx="21.5" cy="10.5" r="2.6" fill="hsl(var(--accent))" />
    </svg>
  );
}

export function Logo({ className = "" }) {
  return (
    <Link
      href="/"
      className={`inline-flex items-center gap-2 rounded-md font-extrabold tracking-tight focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${className}`}
    >
      <LogoMark />
      <span className="text-lg">Match Up</span>
    </Link>
  );
}
