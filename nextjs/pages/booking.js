import { useState } from "react";
import { Loader2 } from "lucide-react";

import { Layout } from "@/components/Layout";
import { TierBadge } from "@/components/TierBadge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useRequireAuth } from "@/lib/auth";
import { DEFAULT_SPORT, SPORTS } from "@/lib/constants";

export default function Booking() {
  const { user, ready } = useRequireAuth();
  const [sport, setSport] = useState(DEFAULT_SPORT);

  return (
    <Layout>
      <div className="container py-10">
        {!ready ? (
          <div className="flex items-center gap-2 text-muted-foreground" role="status">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Loading your account
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-3xl font-extrabold">Hi, {user.full_name}</h1>
              <TierBadge tier={user.tier} />
            </div>
            <Tabs value={sport} onValueChange={setSport} className="mt-6">
              <div className="max-w-full overflow-x-auto">
                <TabsList aria-label="Sport">
                  {SPORTS.map((s) => (
                    <TabsTrigger key={s.id} value={s.id} disabled={!s.available}>
                      {s.label}
                      {!s.available && <span className="ml-1.5 text-xs font-normal">(Coming soon)</span>}
                    </TabsTrigger>
                  ))}
                </TabsList>
              </div>
              {SPORTS.filter((s) => s.available).map((s) => (
                <TabsContent key={s.id} value={s.id}>
                  <p className="rounded-lg border border-dashed p-10 text-center text-muted-foreground">
                    {s.label} booking grid coming soon.
                  </p>
                </TabsContent>
              ))}
            </Tabs>
          </>
        )}
      </div>
    </Layout>
  );
}
