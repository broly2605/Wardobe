"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { NAV_ITEMS, isActive } from "./nav";
import { ShirtIcon } from "@/components/icons";
import { cn } from "@/lib/cn";

/** Desktop sidebar (hidden on small screens; mobile uses the bottom bar). */
export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col p-4 lg:flex">
      <div className="flex h-full flex-col rounded-2xl p-4 glass shadow-glass">
        <Link href="/" className="mb-8 flex items-center gap-3 px-2 pt-2">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-brand text-white shadow-glass">
            <ShirtIcon width={22} height={22} />
          </span>
          <div className="leading-tight">
            <p className="font-semibold text-foreground">Wardrobe</p>
            <p className="text-xs text-muted">AI Closet Scanner</p>
          </div>
        </Link>

        <nav className="flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map(({ href, label, Icon }) => {
            const active = isActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "text-brand"
                    : "text-muted hover:bg-surface-2 hover:text-foreground",
                )}
              >
                {active && (
                  <motion.span
                    layoutId="sidebar-active"
                    className="absolute inset-0 rounded-xl bg-brand-soft"
                    transition={{ type: "spring", stiffness: 400, damping: 32 }}
                  />
                )}
                <span className="relative z-10 flex items-center gap-3">
                  <Icon width={18} height={18} />
                  {label}
                </span>
              </Link>
            );
          })}
        </nav>

        <p className="px-3 pt-4 text-xs text-muted">
          Single-user · Local
        </p>
      </div>
    </aside>
  );
}
