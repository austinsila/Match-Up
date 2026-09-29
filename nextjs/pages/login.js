import { useEffect } from "react";
import { useRouter } from "next/router";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

import { AuthLink, AuthShell, FieldError } from "@/components/AuthShell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { safeNext, useAuth } from "@/lib/auth";

const schema = z.object({
  email: z.string().min(1, "Enter your email").email("Enter a valid email address"),
  password: z.string().min(1, "Enter your password"),
});

export default function Login() {
  const router = useRouter();
  const { user, loading, login } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(schema), defaultValues: { email: "", password: "" } });

  // Already logged in: skip the form.
  useEffect(() => {
    if (!loading && user && router.isReady) router.replace(safeNext(router.query.next));
  }, [loading, user, router]);

  async function onSubmit({ email, password }) {
    try {
      const me = await login(email, password);
      toast.success(`Welcome back, ${me.full_name}`);
      router.replace(safeNext(router.query.next));
    } catch (err) {
      toast.error(err.message);
    }
  }

  return (
    <AuthShell
      title="Log in"
      subtitle="Pick up where you left off and grab your court."
      aside="Your court is waiting. Pick a slot, pay, and just show up."
      footer={
        <>
          New to Match Up? <AuthLink href="/register">Create a free account</AuthLink>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            aria-invalid={!!errors.email}
            aria-describedby={errors.email ? "email-error" : undefined}
            {...register("email")}
          />
          <FieldError id="email-error" error={errors.email} />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            aria-invalid={!!errors.password}
            aria-describedby={errors.password ? "password-error" : undefined}
            {...register("password")}
          />
          <FieldError id="password-error" error={errors.password} />
        </div>

        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
          {isSubmitting ? "Logging in" : "Log in"}
        </Button>
      </form>
    </AuthShell>
  );
}
