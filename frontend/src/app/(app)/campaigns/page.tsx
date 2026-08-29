"use client";

import { useState } from "react";
import { Loader2, Megaphone, ShoppingCart, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState, EmptyState } from "@/components/state-views";
import { useApiQuery } from "@/lib/use-api";
import { api, ApiError } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import type { CampaignType, CampaignStatus } from "@/lib/types";

const STATUS_VARIANT: Record<CampaignStatus, "secondary" | "default" | "success"> = {
  draft: "secondary",
  ready: "default",
  sent: "success",
};

const TYPE_LABEL: Record<CampaignType, string> = {
  cart_recovery: "Cart recovery",
  win_back: "Win-back",
  segment_promo: "Segment promo",
};

export default function CampaignsPage() {
  const { data: segmentsData } = useApiQuery(() => api.analytics.segments());
  const campaignsQuery = useApiQuery(() => api.campaigns.list());
  const [selectedSegment, setSelectedSegment] = useState("");
  const [generating, setGenerating] = useState<CampaignType | null>(null);
  const [genError, setGenError] = useState<string | null>(null);

  const segments = segmentsData?.summary ?? [];

  async function generate(campaignType: CampaignType, targetSegment?: string) {
    setGenError(null);
    setGenerating(campaignType);
    try {
      await api.campaigns.generate({ campaign_type: campaignType, target_segment: targetSegment });
      campaignsQuery.refetch();
    } catch (err) {
      setGenError(err instanceof ApiError ? err.message : "Could not generate campaign.");
    } finally {
      setGenerating(null);
    }
  }

  const campaigns = campaignsQuery.data ?? [];

  return (
    <div>
      <PageHeader title="Marketing campaigns" description="Generate ready-to-send copy from your live customer data." />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <ShoppingCart className="h-4 w-4" /> Cart recovery
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <p className="text-sm text-muted-foreground">
              Draft a message to every customer with an abandoned cart right now.
            </p>
            <Button onClick={() => generate("cart_recovery")} disabled={generating !== null} className="self-start">
              {generating === "cart_recovery" && <Loader2 className="h-4 w-4 animate-spin" />}
              Generate campaign
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Megaphone className="h-4 w-4" /> Segment promo / win-back
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <p className="text-sm text-muted-foreground">Target one RFM segment with tailored copy.</p>
            <div className="flex flex-wrap gap-2">
              <select
                value={selectedSegment}
                onChange={(e) => setSelectedSegment(e.target.value)}
                className="h-9 flex-1 min-w-[10rem] rounded-md border border-input bg-transparent px-3 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">Select a segment…</option>
                {segments.map((s) => (
                  <option key={s.segment} value={s.segment}>
                    {s.segment} ({s.customer_count})
                  </option>
                ))}
              </select>
              <Button
                onClick={() => generate("segment_promo", selectedSegment)}
                disabled={!selectedSegment || generating !== null}
              >
                {generating === "segment_promo" && <Loader2 className="h-4 w-4 animate-spin" />}
                Generate
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {genError && <p className="mt-4 rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{genError}</p>}

      <div className="mt-8">
        <h2 className="mb-4 text-sm font-medium text-muted-foreground">Generated campaigns</h2>

        {campaignsQuery.error && <ErrorState message={campaignsQuery.error} onRetry={campaignsQuery.refetch} />}

        {!campaignsQuery.error && campaignsQuery.isLoading && (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>
        )}

        {!campaignsQuery.error && !campaignsQuery.isLoading && campaigns.length === 0 && (
          <EmptyState title="No campaigns yet" description="Generate one above to see it appear here." />
        )}

        {!campaignsQuery.error && campaigns.length > 0 && (
          <div className="flex flex-col gap-3">
            {campaigns.map((c) => (
              <Card key={c.id}>
                <CardContent className="flex flex-col gap-3 p-5">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="font-medium">{c.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatDateTime(c.created_at)} · {c.audience_size} recipients
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="outline">{TYPE_LABEL[c.campaign_type]}</Badge>
                      <Badge variant={STATUS_VARIANT[c.status]} className="capitalize">
                        {c.status}
                      </Badge>
                    </div>
                  </div>
                  <details className="group rounded-lg bg-muted p-3 text-sm">
                    <summary className="flex cursor-pointer items-center gap-2 font-medium marker:content-none">
                      <Sparkles className="h-3.5 w-3.5 text-primary" />
                      {c.subject_line}
                    </summary>
                    <p className="mt-3 whitespace-pre-line text-muted-foreground">{c.body}</p>
                  </details>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
