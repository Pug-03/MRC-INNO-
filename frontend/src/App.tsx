import { NavLink, Route, Routes } from "react-router-dom";
import { Dashboard } from "./pages/Dashboard";
import { HistoryPage } from "./pages/History";
import { useI18n } from "./i18n/I18nProvider";
import { LanguageToggle } from "./components/LanguageToggle";
import { ThemeToggle } from "./components/ThemeToggle";
import { Clock } from "./components/Clock";
import { Icon } from "./components/Icon";

export default function App() {
  const { t } = useI18n();

  const navClass = ({ isActive }: { isActive: boolean }) =>
    "flex items-center gap-1.5 text-[11px] uppercase tracking-wider px-2.5 py-1 border hairline " +
    (isActive ? "bg-ink text-paper border-ink" : "text-ink-mute hover:text-ink");

  return (
    <div className="min-h-full p-3 sm:p-5">
      <div className="min-h-[calc(100vh-24px)] sm:min-h-[calc(100vh-40px)] max-w-[1280px] mx-auto border-2 border-frame bg-paper px-4 sm:px-6 py-5">
      <header className="flex flex-wrap gap-x-4 gap-y-3 items-center justify-between border-b hairline pb-4 mb-6">
        <div>
          <div className="text-[11px] uppercase tracking-[0.15em] text-ink-mute">
            {t("app.subtitle")}
          </div>
          <h1 className="text-xl font-semibold tracking-tight">
            {t("app.title")}
          </h1>
        </div>
        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto justify-end">
          <nav className="flex gap-2">
            <NavLink to="/" end className={navClass}>
              <Icon name="dashboard" size={14} />
              {t("nav.dashboard")}
            </NavLink>
            <NavLink to="/history" className={navClass}>
              <Icon name="calendar" size={14} />
              {t("nav.history")}
            </NavLink>
          </nav>
          <ThemeToggle />
          <LanguageToggle />
          <Clock />
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>
      </div>
    </div>
  );
}
