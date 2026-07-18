import { forwardRef, type SelectHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...rest }, ref) => (
  <select
    ref={ref}
    className={cn(
      "h-10 rounded-xl border border-border bg-surface px-3 text-sm text-foreground transition-colors",
      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand",
      className,
    )}
    {...rest}
  >
    {children}
  </select>
));

Select.displayName = "Select";
