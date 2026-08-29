"use client";

import { useMemo, useState } from "react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/state-views";
import { SegmentBadge } from "@/components/segment-badge";
import { cn, formatCurrency } from "@/lib/utils";
import { useApiQuery } from "@/lib/use-api";
import { api } from "@/lib/api";

export default function SegmentsPage() {
  const { data, isLoading, error, refetch } = useApiQuery(() => api.analytics.segments());
  const [activeSegment, setActiveSegment] = useState<string | null>(null);

  const summary = useMemo(() => [...(data?.summary ?? [])].sort((a, b) => b.total_monetary - a.total_monetary), [data]);
  const customers = data?.customers ?? [];
  const visibleCustomers = activeSegment ? customers.filter((c) => c.segment === activeSegment) : customers;

  return (
    <div>
      <PageHeader
        title="Customer segmentation"
        description="RFM segments computed relative to your own customer population -- not fixed cutoffs."
      />

      {error && <ErrorState message={error} onRetry={refetch} />}

      {!error && isLoading && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      )}

      {!error && !isLoading && customers.length === 0 && (
        <EmptyState title="No customers yet" description="Segments will appear once customers have order history." />
      )}

      {!error && customers.length > 0 && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {summary.map((s) => (
              <button
                key={s.segment}
                onClick={() => setActiveSegment(activeSegment === s.segment ? null : s.segment)}
                className={cn(
                  "rounded-xl border border-border bg-card p-4 text-left transition-colors hover:border-primary/40",
                  activeSegment === s.segment && "border-primary ring-1 ring-primary",
                )}
              >
                <SegmentBadge segment={s.segment} />
                <p className="mt-3 text-xl font-semibold">{s.customer_count}</p>
                <p className="text-xs text-muted-foreground">{formatCurrency(s.total_monetary)} lifetime value</p>
              </button>
            ))}
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="px-5 py-3 font-medium">Customer</th>
                      <th className="px-5 py-3 font-medium">Segment</th>
                      <th className="px-5 py-3 font-medium">RFM</th>
                      <th className="px-5 py-3 font-medium">Recency</th>
                      <th className="px-5 py-3 font-medium">Orders</th>
                      <th className="px-5 py-3 text-right font-medium">Lifetime value</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {visibleCustomers.map((c) => (
                      <tr key={c.customer_id} className="hover:bg-muted/50">
                        <td className="px-5 py-3 font-medium">{c.customer_name}</td>
                        <td className="px-5 py-3">
                          <SegmentBadge segment={c.segment} />
                        </td>
                        <td className="px-5 py-3 font-mono text-xs text-muted-foreground">
                          {c.r_score}-{c.f_score}-{c.m_score}
                        </td>
                        <td className="px-5 py-3 text-muted-foreground">{c.recency_days}d ago</td>
                        <td className="px-5 py-3 text-muted-foreground">{c.frequency}</td>
                        <td className="px-5 py-3 text-right font-medium">{formatCurrency(c.monetary)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
