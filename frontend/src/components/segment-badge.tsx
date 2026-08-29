import { cn } from "@/lib/utils";

const SEGMENT_STYLES: Record<string, string> = {
  Champions: "bg-success/15 text-success",
  "Loyal Customers": "bg-primary/15 text-primary",
  "Big Spenders": "bg-accent text-accent-foreground",
  "At Risk": "bg-warning/15 text-warning",
  "New Customers": "bg-secondary text-secondary-foreground",
  Lost: "bg-destructive/10 text-destructive",
  "Needs Attention": "bg-warning/15 text-warning",
};

export function SegmentBadge({ segment }: { segment: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        SEGMENT_STYLES[segment] ?? "bg-muted text-muted-foreground",
      )}
    >
      {segment}
    </span>
  );
}
