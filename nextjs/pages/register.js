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
import { useAuth } from "@/lib/auth";
import { PRICING } from "@/lib/constants";

const schema = z
  .object({
    full_name: z.string().trim().min(1, "Enter your full name").max(100, "Name is too long"),
    email: z.string().min(1, "Enter your email").email("Enter a valid email address"),
    password: z.string().min(8, "Use at least 8 characters"),
    confirm_password: z.string().min(1, "Repeat your password"),
  })
  .refine((v) => v.password === v.confirm_password, {
    path: ["confirm_password"],
    message: "Passwords do not match",
  });

export default function Register() {
  const router = useRouter();
  const { user, loading, register: signUp } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { full_name: "", email: "", password: "", confirm_password: "" },
  });

  useEffect(() => {
    if (!loading && user) router.replace("/booking");
  }, [loading, user, router]);

  async function onSubmit({ full_name, email, password }) {
    try {
      const me = await signUp(full_name.trim(), email, password);
      toast.success(`Account created. Welcome, ${me.full_name}`);
      router.replace("/booking");
    } catch (err) {
      toast.error(err.message);
    }
  }

  const field = (name, label, props) => (
    <div className="space-y-2">
      <Label htmlFor={name}>{label}</Label>
      <Input
        id={name}
        aria-invalid={!!errors[name]}
        aria-describedby={errors[name] ? `${name}-error` : undefined}
        {...props}
        {...register(name)}
      />
      <FieldError id={`${name}-error`} error={errors[name]} />
    </div>
  );

  return (
    <AuthShell
      title="Create your account"
      subtitle="It takes a minute. No payment needed to sign up."
      aside="Every court, one tap each. Stop calling to ask what is free."
      footer={
        <>
          Already have an account? <AuthLink href="/login">Log in</AuthLink>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
        {field("full_name", "Full name", { type: "text", autoComplete: "name" })}
        {field("email", "Email", { type: "email", autoComplete: "email" })}
        {field("password", "Password (8+ characters)", { type: "password", autoComplete: "new-password" })}
        {field("confirm_password", "Confirm password", { type: "password", autoComplete: "new-password" })}

        <p className="rounded-md bg-secondary px-3 py-2 text-sm text-secondary-foreground">
          You start on the Free plan: book up to {PRICING.freeAdvanceDays} days ahead. Upgrade to Pro any time.
        </p>

        <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />}
          {isSubmitting ? "Creating account" : "Create account"}
        </Button>
      </form>
    </AuthShell>
  );
}
