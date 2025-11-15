import * as React from "react";
import { cn } from "@/lib/utils";

interface TabsProps extends React.HTMLAttributes<HTMLDivElement> {
  defaultValue?: string;
}

interface TabsContextValue {
  value: string;
}

const Tabs = React.forwardRef<HTMLDivElement, TabsProps>(
  ({ className, defaultValue, children, ...props }, ref) => {
    const [value, setValue] = React.useState(defaultValue || "");

    return (
      <div
        ref={ref}
        className={cn("w-full", className)}
        {...props}
      >
        {React.Children.map((child) => {
          if (React.isValidElement(child)) {
            return React.cloneElement(child, {
              onClick: () => setValue(child.props.value as string),
              className: cn(
                child.props.className,
                value === child.props.value
                  ? "bg-muted text-muted-foreground"
                  : "text-muted-foreground hover:text-muted-foreground"
              )
            });
          }
          return child;
        })}
      </div>
    );
});
Tabs.displayName = "Tabs";

export { Tabs };
