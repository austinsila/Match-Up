// Display constants for the landing page only. Later pages should read
// prices from /api/pricing or the checkout summary (backend is the source of truth).
export const PRICING = {
  courts: 16,
  slotMinutes: 30,
  courtSlot: 90,
  proMonthly: 299,
  proDiscountPct: 10,
  freeAdvanceDays: 3,
  proAdvanceDays: 30,
};

export const PRO_COURT_SLOT = PRICING.courtSlot * (1 - PRICING.proDiscountPct / 100);

// Sports on the platform. Badminton is the launch sport; the others are
// "Coming soon" until prices are decided. PRICING above is badminton pricing.
export const SPORTS = [
  { id: "badminton", label: "Badminton", available: true },
  { id: "football", label: "Football", available: false },
  { id: "basketball", label: "Basketball", available: false },
];

export const DEFAULT_SPORT = SPORTS.find((s) => s.available).id;
