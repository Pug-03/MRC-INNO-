import { createContext, useContext, useEffect, useMemo, useState } from "react";
import en, { TranslationKey } from "./en";
import th from "./th";

type Lang = "en" | "th";

interface Ctx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (k: TranslationKey) => string;
}

const I18nContext = createContext<Ctx | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    const saved = localStorage.getItem("lang");
    return saved === "th" ? "th" : "en";
  });

  useEffect(() => {
    localStorage.setItem("lang", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<Ctx>(() => {
    const dict = lang === "th" ? th : en;
    return {
      lang,
      setLang,
      t: (k) => dict[k] ?? k,
    };
  }, [lang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const v = useContext(I18nContext);
  if (!v) throw new Error("useI18n outside provider");
  return v;
}
