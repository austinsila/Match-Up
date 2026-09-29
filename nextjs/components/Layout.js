import { Logo } from "@/components/Logo";
import { Navbar } from "@/components/Navbar";

export function Layout({ children }) {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
      <footer className="border-t">
        <div className="container flex flex-col gap-2 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <Logo />
          <p>Book any court, any sport. Badminton open now.</p>
        </div>
      </footer>
    </div>
  );
}
