"use client";

import { useState } from "react";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { AuthShell } from "@/components/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth-context";

export default function RegisterPage() {
  const { register, error, clearError } = useAuth();
  const [merchantName, setMerchantName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [industry, setIndustry] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await register({ merchant_name: merchantName, name, email, password, industry: industry || undefined });
    } catch {
      // error surfaced via auth context
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthShell>
      <div className="flex flex-col gap-2 text-left">
        <h2 className="text-2xl font-semibold">Create your account</h2>
        <p className="text-sm text-muted-foreground">Set up MerchantGPT for your store in under a minute.</p>
      </div>

      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="merchant_name">Store / merchant name</Label>
          <Input
            id="merchant_name"
            required
            value={merchantName}
            onChange={(e) => {
              setMerchantName(e.target.value);
              clearError();
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="name">Your name</Label>
          <Input
            id="name"
            required
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              clearError();
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              clearError();
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            maxLength={72}
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              clearError();
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="industry">Industry (optional)</Label>
          <Input
            id="industry"
            placeholder="Home goods, apparel, beauty…"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          />
        </div>

        {error && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}

        <Button type="submit" disabled={isSubmitting} className="mt-2">
          {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
