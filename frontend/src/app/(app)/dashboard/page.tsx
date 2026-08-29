"use client";

import { DollarSign, Package, Receipt, ShoppingCart, TrendingUp, Users } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { KpiCard } from "@/components/kpi-card";
import { RevenueChart } from "@/components/revenue-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/state-views";
import { useApiQuery } from "@/lib/use-api";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { formatCurrency, formatPercent } from "@/lib/utils";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, isLoading, error, refetch } = useApiQuery(() => api.analytics.dashboard());

  return (
    <div>
      <PageHeader
        title={`Welcome back${user ? `, ${user.name.split(" ")[0]}` : ""}`}
        description="Your store's performance over the last 30 days."
      />

      {error && <ErrorState message={error} onRetry={refetch} />}

      {!error && isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      )}

      {!error && data && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <KpiCard label="Revenue (30d)" value={formatCurrency(data.revenue_30d)} icon={DollarSign} tone="success" />
            <KpiCard label="Orders (30d)" value={data.orders_30d.toLocaleString()} icon={Package} />
            <KpiCard label="Avg. order value" value={formatCurrency(data.avg_order_value_30d)} icon={TrendingUp} />
            <KpiCard
              label="Refund rate"
              value={formatPercent(data.refund_rate_30d)}
              hint={formatCurrency(data.refund_amount_30d) + " refunded"}
              icon={Receipt}
              tone={data.refund_rate_30d > 0.1 ? "destructive" : "default"}
            />
            <KpiCard label="Active customers" value={data.active_customers_30d.toLocaleString()} icon={Users} />
            <KpiCard
              label="Cart abandonment"
              value={formatPercent(data.cart_abandonment_rate_30d)}
              hint={formatCurrency(data.abandoned_cart_value_30d) + " at risk"}
              icon={ShoppingCart}
              tone={data.cart_abandonment_rate_30d > 0.6 ? "warning" : "default"}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Revenue trend</CardTitle>
            </CardHeader>
            <CardContent>
              {data.revenue_by_day.length > 0 ? (
                <RevenueChart data={data.revenue_by_day} />
              ) : (
                <p className="py-10 text-center text-sm text-muted-foreground">No revenue in this period yet.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top products (30d)</CardTitle>
            </CardHeader>
            <CardContent>
              {data.top_products.length === 0 ? (
                <p className="py-4 text-center text-sm text-muted-foreground">No product sales yet.</p>
              ) : (
                <div className="flex flex-col divide-y divide-border">
                  {data.top_products.map((p, i) => (
                    <div key={p.name} className="flex items-center justify-between gap-4 py-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-medium text-muted-foreground">
                          {i + 1}
                        </span>
                        <span className="truncate text-sm font-medium">{p.name}</span>
                      </div>
                      <div className="flex shrink-0 items-center gap-4 text-sm text-muted-foreground">
                        <span>{p.units} units</span>
                        <span className="w-20 text-right font-medium text-foreground">{formatCurrency(p.revenue)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
