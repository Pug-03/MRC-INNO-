import { Card } from "./Card";
import { useI18n } from "../i18n/I18nProvider";
import { CATEGORIES, CATEGORY_COLOR } from "../theme";
import { Totals } from "../api";

export function TotalCount({ totals }: { totals: Totals | null }) {
  const { t } = useI18n();
  const total = totals?.total ?? 0;

  return (
    <Card title={t("total.title")} icon="counter">
      <div className="flex flex-col gap-5">
        <div className="num text-6xl font-light leading-none">
          {total.toLocaleString()}
        </div>

        <div>
          <div className="text-[11px] uppercase tracking-[0.1em] text-ink-mute mb-2">
            {t("total.legend")}
          </div>
          <div className="grid grid-cols-5 gap-2">
            {CATEGORIES.map((c) => {
              const n = totals ? totals[c] : 0;
              return (
                <div key={c} className="flex flex-col items-start">
                  <span
                    className="block w-full h-1.5"
                    style={{ background: CATEGORY_COLOR[c] }}
                  />
                  <div className="mt-1.5 text-[11px] text-ink-mute">
                    {c}
                  </div>
                  <div className="num text-lg">{n}</div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
}
