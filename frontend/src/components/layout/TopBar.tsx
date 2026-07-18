"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "./nav";
import { ThemeToggle } from "./ThemeToggle";
import { ShirtIcon } from "@/components/icons";

function titleFor(pathname: string): string {
  if (pathname.startsWith("/wardrobe/")) return "Item Details";
  const match = NAV_ITEMS.find(
    (n) => n.href === pathname || (n.href !== "/" && pathname.startsWith(n.href)),
  );
  return match?.label ?? "Dashboard";
}

export function TopBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 mb-6 flex items-center justify-between gap-3 rounded-2xl px-4 py-3 glass shadow-glass">
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-brand text-white lg:hidden"
          aria-label="Home"
        >
          <ShirtIcon width={18} height={18} />
        </Link>
        <h1 className="text-lg font-semibold text-foreground">
          {titleFor(pathname)}
        </h1>
      </div>
      <ThemeToggle />
    </header>
  );
}
