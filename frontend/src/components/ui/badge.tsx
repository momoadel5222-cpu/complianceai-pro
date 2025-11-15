import * as React from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline';
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
          {
            "default": "bg-gray-100 text-gray-800",
            "secondary": "bg-gray-100 text-gray-800",
            "destructive": "bg-red-500 text-white",
            "outline": "text-gray-800 border border-gray-200"
          }[variant],
          className
        )}
        {...props}
      />
    );
});
Badge.displayName = "Badge";

export { Badge };
