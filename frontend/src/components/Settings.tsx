import { useEffect, useState } from "react";
import { Card } from "./Card";
import { useI18n } from "../i18n/I18nProvider";
import {
  getSettings,
  resetAll,
  resetSettings,
  setAutoNotify,
  setInterval_,
  setRoi,
  Settings as S,
} from "../api";

export function Settings({ onAfterReset }: { onAfterReset?: () => void }) {
  const { t } = useI18n();
  const [s, setS] = useState<S | null>(null);
  const [busy, setBusy] = useState(false);
  const [resetStatus, setResetStatus] = useState<null | "ok">(null);

  const load = async () => {
    try {
      setS(await getSettings());
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onInterval = async (v: number) => {
    setBusy(true);
    try {
      await setInterval_(v);
      setS((prev) => (prev ? { ...prev, interval_sec: v } : prev));
    } finally {
      setBusy(false);
    }
  };

  const onToggle = async () => {
    if (!s) return;
    setBusy(true);
    try {
      const next = !s.auto_notify;
      await setAutoNotify(next);
      setS({ ...s, auto_notify: next });
    } finally {
      setBusy(false);
    }
  };

  const onResetData = async () => {
    if (!confirm(t("settings.reset_confirm"))) return;
    setBusy(true);
    try {
      await resetAll("all");
      setResetStatus("ok");
      setTimeout(() => setResetStatus(null), 2000);
      onAfterReset?.();
    } finally {
      setBusy(false);
    }
  };

  const onResetSettings = async () => {
    if (!confirm(t("settings.reset_settings_confirm"))) return;
    setBusy(true);
    try {
      const next = await resetSettings();
      setS(next);
      setResetStatus("ok");
      setTimeout(() => setResetStatus(null), 2000);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card title={t("settings.title")} icon="cpu">
      <div className="grid gap-4">
        <div>
          <div className="text-[11px] uppercase tracking-[0.1em] text-ink-mute mb-1.5">
            {t("settings.interval")}
          </div>
          <div className="flex gap-1">
            {(s?.allowed_intervals ?? [0.5, 1, 2, 3]).map((v) => {
              const active = s?.interval_sec === v;
              return (
                <button
                  key={v}
                  disabled={busy}
                  onClick={() => onInterval(v)}
                  className={
                    "flex-1 text-[11px] uppercase tracking-wider px-2 py-1.5 border hairline num " +
                    (active
                      ? "bg-ink text-paper border-ink"
                      : "text-ink-mute hover:text-ink")
                  }
                >
                  {v} {t("settings.seconds")}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <div className="flex items-baseline justify-between mb-1.5">
            <div className="text-[11px] uppercase tracking-[0.1em] text-ink-mute">
              {t("settings.roi")}
            </div>
            <div className="text-[11px] num text-ink-mute">
              {s ? `${Math.round(s.roi_fraction * 100)}%` : "-"}
            </div>
          </div>
          <input
            type="range"
            min={5}
            max={45}
            step={1}
            value={s ? Math.round(s.roi_fraction * 100) : 20}
            disabled={busy || !s}
            onChange={(e) => {
              const pct = Number(e.target.value);
              const f = pct / 100;
              setS((prev) => (prev ? { ...prev, roi_fraction: f } : prev));
              setRoi(f).catch(() => {});
            }}
            className="w-full accent-ink"
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="text-[11px] uppercase tracking-[0.1em] text-ink-mute">
            {t("settings.auto_notify")}
          </div>
          <button
            onClick={onToggle}
            disabled={busy}
            className={
              "relative inline-flex h-5 w-9 items-center border hairline " +
              (s?.auto_notify ? "bg-ink" : "bg-paper")
            }
            aria-pressed={s?.auto_notify ?? false}
          >
            <span
              className={
                "inline-block h-3 w-3 bg-elev border hairline transition-transform " +
                (s?.auto_notify ? "translate-x-5" : "translate-x-1")
              }
            />
          </button>
        </div>

        <div className="border-t hairline pt-3 grid grid-cols-2 gap-2">
          <button
            onClick={onResetSettings}
            disabled={busy}
            className="text-[11px] uppercase tracking-wider py-1.5 border hairline text-ink hover:bg-paper disabled:opacity-50"
          >
            {t("settings.reset_settings")}
          </button>
          <button
            onClick={onResetData}
            disabled={busy}
            className="text-[11px] uppercase tracking-wider py-1.5 border hairline text-ink hover:bg-paper disabled:opacity-50"
          >
            {resetStatus === "ok" ? t("settings.reset_done") : t("settings.reset_data")}
          </button>
        </div>
      </div>
    </Card>
  );
}
