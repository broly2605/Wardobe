import type { ComponentType, SVGProps } from "react";
import {
  AnalyticsIcon,
  DashboardIcon,
  ScanIcon,
  SettingsIcon,
  SparklesIcon,
  WardrobeIcon,
} from "@/components/icons";

export interface NavItem {
  href: string;
  label: string;
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard", Icon: DashboardIcon },
  { href: "/scan", label: "Scan", Icon: ScanIcon },
  { href: "/wardrobe", label: "Wardrobe", Icon: WardrobeIcon },
  { href: "/style", label: "Style", Icon: SparklesIcon },
  { href: "/analytics", label: "Analytics", Icon: AnalyticsIcon },
  { href: "/settings", label: "Settings", Icon: SettingsIcon },
];

/** Whether a nav href is active for the current pathname. */
export function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}
