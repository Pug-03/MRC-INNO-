import { useI18n } from "../i18n/I18nProvider";

export function LanguageToggle() {
  const { lang, setLang, t } = useI18n();

  const btn = (value: "en" | "th", label: string) => (
    <button
      onClick={() => setLang(value)}
      className={
        "px-2.5 py-1 text-[11px] uppercase tracking-wider " +
        (lang === value
          ? "bg-ink text-paper"
          : "text-ink-mute hover:text-ink")
      }
    >
      {label}
    </button>
  );

  return (
    <div className="flex items-center border hairline">
      {btn("en", t("lang.en"))}
      {btn("th", t("lang.th"))}
    </div>
  );
}
