import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { LogOut, Menu, X } from "lucide-react";

import { Logo } from "@/components/Logo";
import { TierBadge } from "@/components/TierBadge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

const links = [
  { href: "/booking", label: "Booking" },
  { href: "/#pricing", label: "Pricing" },
];

export function Navbar() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [open, setOpen] = useState(false);

  const linkClass = (href) =>
    `rounded-md px-3 py-2 text-sm font-medium hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
      router.pathname === href ? "text-primary" : "text-foreground/80"
    }`;

  function handleLogout() {
    setOpen(false);
    logout();
  }

  return (
    <header className="sticky top-0 z-40 border-b bg-background/90 backdrop-blur">
      <div className="container flex h-16 items-center justify-between gap-4">
        <Logo />

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className={linkClass(l.href)}>
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {loading ? null : user ? (
            <>
              <span className="text-sm font-medium">{user.full_name}</span>
              <TierBadge tier={user.tier} />
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="mr-1.5 h-4 w-4" aria-hidden="true" />
                Log out
              </Button>
            </>
          ) : (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/login">Log in</Link>
              </Button>
              <Button asChild variant="accent" size="sm">
                <Link href="/register">Sign up</Link>
              </Button>
            </>
          )}
        </div>

        <button
          type="button"
          className="inline-flex h-10 w-10 items-center justify-center rounded-md hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring md:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          aria-controls="mobile-menu"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {open && (
        <div id="mobile-menu" className="border-t bg-background md:hidden">
          <nav aria-label="Mobile" className="container flex flex-col gap-1 py-3">
            {links.map((l) => (
              <Link key={l.href} href={l.href} className={linkClass(l.href)} onClick={() => setOpen(false)}>
                {l.label}
              </Link>
            ))}
            <div className="mt-2 flex flex-col gap-2 border-t pt-3">
              {loading ? null : user ? (
                <>
                  <div className="flex items-center gap-2 px-3 text-sm font-medium">
                    {user.full_name}
                    <TierBadge tier={user.tier} />
                  </div>
                  <Button variant="outline" onClick={handleLogout}>
                    Log out
                  </Button>
                </>
              ) : (
                <>
                  <Button asChild variant="outline">
                    <Link href="/login" onClick={() => setOpen(false)}>
                      Log in
                    </Link>
                  </Button>
                  <Button asChild variant="accent">
                    <Link href="/register" onClick={() => setOpen(false)}>
                      Sign up
                    </Link>
                  </Button>
                </>
              )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}
