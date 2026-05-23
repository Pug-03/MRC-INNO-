import { useEffect, useState } from "react";
import { Card } from "../components/Card";
import { useI18n } from "../i18n/I18nProvider";
import { excelUrl, getHistory, Totals } from "../api";
import { CATEGORIES, CATEGORY_COLOR } from "../theme";
import { Icon } from "../components/Icon";

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}
function daysAgoIso(n: number) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

export function HistoryPage() {
  const { t } = useI18n();
  const [start, setStart] = useState(daysAgoIso(13));
  const [end, setEnd] = useState(todayIso());
  const [days, setDays] = useState<Totals[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async (s: string, e: string) => {
    setLoading(true);
    try {
      const r = await getHistory(s, e);
      setDays(r.days);
    } catch {
      setDays([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(start, end);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const maxTotal = Math.max(1, ...days.map((d) => d.total));

  return (
    <div className="grid gap-5">
      <Card
        title={t("history.title")}
        icon="calendar"
        action={
          <a
            href={excelUrl(start, end)}
            className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider px-2.5 py-1 border hairline hover:bg-paper"
          >
            <Icon name="download" size={14} />
            {t("history.export")}
          </a>
        }
      >
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col text-[11px] uppercase tracking-[0.1em] text-ink-mute">
            {t("history.from")}
            <input
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              className="mt-1 border hairline px-2 py-1 text-sm num text-ink"
            />
          </label>
          <label className="flex flex-col text-[11px] uppercase tracking-[0.1em] text-ink-mute">
            {t("history.to")}
            <input
              type="date"
              value={end}
              onChange={(e) => setEnd(e.target.value)}
              className="mt-1 border hairline px-2 py-1 text-sm num text-ink"
            />
          </label>
          <button
            onClick={() => fetchData(start, end)}
            className="px-3 py-1.5 border hairline text-[11px] uppercase tracking-wider hover:bg-paper"
          >
            {t("history.apply")}
          </button>
        </div>
      </Card>

      <Card>
        {loading ? (
          <div className="py-10 text-center text-sm text-ink-mute">…</div>
        ) : days.length === 0 ? (
          <div className="py-10 text-center text-sm text-ink-mute">
            {t("history.empty")}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-[0.1em] text-ink-mute">
                  <th className="py-2 pr-4 font-medium">{t("history.day")}</th>
                  {CATEGORIES.map((c) => (
                    <th key={c} className="py-2 pr-4 font-medium num">
                      {c}
                    </th>
                  ))}
                  <th className="py-2 pr-4 font-medium num">
                    {t("history.total")}
                  </th>
                  <th className="py-2 pl-2 font-medium w-[35%]" />
                </tr>
              </thead>
              <tbody className="divide-y hairline">
                {days.map((d) => (
                  <tr key={d.day}>
                    <td className="py-2 pr-4 num text-ink-soft">{d.day}</td>
                    {CATEGORIES.map((c) => (
                      <td key={c} className="py-2 pr-4 num">
                        {d[c]}
                      </td>
                    ))}
                    <td className="py-2 pr-4 num font-medium">{d.total}</td>
                    <td className="py-2 pl-2">
                      <div className="flex h-2">
                        {CATEGORIES.map((c) => {
                          const w = d.total
                            ? (d[c] / d.total) * (d.total / maxTotal) * 100
                            : 0;
                          if (w === 0) return null;
                          return (
                            <span
                              key={c}
                              style={{
                                width: `${w}%`,
                                background: CATEGORY_COLOR[c],
                              }}
                            />
                          );
                        })}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
