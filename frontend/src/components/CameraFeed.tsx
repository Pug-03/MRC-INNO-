import { ChangeEvent, useEffect, useState } from "react";
import { Card } from "./Card";
import { useI18n } from "../i18n/I18nProvider";
import {
  CameraDevice,
  getSettings,
  getStats,
  listCameras,
  selectCamera,
  setPaused,
  streamUrl,
  StatsResponse,
} from "../api";
import { CATEGORY_COLOR } from "../theme";
import { Icon } from "./Icon";

export function CameraFeed() {
  const { t } = useI18n();
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [paused, setPausedLocal] = useState(false);
  const [devices, setDevices] = useState<CameraDevice[]>([]);
  const [currentDevice, setCurrentDevice] = useState<number | null>(null);
  const [streamKey, setStreamKey] = useState(0);
  const [switching, setSwitching] = useState(false);

  const refreshDevices = async () => {
    try {
      const d = await listCameras();
      setDevices(d.devices);
      setCurrentDevice(d.current);
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const s = await getStats();
        if (alive) setStats(s);
      } catch {
        /* ignore */
      }
    };
    tick();
    const id = setInterval(tick, 1000);
    getSettings().then((s) => alive && setPausedLocal(s.paused)).catch(() => {});
    refreshDevices();
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const togglePause = async () => {
    const next = !paused;
    setPausedLocal(next);
    try {
      await setPaused(next);
    } catch {
      setPausedLocal(!next);
    }
  };

  const onPickDevice = async (e: ChangeEvent<HTMLSelectElement>) => {
    const value = parseInt(e.target.value, 10);
    if (Number.isNaN(value) || value === currentDevice) return;
    setSwitching(true);
    try {
      const r = await selectCamera(value);
      setCurrentDevice(r.current);
      // Force the MJPEG <img> to reconnect so we drop the old stream buffer.
      setStreamKey((k) => k + 1);
      refreshDevices();
    } catch (err) {
      alert(t("camera.switch_failed"));
    } finally {
      setSwitching(false);
    }
  };

  const live = stats?.live;

  return (
    <Card
      title={t("camera.title")}
      icon="camera"
      action={
        <div className="flex items-center gap-2">
          <select
            value={currentDevice ?? ""}
            onChange={onPickDevice}
            disabled={switching || devices.length === 0}
            title={t("camera.device")}
            className="text-[11px] uppercase tracking-wider px-2 py-1 border hairline bg-paper text-ink disabled:opacity-50"
          >
            {devices.length === 0 && (
              <option value="">{t("camera.no_devices")}</option>
            )}
            {currentDevice === null && devices.length > 0 && (
              <option value="">{t("camera.device")}</option>
            )}
            {devices.map((d) => (
              <option key={d.index} value={d.index}>
                {d.name}
              </option>
            ))}
          </select>
          <button
            onClick={refreshDevices}
            disabled={switching}
            title={t("camera.refresh")}
            className="text-[11px] uppercase tracking-wider px-2 py-1 border hairline hover:bg-ink hover:text-paper disabled:opacity-50"
          >
            {t("camera.refresh")}
          </button>
          <button
            onClick={togglePause}
            className={
              "flex items-center gap-1.5 text-[11px] uppercase tracking-wider px-3 py-1 border " +
              (paused
                ? "bg-cat-b text-white border-cat-b"
                : "bg-ink text-paper border-ink hover:opacity-90")
            }
          >
            <Icon name={paused ? "play" : "pause"} size={14} />
            {paused ? t("camera.resume") : t("camera.pause")}
          </button>
        </div>
      }
    >
      <div className="grid gap-5 md:grid-cols-[minmax(0,1fr)_220px]">
        <div className="relative bg-black aspect-[4/3] overflow-hidden">
          <img
            key={streamKey}
            src={`${streamUrl}?k=${streamKey}`}
            alt="camera"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="space-y-4">
          <div>
            <div className="text-[11px] uppercase tracking-[0.1em] text-ink-mute">
              {t("camera.detected")}
            </div>
            {live ? (
              <div className="mt-1 flex items-center gap-3">
                <span
                  className="inline-block w-8 h-8 border hairline"
                  style={{ background: CATEGORY_COLOR[live.category] }}
                />
                <div>
                  <div className="text-2xl font-semibold leading-none">
                    {live.category}
                  </div>
                  <div className="text-xs text-ink-mute capitalize">
                    {live.color_name}
                  </div>
                </div>
              </div>
            ) : (
              <div className="mt-1 text-sm text-ink-mute">{t("camera.none")}</div>
            )}
          </div>

          {live && (
            <div className="border-t hairline pt-3 space-y-2">
              <div className="text-[11px] uppercase tracking-[0.1em] text-ink-mute">
                {t("camera.mean")}
              </div>
              <div className="flex items-center gap-3">
                <span
                  className="inline-block w-8 h-8 border hairline"
                  style={{ background: live.mean_rgb_hex }}
                />
                <div className="num text-xs leading-tight">
                  <div>{live.mean_rgb_hex}</div>
                  <div className="text-ink-mute">
                    {t("camera.hsv")} {live.mean_hsv[0]} · {live.mean_hsv[1]} · {live.mean_hsv[2]}
                  </div>
                </div>
              </div>
              <div className="num text-[11px] text-ink-mute">
                {t("camera.dominant")}: H={live.hue} S={live.saturation} V={live.value}
              </div>
            </div>
          )}

          <div className="text-[11px] leading-relaxed text-ink-mute border-t hairline pt-3">
            {t("camera.roi")}
          </div>

          <div className="text-[11px] text-ink-mute space-y-1">
            <div>
              <span className="uppercase tracking-[0.1em]">
                {t("camera.mode")}
              </span>{" "}
              <span className="num">{stats?.camera_mode ?? "-"}</span>
            </div>
            <div>
              <span className="uppercase tracking-[0.1em]">
                {t("camera.inference")}
              </span>{" "}
              <span className="num">
                {stats ? `${stats.inference_ms.toFixed(1)} ms` : "-"}
              </span>
            </div>
            <div>
              <span className="uppercase tracking-[0.1em]">
                {t("camera.fps")}
              </span>{" "}
              <span className="num">
                {stats ? `${stats.display_fps.toFixed(1)}` : "-"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
