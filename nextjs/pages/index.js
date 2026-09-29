import Link from "next/link";
import { Check, Minus, PhoneOff, Eye, CopyX } from "lucide-react";

import { Layout } from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PRICING, PRO_COURT_SLOT, SPORTS } from "@/lib/constants";

// Peak-hour preview board (a=available, b=booked, h=held). Static on purpose.
const BOARD = ["bbaabhaa", "aabbbaaa", "abaahhab", "bbbaaaba", "aaabbbaa", "hbaaabbb"];
const CELL = {
  a: "bg-card border border-border",
  b: "bg-primary border border-primary",
  h: "bg-accent border border-accent",
};
const CELL_LABEL = { a: "Available", b: "Booked", h: "Held" };

function CourtBoard() {
  return (
    <div className="rounded-2xl border bg-card p-4 shadow-sm sm:p-5">
      <div className="grid grid-cols-[3.5rem_repeat(8,minmax(0,1fr))] gap-1 text-xs text-muted-foreground">
        <span aria-hidden="true" />
        {["18:00", "19:00", "20:00", "21:00"].map((t) => (
          <span key={t} className="col-span-2 font-medium">
            {t}
          </span>
        ))}
        {BOARD.map((row, i) => (
          <div key={i} className="contents">
            <span className="flex items-center font-medium text-foreground">Court {i + 1}</span>
            {row.split("").map((c, j) => (
              <span
                key={j}
                role="img"
                aria-label={`Court ${i + 1}, slot ${j + 1}: ${CELL_LABEL[c]}`}
                className={`h-8 rounded-sm ${CELL[c]}`}
              />
            ))}
          </div>
        ))}
      </div>
      <dl className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
        {Object.keys(CELL).map((k) => (
          <div key={k} className="flex items-center gap-1.5">
            <span aria-hidden="true" className={`h-3 w-3 rounded-sm ${CELL[k]}`} />
            <dt>{CELL_LABEL[k]}</dt>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-sm font-medium">Badminton, Friday evening, live. Green is gone, orange is being paid for right now.</p>
    </div>
  );
}

const pains = [
  {
    icon: PhoneOff,
    title: "No more phone tag",
    text: "Calling the desk to ask what is free wastes everyone's evening. Here you see it all at once.",
  },
  {
    icon: CopyX,
    title: "No double-booking",
    text: "A slot you pick is held for you for 8 minutes. Nobody else can take it while you pay.",
  },
  {
    icon: Eye,
    title: "See every court",
    text: `Every court, every ${PRICING.slotMinutes} minutes, in one grid before you commit. Badminton launches with ${PRICING.courts} courts.`,
  },
];

const steps = [
  { title: "Pick your slots", text: "Choose a date and tap the courts and times you want." },
  { title: "Hold and pay", text: "Your slots are held for 8 minutes while you check out with PromptPay." },
  { title: "Show up and play", text: "Rent equipment with the booking (badminton rackets and shoes), or bring your own." },
];

const matrix = [
  { label: "Badminton court per 30 minutes", free: `${PRICING.courtSlot} THB`, pro: `${PRO_COURT_SLOT} THB (10% off)` },
  { label: "Book ahead", free: `${PRICING.freeAdvanceDays} days`, pro: `${PRICING.proAdvanceDays} days` },
  { label: "Cancellation", free: "Fee if under 24 hours", pro: "Always free" },
  { label: "Rescheduling", free: false, pro: true },
  { label: "Free racket and shoes each booking", free: false, pro: true },
  { label: "Priority quota at peak hours", free: false, pro: true },
];

function Cell({ value, pro }) {
  if (value === true) {
    return (
      <>
        <Check className="mx-auto h-5 w-5 text-primary" aria-hidden="true" />
        <span className="sr-only">Included</span>
      </>
    );
  }
  if (value === false) {
    return (
      <>
        <Minus className="mx-auto h-5 w-5 text-muted-foreground" aria-hidden="true" />
        <span className="sr-only">Not included</span>
      </>
    );
  }
  return <span className={pro ? "font-semibold" : ""}>{value}</span>;
}

export default function Home() {
  return (
    <Layout>
      <section className="border-b">
        <div className="container grid gap-10 py-12 sm:py-16 lg:grid-cols-[1.05fr_1fr] lg:items-center lg:py-24">
          <div>
            <h1 className="text-4xl font-extrabold leading-[1.05] sm:text-5xl lg:text-6xl">
              Book any court, any sport, without picking up the phone.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-muted-foreground">
              Badminton is open now: see which of the {PRICING.courts} courts are free, hold your slots,
              and pay in under ten minutes. Football and basketball are coming soon. Go Pro for{" "}
              {PRICING.proDiscountPct}% off and a 30-day booking window.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Button asChild variant="accent" size="lg">
                <Link href="/register">Create a free account</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="#pricing">Compare Free and Pro</Link>
              </Button>
            </div>
          </div>
          <CourtBoard />
        </div>
      </section>

      <section id="sports" aria-labelledby="sports-heading" className="container scroll-mt-20 border-b py-12 sm:py-16">
        <h2 id="sports-heading" className="text-3xl font-extrabold sm:text-4xl">Pick your sport</h2>
        <ul className="mt-8 grid gap-4 md:grid-cols-3">
          {SPORTS.map((s) => (
            <li
              key={s.id}
              className={
                s.available
                  ? "rounded-2xl border-2 border-primary bg-card p-5"
                  : "rounded-2xl border border-dashed bg-muted/40 p-5 text-muted-foreground"
              }
            >
              <div className="flex items-center justify-between gap-3">
                <h3 className={`text-xl font-bold ${s.available ? "text-foreground" : ""}`}>{s.label}</h3>
                {s.available ? (
                  <Badge>Available</Badge>
                ) : (
                  <Badge variant="secondary">Coming soon</Badge>
                )}
              </div>
              <p className="mt-2 text-sm">
                {s.available
                  ? `${PRICING.courts} courts, ${PRICING.courtSlot} THB per ${PRICING.slotMinutes} minutes.`
                  : "Prices to be announced."}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className="container py-14 sm:py-20">
        <h2 className="max-w-2xl text-3xl font-extrabold sm:text-4xl">Booking a court should not be a chore.</h2>
        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {pains.map(({ icon: Icon, title, text }) => (
            <div key={title} className="border-t-2 border-primary pt-4">
              <Icon className="h-6 w-6 text-primary" aria-hidden="true" />
              <h3 className="mt-3 text-lg font-bold">{title}</h3>
              <p className="mt-1 text-muted-foreground">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-primary text-primary-foreground">
        <div className="container py-14 sm:py-20">
          <h2 className="text-3xl font-extrabold sm:text-4xl">How it works</h2>
          <ol className="mt-8 grid gap-8 md:grid-cols-3">
            {steps.map((s, i) => (
              <li key={s.title} className="flex gap-4">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent font-bold text-accent-foreground">
                  {i + 1}
                </span>
                <div>
                  <h3 className="text-lg font-bold">{s.title}</h3>
                  <p className="mt-1 text-primary-foreground/80">{s.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="pricing" className="container scroll-mt-20 py-14 sm:py-20">
        <h2 className="text-3xl font-extrabold sm:text-4xl">Free, or Pro at {PRICING.proMonthly} THB a month</h2>
        <p className="mt-3 max-w-xl text-muted-foreground">
          Prices shown are for badminton courts at launch: {PRICING.courtSlot} THB per {PRICING.slotMinutes}{" "}
          minutes on Free. Football and basketball pricing will be announced. Pro pays for itself after a few
          sessions.
        </p>

        <div className="mt-8 overflow-hidden rounded-2xl border bg-card">
          <table className="w-full table-fixed border-collapse text-left text-sm sm:text-base">
            <caption className="sr-only">Free and Pro plan comparison</caption>
            <thead>
              <tr className="border-b">
                <th scope="col" className="w-[38%] p-3 sm:p-4">
                  <span className="sr-only">Feature</span>
                </th>
                <th scope="col" className="p-3 text-center sm:p-4">
                  <span className="block text-lg font-bold">Free</span>
                  <span className="block text-sm font-normal text-muted-foreground">0 THB</span>
                </th>
                <th scope="col" className="bg-accent/15 p-3 text-center sm:p-4">
                  <span className="block text-lg font-bold">Pro</span>
                  <span className="block text-sm font-normal text-muted-foreground">
                    {PRICING.proMonthly} THB / month
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {matrix.map((row) => (
                <tr key={row.label} className="border-b last:border-0">
                  <th scope="row" className="p-3 font-medium sm:p-4">
                    {row.label}
                  </th>
                  <td className="p-3 text-center sm:p-4">
                    <Cell value={row.free} />
                  </td>
                  <td className="bg-accent/15 p-3 text-center sm:p-4">
                    <Cell value={row.pro} pro />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="container pb-16 sm:pb-24">
        <div className="rounded-2xl bg-secondary p-8 sm:p-12">
          <h2 className="max-w-xl text-3xl font-extrabold sm:text-4xl">Your next game starts with one free account.</h2>
          <Button asChild variant="accent" size="lg" className="mt-6">
            <Link href="/register">Create a free account</Link>
          </Button>
        </div>
      </section>
    </Layout>
  );
}
