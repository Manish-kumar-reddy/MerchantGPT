"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, TrendingDown, Users, ShoppingCart, MessageSquareText, Menu } from "lucide-react";
import { cn } from "@/lib/utils";

const MOBILE_ITEMS = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/chat", label: "Chat", icon: MessageSquareText },
  { href: "/leaks", label: "Leaks", icon: TrendingDown },
  { href: "/segments", label: "Segments", icon: Users },
  { href: "/carts", label: "Carts", icon: ShoppingCart },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-border bg-card md:hidden">
      {MOBILE_ITEMS.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname?.startsWith(href + "/");
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium",
              active ? "text-primary" : "text-muted-foreground",
            )}
          >
            <Icon className="h-5 w-5" />
            {label}
          </Link>
        );
      })}
      <Link
        href="/campaigns"
        className={cn(
          "flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium",
          pathname?.startsWith("/campaigns") || pathname?.startsWith("/reports") || pathname?.startsWith("/churn")
            ? "text-primary"
            : "text-muted-foreground",
        )}
      >
        <Menu className="h-5 w-5" />
        More
      </Link>
    </nav>
  );
}
