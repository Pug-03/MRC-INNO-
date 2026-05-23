import { useEffect, useState } from "react";
import { Card } from "./Card";
import { useI18n } from "../i18n/I18nProvider";
import { getSystem, SystemStats } from "../api";

function Bar({
  value,
  max = 100,
  tone = "normal",
}: {
  value: number | null;
  max?: number;
  tone?: "normal" | "warm" | "hot" | "unknown";
}) {
  const pct = value == null ? 0 : Math.min(100, (value / max) * 100);
  const color =
    tone === "hot"
      ? "#d84040"
      : tone === "warm"
      ? "#d8a140"
      : tone === "normal"
      ? "#2a8f4a"
      : "#888888";
  return (
    <div className="h-1.5 bg-paper border hairline">
      <div style={{ width: `${pct}%`, background: color }} className="h-full" />
    </div>
  );
}

function toneForTemp(level: string | undefined) {
  if (level === "hot" || level === "warm" || level === "normal") return level;
  return "unknown" as const;
}

function toneForLoad(pct: number | null) {
  if (pct == null) return "unknown" as const;
  if (pct >= 90) return "hot" as const;
  if (pct >= 70) return "warm" as const;
  return "normal" as const;
}

function Row({
  label,
  temp,
  tempLevel,
  load,
  loadUnit = "%",
  extraRight,
  showTemp = true,
}: {
  label: string;
  temp: number | null;
  tempLevel?: string;
  load: number | null;
  loadUnit?: string;
  extraRight?: React.ReactNode;
  showTemp?: boolean;
}) {
  const { t } = useI18n();
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between">
        <span className="uppercase text-[11px] tracking-[0.1em] text-ink-mute">
          {label}
        </span>
        {extraRight}
      </div>

      {showTemp && (
        <div>
          <div className="flex items-baseline justify-between text-sm">
            <span className="text-[11px] text-ink-mute">{t("system.temp")}</span>
            <span className="num">
              {temp == null ? "—" : `${temp.toFixed(0)} °C`}
            </span>
          </div>
          <div className="mt-1">
            <Bar value={temp} max={100} tone={toneForTemp(tempLevel)} />
          </div>
          <div className="mt-0.5 text-[10px] text-ink-mute">
            {t(`system.level.${toneForTemp(tempLevel)}` as const)}
          </div>
        </div>
      )}

      <div>
        <div className="flex items-baseline justify-between text-sm">
          <span className="text-[11px] text-ink-mute">{t("system.load")}</span>
          <span className="num">
            {load == null ? "—" : `${load.toFixed(0)} ${loadUnit}`}
          </span>
        </div>
        <div className="mt-1">
          <Bar value={load} max={100} tone={toneForLoad(load)} />
        </div>
      </div>
    </div>
  );
}

export function SystemHealth() {
  const { t } = useI18n();
  const [s, setS] = useState<SystemStats | null>(null);

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const r = await getSystem();
        if (alive) setS(r);
      } catch {
        /* ignore */
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return (
    <Card title={t("system.title")} icon="cpu">
      <div className="grid gap-5">
        <Row
          label={`${t("system.cpu")}${s ? ` · ${s.cpu.cores} cores` : ""}`}
          temp={null}
          load={s?.cpu.load_percent ?? null}
          showTemp={false}
        />
        <Row
          label={`${t("system.gpu")}${s?.gpu.name ? ` · ${s.gpu.name.replace("NVIDIA GeForce ", "")}` : ""}`}
          temp={s?.gpu.temperature_c ?? null}
          tempLevel={s?.gpu.level}
          load={s?.gpu.load_percent ?? null}
          extraRight={
            s?.gpu.memory_percent != null ? (
              <span className="num text-[11px] text-ink-mute">
                {t("system.vram")} {s.gpu.memory_percent.toFixed(0)} %
              </span>
            ) : null
          }
        />
        <div>
          <div className="flex items-baseline justify-between text-sm">
            <span className="uppercase text-[11px] tracking-[0.1em] text-ink-mute">
              {t("system.mem")}
            </span>
            <span className="num">
              {s
                ? `${s.memory.used_gb.toFixed(1)} / ${s.memory.total_gb.toFixed(1)} GB · ${s.memory.percent.toFixed(0)} %`
                : "—"}
            </span>
          </div>
          <div className="mt-1.5">
            <Bar value={s?.memory.percent ?? null} tone={toneForLoad(s?.memory.percent ?? null)} />
          </div>
        </div>
      </div>
    </Card>
  );
}
