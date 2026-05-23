import { useEffect, useState } from "react";
import { Card } from "./Card";
import { useI18n } from "../i18n/I18nProvider";
import { DetectionEvent, sendLine } from "../api";
import { CATEGORY_COLOR } from "../theme";
import { Icon } from "./Icon";

export function EventLog({
  events,
  totalToday,
}: {
  events: DetectionEvent[];
  totalToday: number;
}) {
  const { t, lang } = useI18n();
  const [status, setStatus] = useState<null | "ok" | "fail">(null);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (status === null) return;
    const id = setTimeout(() => setStatus(null), 2500);
    return () => clearTimeout(id);
  }, [status]);

  const onSend = async () => {
    setSending(true);
    try {
      const msg = `Cap Sorter — today: ${totalToday} caps`;
      const r = await sendLine(msg);
      setStatus(r.delivered ? "ok" : "fail");
    } catch {
      setStatus("fail");
    } finally {
      setSending(false);
    }
  };

  return (
    <Card
      title={t("log.title")}
      icon="log"
      action={
        <button
          onClick={onSend}
          disabled={sending}
          className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider px-2.5 py-1 border hairline hover:bg-paper disabled:opacity-50"
        >
          <Icon name="send" size={14} />
          {status === "ok"
            ? t("log.sent")
            : status === "fail"
            ? t("log.failed")
            : t("log.send")}
        </button>
      }
    >
      {events.length === 0 ? (
        <div className="py-8 text-center text-sm text-ink-mute">
          {t("log.empty")}
        </div>
      ) : (
        <ul className="divide-y hairline max-h-[320px] overflow-auto no-scrollbar">
          {events.map((e) => {
            const time = new Date(e.ts).toLocaleTimeString(
              lang === "th" ? "th-TH" : "en-GB",
              { hour12: false }
            );
            return (
              <li
                key={e.id}
                className="flex items-center gap-3 py-2 text-sm"
              >
                <span
                  className="inline-block w-2.5 h-2.5"
                  style={{ background: CATEGORY_COLOR[e.category] }}
                />
                <span className="num text-ink-mute w-20">{time}</span>
                <span className="font-medium w-6">{e.category}</span>
                <span className="text-ink-mute capitalize">{e.color_name}</span>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
