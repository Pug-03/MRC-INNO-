import { useEffect, useState } from "react";
import { useI18n } from "../i18n/I18nProvider";

export function Clock() {
  const { lang } = useI18n();
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const locale = lang === "th" ? "th-TH" : "en-GB";
  const date = now.toLocaleDateString(locale, {
    weekday: "short",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
  const time = now.toLocaleTimeString(locale, { hour12: false });

  return (
    <div className="text-right num leading-tight">
      <div className="text-[11px] uppercase tracking-[0.1em] text-ink-mute">
        {date}
      </div>
      <div className="text-lg text-ink">{time}</div>
    </div>
  );
}
