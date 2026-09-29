// Decorative top-down badminton court (doubles) drawn as line art.
export function CourtLines({ className = "" }) {
  return (
    <svg viewBox="0 0 400 600" preserveAspectRatio="xMidYMid slice" className={className} aria-hidden="true">
      <g fill="none" stroke="currentColor" strokeWidth="3">
        <rect x="40" y="40" width="320" height="520" />
        <rect x="65" y="40" width="270" height="520" />
        <path d="M40 300h320" strokeWidth="5" />
        <path d="M40 216h320M40 384h320" />
        <path d="M200 40v176M200 384v176" />
        <path d="M65 76h270M65 524h270" />
      </g>
    </svg>
  );
}
