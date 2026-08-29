"use client";

import { useMemo, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/state-views";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useApiQuery } from "@/lib/use-api";
import { api } from "@/lib/api";
import type { RiskTier } from "@/lib/types";

const TIER_VARIANT: Record<RiskTier, "destructive" | "warning" | "secondary"> = {
  high: "destructive",
  medium: "warning",
  low: "secondary",
};

export default function ChurnPage() {
  const { data, isLoading, error, refetch } = useApiQuery(() => api.analytics.churn());
  const [tier, setTier] = useState<"all" | RiskTier>("all");

  const customers = useMemo(() => data?.customers ?? [], [data]);
  const sorted = useMemo(() => [...customers].sort((a, b) => b.risk_score - a.risk_score), [customers]);
  const filtered = tier === "all" ? sorted : sorted.filter((c) => c.risk_tier === tier);

  const counts = useMemo(
    () => ({
      high: customers.filter((c) => c.risk_tier === "high").length,
      medium: customers.filter((c) => c.risk_tier === "medium").length,
      low: customers.filter((c) => c.risk_tier === "low").length,
    }),
    [customers],
  );

  return (
    <div>
      <PageHeader
        title="Churn risk"
        description="Heuristic score based on how overdue each customer is against their own historical order cadence."
      />

      {error && <ErrorState message={error} onRetry={refetch} />}

      {!error && isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      )}

      {!error && !isLoading && customers.length === 0 && (
        <EmptyState title="No churn signal yet" description="Customers need repeat order history to compute risk." />
      )}

      {!error && customers.length > 0 && (
        <div className="flex flex-col gap-4">
          <Tabs value={tier} onValueChange={(v) => setTier(v as typeof tier)}>
            <TabsList>
              <TabsTrigger value="all">All ({customers.length})</TabsTrigger>
              <TabsTrigger value="high">High ({counts.high})</TabsTrigger>
              <TabsTrigger value="medium">Medium ({counts.medium})</TabsTrigger>
              <TabsTrigger value="low">Low ({counts.low})</TabsTrigger>
            </TabsList>
          </Tabs>

          <Card>
            <CardContent className="p-0">
              <div className="divide-y divide-border">
                {filtered.map((c) => (
                  <div key={c.customer_id} className="flex flex-col gap-2 p-5 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{c.customer_name}</p>
                        <Badge variant={TIER_VARIANT[c.risk_tier]} className="capitalize">
                          {c.risk_tier} risk
                        </Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{c.reason}</p>
                    </div>
                    <div className="flex shrink-0 items-center gap-4 text-sm">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-destructive"
                          style={{ width: `${Math.round(c.risk_score * 100)}%` }}
                        />
                      </div>
                      <span className="w-10 text-right font-medium tabular-nums">{Math.round(c.risk_score * 100)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
