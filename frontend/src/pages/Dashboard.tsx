import { useEffect, useState } from "react";
import { CameraFeed } from "../components/CameraFeed";
import { CategoryPie } from "../components/CategoryPie";
import { TotalCount } from "../components/TotalCount";
import { EventLog } from "../components/EventLog";
import { SystemHealth } from "../components/SystemHealth";
import { Settings } from "../components/Settings";
import {
  DetectionEvent,
  getStats,
  StatsResponse,
  subscribeEvents,
} from "../api";

export function Dashboard() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [events, setEvents] = useState<DetectionEvent[]>([]);

  useEffect(() => {
    let alive = true;
    const refresh = async () => {
      try {
        const s = await getStats();
        if (!alive) return;
        setStats(s);
        setEvents(s.recent);
      } catch {
        /* ignore */
      }
    };
    refresh();
    const id = setInterval(refresh, 3000);
    const unsub = subscribeEvents((ev) => {
      setEvents((prev) => [ev, ...prev].slice(0, 50));
      setStats((prev) =>
        prev
          ? {
              ...prev,
              today: {
                ...prev.today,
                [ev.category]: (prev.today[ev.category] as number) + 1,
                total: prev.today.total + 1,
              },
            }
          : prev
      );
    });
    return () => {
      alive = false;
      clearInterval(id);
      unsub();
    };
  }, []);

  return (
    <div className="grid gap-5 lg:grid-cols-3">
      <div className="lg:col-span-2 grid gap-5">
        <CameraFeed />
        <div className="grid gap-5 md:grid-cols-2">
          <TotalCount totals={stats?.today ?? null} />
          <CategoryPie totals={stats?.today ?? null} />
        </div>
      </div>
      <div className="grid gap-5 content-start">
        <Settings
          onAfterReset={() => {
            setEvents([]);
            setStats((prev) =>
              prev
                ? {
                    ...prev,
                    today: { A: 0, B: 0, C: 0, D: 0, E: 0, total: 0, day: prev.today.day },
                    recent: [],
                  }
                : prev
            );
          }}
        />
        <SystemHealth />
        <EventLog events={events} totalToday={stats?.today.total ?? 0} />
      </div>
    </div>
  );
}
