"use client";

import { useState } from "react";
import { FileText, Loader2, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/state-views";
import { useApiQuery } from "@/lib/use-api";
import { api, ApiError } from "@/lib/api";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function ReportsPage() {
  const { data, isLoading, error, refetch } = useApiQuery(() => api.reports.list());
  const [generating, setGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);
  const reports = data ?? [];

  async function generateReport() {
    setGenError(null);
    setGenerating(true);
    try {
      await api.reports.generate();
      refetch();
    } catch (err) {
      setGenError(err instanceof ApiError ? err.message : "Could not generate report.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Weekly executive reports"
        description="A narrative summary of performance and top issues, generated on demand."
        action={
          <Button onClick={generateReport} disabled={generating}>
            {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            Generate this week&apos;s report
          </Button>
        }
      />

      {genError && <p className="mb-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{genError}</p>}

      {error && <ErrorState message={error} onRetry={refetch} />}

      {!error && isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      )}

      {!error && !isLoading && reports.length === 0 && (
        <EmptyState title="No reports yet" description="Generate your first weekly report to see it here." />
      )}

      {!error && reports.length > 0 && (
        <div className="flex flex-col gap-4">
          {reports.map((r) => {
            const metrics = r.metrics as {
              revenue_30d?: number;
              orders_30d?: number;
              refund_rate_30d?: number;
              cart_abandonment_rate_30d?: number;
              top_leak_findings?: string[];
            };
            return (
              <Card key={r.id}>
                <CardContent className="flex flex-col gap-4 p-5">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary" />
                    <p className="font-medium">
                      {formatDate(r.period_start)} — {formatDate(r.period_end)}
                    </p>
                  </div>
                  <p className="text-sm leading-relaxed text-muted-foreground">{r.narrative}</p>
                  {metrics.top_leak_findings && metrics.top_leak_findings.length > 0 && (
                    <ul className="flex flex-col gap-1.5 rounded-lg bg-muted p-3 text-sm">
                      {metrics.top_leak_findings.map((item, i) => (
                        <li key={i} className="flex gap-2">
                          <span className="text-muted-foreground">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  <div className="flex flex-wrap gap-6 border-t border-border pt-3 text-sm">
                    {metrics.revenue_30d !== undefined && (
                      <div>
                        <p className="text-xs text-muted-foreground">Revenue</p>
                        <p className="font-medium">{formatCurrency(metrics.revenue_30d)}</p>
                      </div>
                    )}
                    {metrics.orders_30d !== undefined && (
                      <div>
                        <p className="text-xs text-muted-foreground">Orders</p>
                        <p className="font-medium">{metrics.orders_30d}</p>
                      </div>
                    )}
                    {metrics.refund_rate_30d !== undefined && (
                      <div>
                        <p className="text-xs text-muted-foreground">Refund rate</p>
                        <p className="font-medium">{(metrics.refund_rate_30d * 100).toFixed(1)}%</p>
                      </div>
                    )}
                    {metrics.cart_abandonment_rate_30d !== undefined && (
                      <div>
                        <p className="text-xs text-muted-foreground">Cart abandonment</p>
                        <p className="font-medium">{(metrics.cart_abandonment_rate_30d * 100).toFixed(1)}%</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
