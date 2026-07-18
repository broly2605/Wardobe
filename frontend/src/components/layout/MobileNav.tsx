"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { NAV_ITEMS, isActive } from "./nav";
import { cn } from "@/lib/cn";

/** Bottom tab bar shown on small screens. */
export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 p-3 lg:hidden">
      <div className="flex items-center justify-around rounded-2xl px-2 py-1.5 shadow-glass-lg glass-strong">
        {NAV_ITEMS.map(({ href, label, Icon }) => {
          const active = isActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              aria-label={label}
              className={cn(
                "relative flex flex-1 flex-col items-center gap-0.5 rounded-xl px-1 py-1.5 text-[10px] font-medium transition-colors",
                active ? "text-brand" : "text-muted",
              )}
            >
              {active && (
                <motion.span
                  layoutId="mobilenav-active"
                  className="absolute inset-0 rounded-xl bg-brand-soft"
                  transition={{ type: "spring", stiffness: 400, damping: 32 }}
                />
              )}
              <span className="relative z-10 flex flex-col items-center gap-0.5">
                <Icon width={20} height={20} />
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
