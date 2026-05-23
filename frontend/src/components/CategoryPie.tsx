import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";
import { Card } from "./Card";
import { useI18n } from "../i18n/I18nProvider";
import { CATEGORIES, CATEGORY_COLOR } from "../theme";
import { Totals } from "../api";

export function CategoryPie({ totals }: { totals: Totals | null }) {
  const { t } = useI18n();

  const data = CATEGORIES.map((c) => ({
    name: c,
    value: totals ? totals[c] : 0,
  }));
  const total = data.reduce((a, b) => a + b.value, 0);

  return (
    <Card title={t("pie.title")} icon="pie">
      {total === 0 ? (
        <div className="py-10 text-center text-sm text-ink-mute">
          {t("pie.empty")}
        </div>
      ) : (
        <div className="grid gap-5">
          <div className="h-[160px]">
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  innerRadius={48}
                  outerRadius={78}
                  stroke="#ffffff"
                  strokeWidth={2}
                  startAngle={90}
                  endAngle={-270}
                  isAnimationActive={false}
                >
                  {data.map((d) => (
                    <Cell key={d.name} fill={CATEGORY_COLOR[d.name as keyof typeof CATEGORY_COLOR]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>

          <ul className="divide-y hairline min-w-0">
            {data.map((d) => {
              const pct = total ? (d.value / total) * 100 : 0;
              return (
                <li
                  key={d.name}
                  className="flex items-center justify-between gap-3 py-2 text-sm min-w-0"
                >
                  <div className="flex items-center gap-2.5 min-w-0 flex-1">
                    <span
                      className="inline-block w-3 h-3 flex-shrink-0"
                      style={{ background: CATEGORY_COLOR[d.name as keyof typeof CATEGORY_COLOR] }}
                    />
                    <span className="font-medium flex-shrink-0">{d.name}</span>
                    <span className="text-ink-mute text-xs truncate">
                      {t(`cat.${d.name}` as const)}
                    </span>
                  </div>
                  <div className="flex items-baseline gap-3 num flex-shrink-0">
                    <span className="tabular-nums w-10 text-right">{d.value}</span>
                    <span className="text-ink-mute text-xs w-14 text-right whitespace-nowrap">
                      {pct.toFixed(1)}%
                    </span>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </Card>
  );
}
