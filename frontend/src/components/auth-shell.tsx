import { BarChart3, MessageSquareText, ShoppingCart, TrendingDown } from "lucide-react";

const FEATURES = [
  { icon: BarChart3, text: "Real-time revenue, refund, and cart analytics" },
  { icon: TrendingDown, text: "Automatic revenue leak detection" },
  { icon: ShoppingCart, text: "Abandoned cart recovery campaigns" },
  { icon: MessageSquareText, text: "Chat with an AI agent that queries your data" },
];

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-primary p-10 text-primary-foreground lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.15),transparent_45%),radial-gradient(circle_at_80%_80%,rgba(255,255,255,0.12),transparent_45%)]" />
        <div className="relative z-10 flex items-center gap-2 text-lg font-semibold">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-foreground/15 font-bold">M</div>
          MerchantGPT
        </div>
        <div className="relative z-10 flex flex-col gap-6">
          <h1 className="text-3xl font-semibold leading-tight text-balance">
            Your autonomous AI growth manager for e-commerce.
          </h1>
          <ul className="flex flex-col gap-4">
            {FEATURES.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm text-primary-foreground/90">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-foreground/15">
                  <Icon className="h-4 w-4" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="relative z-10 text-xs text-primary-foreground/70">
          Analyzes sales, customers, carts, and refunds — then recommends and executes growth actions.
        </p>
      </div>
      <div className="flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  );
}
