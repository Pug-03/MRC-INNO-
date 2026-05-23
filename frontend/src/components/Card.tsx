import { Icon } from "./Icon";

export function Card({
  title,
  icon,
  action,
  children,
  className = "",
}: {
  title?: string;
  icon?: React.ComponentProps<typeof Icon>["name"];
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`bg-elev border border-frame ${className}`}>
      {(title || action) && (
        <header className="flex items-center justify-between px-5 py-3 border-b hairline">
          <div className="flex items-center gap-2 text-ink-soft">
            {icon && <Icon name={icon} className="text-ink-mute" />}
            <h2 className="text-[13px] font-medium uppercase tracking-[0.08em]">
              {title}
            </h2>
          </div>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
