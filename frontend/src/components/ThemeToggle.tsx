import { useTheme } from "../theme/ThemeProvider";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="flex items-center border hairline w-[58px] h-[28px] p-0.5 relative text-ink-mute hover:text-ink"
    >
      <span
        className={
          "absolute top-0.5 h-[22px] w-[26px] bg-ink transition-transform " +
          (isDark ? "translate-x-[26px]" : "translate-x-0")
        }
      />
      <span
        className={
          "relative z-10 flex-1 flex items-center justify-center " +
          (isDark ? "text-ink-mute" : "text-paper")
        }
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4l1.4-1.4M17 7l1.4-1.4" strokeLinecap="round" />
        </svg>
      </span>
      <span
        className={
          "relative z-10 flex-1 flex items-center justify-center " +
          (isDark ? "text-paper" : "text-ink-mute")
        }
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" />
        </svg>
      </span>
    </button>
  );
}
