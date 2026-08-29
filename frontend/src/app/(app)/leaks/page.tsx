"use client";

import { AlertTriangle, TrendingDown } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/state-views";
import { useApiQuery } from "@/lib/use-api";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import type { LeakSeverity } from "@/lib/types";

const SEVERITY_VARIANT: Record<LeakSeverity, "destructive" | "warning" | "secondary"> = {
  high: "destructive",
  medium: "warning",
  low: "secondary",
};

export default function LeaksPage() {
  const { data, isLoading, error, refetch } = useApiQuery(() => api.analytics.revenueLeaks());
  const findings = data?.findings ?? [];
  const totalImpact = findings.reduce((sum, f) => sum + f.estimated_monthly_impact, 0);

  return (
    <div>
      <PageHeader
        title="Revenue leak detection"
        description="Rule-based signals surfaced from your refunds, margins, carts, and month-over-month trends."
      />

      {error && <ErrorState message={error} onRetry={refetch} />}

      {!error && isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      )}

      {!error && !isLoading && findings.length === 0 && (
        <EmptyState title="No leaks detected" description="Nothing crossed a risk threshold in the current data." />
      )}

      {!error && findings.length > 0 && (
        <div className="flex flex-col gap-4">
          <Card className="border-primary/30 bg-accent">
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <TrendingDown className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Estimated combined monthly impact</p>
                <p className="text-xl font-semibold">{formatCurrency(totalImpact)}</p>
              </div>
            </CardContent>
          </Card>

          {findings.map((f, i) => (
            <Card key={`${f.leak_type}-${i}`}>
              <CardContent className="flex flex-col gap-3 p-5">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    <h3 className="font-medium">{f.title}</h3>
                  </div>
                  <Badge variant={SEVERITY_VARIANT[f.severity]} className="capitalize">
                    {f.severity} severity
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{f.description}</p>
                <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-muted p-3">
                  <p className="text-sm">{f.recommendation}</p>
                  <span className="shrink-0 text-sm font-semibold text-destructive">
                    -{formatCurrency(f.estimated_monthly_impact)}/mo
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
