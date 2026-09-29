import Link from "next/link";

import { Layout } from "@/components/Layout";
import { CourtLines } from "@/components/CourtLines";

// Two-column auth layout: green court panel (desktop) + form.
export function AuthShell({ title, subtitle, children, footer, aside }) {
  return (
    <Layout>
      <div className="grid lg:min-h-[calc(100vh-4rem)] lg:grid-cols-2">
        <div className="relative hidden overflow-hidden bg-primary text-primary-foreground lg:block">
          <CourtLines className="absolute inset-0 h-full w-full opacity-30" />
          <div className="relative flex h-full flex-col justify-end p-12">
            <p className="max-w-sm text-3xl font-extrabold leading-tight">{aside}</p>
          </div>
        </div>
        <section className="flex items-center justify-center px-4 py-10 sm:px-8">
          <div className="w-full max-w-md">
            <h1 className="text-3xl font-extrabold">{title}</h1>
            <p className="mt-2 text-muted-foreground">{subtitle}</p>
            <div className="mt-8">{children}</div>
            <p className="mt-6 text-sm text-muted-foreground">{footer}</p>
          </div>
        </section>
      </div>
    </Layout>
  );
}

export function AuthLink({ href, children }) {
  return (
    <Link href={href} className="font-semibold text-primary underline underline-offset-4 hover:text-primary/80">
      {children}
    </Link>
  );
}

export function FieldError({ id, error }) {
  if (!error) return null;
  return (
    <p id={id} role="alert" className="text-sm text-destructive">
      {error.message}
    </p>
  );
}
