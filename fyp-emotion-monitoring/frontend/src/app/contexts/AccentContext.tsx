import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

export type AccentColor = "violet" | "green" | "blue" | "orange" | "red" | "amber";

interface AccentContextType {
  accent: AccentColor;
  setAccent: (color: AccentColor) => void;
}

const AccentContext = createContext<AccentContextType | undefined>(undefined);

export function AccentProvider({ children }: { children: ReactNode }) {
  const [accent, setAccentState] = useState<AccentColor>(
    () => (localStorage.getItem("accent-color") as AccentColor) || "violet"
  );

  const setAccent = (color: AccentColor) => {
    localStorage.setItem("accent-color", color);
    setAccentState(color);
  };

  useEffect(() => {
    document.documentElement.setAttribute("data-accent", accent);
  }, [accent]);

  return (
    <AccentContext.Provider value={{ accent, setAccent }}>
      {children}
    </AccentContext.Provider>
  );
}

export function useAccent() {
  const ctx = useContext(AccentContext);
  if (!ctx) throw new Error("useAccent must be used within AccentProvider");
  return ctx;
}
