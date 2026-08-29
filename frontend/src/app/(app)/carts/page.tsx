"use client";

import Link from "next/link";
import { Clock, Mail } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/state-views";
import { useApiQuery } from "@/lib/use-api";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

function formatHoursAgo(hours: number) {
  if (hours < 24) return `${Math.round(hours)}h ago`;
  return `${Math.round(hours / 24)}d ago`;
}

export default function CartsPage() {
  const { data, isLoading, error, refetch } = useApiQuery(() => api.analytics.abandonedCarts());
  const carts = data?.carts ?? [];
  const totalValue = carts.reduce((sum, c) => sum + c.total_amount, 0);

  return (
    <div>
      <PageHeader
        title="Abandoned carts"
        description="Carts left behind in the last 30 days, most recent first."
        action={
          <Button asChild>
            <Link href="/campaigns">Generate recovery campaign</Link>
          </Button>
        }
      />

      {error && <ErrorState message={error} onRetry={refetch} />}

      {!error && isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      )}

      {!error && !isLoading && carts.length === 0 && (
        <EmptyState title="No abandoned carts" description="Nothing was left behind in the last 30 days." />
      )}

      {!error && carts.length > 0 && (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{carts.length} carts</span> worth{" "}
            <span className="font-medium text-foreground">{formatCurrency(totalValue)}</span> at risk
          </p>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {carts.map((cart) => (
              <Card key={cart.cart_id}>
                <CardContent className="flex flex-col gap-3 p-5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="font-medium">{cart.customer_name}</p>
                      <p className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Mail className="h-3 w-3" />
                        {cart.customer_email}
                      </p>
                    </div>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatHoursAgo(cart.hours_since_abandoned)}
                    </span>
                  </div>

                  <div className="flex flex-col gap-1.5 rounded-lg bg-muted p-3">
                    {cart.items.map((item, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">
                          {item.quantity} x {item.product_name}
                        </span>
                        <span>{formatCurrency(item.unit_price * item.quantity)}</span>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Cart total</span>
                    <span className="font-semibold">{formatCurrency(cart.total_amount)}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
