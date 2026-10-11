import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

const NAV = [
  { to: "/executive", label: "Executive overview" },
  { to: "/attrition", label: "Attrition" },
  { to: "/departments", label: "Departments" },
  { to: "/compensation", label: "Compensation" },
  { to: "/tenure", label: "Tenure" },
  { to: "/risk", label: "Risk segments" },
  { to: "/method", label: "Data & method" },
];

type Theme = "system" | "light" | "dark";

function readTheme(): Theme {
  try {
    const t = localStorage.getItem("workforce-intel-theme");
    return t === "light" || t === "dark" ? t : "system";
  } catch {
    return "system";
  }
}

function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readTheme);
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("workforce-intel-theme", theme);
    } catch {
      /* storage unavailable: the preference lasts for this page view */
    }
  }, [theme]);
  const next: Record<Theme, Theme> = {
    system: "light",
    light: "dark",
    dark: "system",
  };
  return (
    <button
      className="btn ghost"
      type="button"
      onClick={() => setTheme(next[theme])}
      aria-label={`Theme: ${theme}. Switch to ${next[theme]}`}
    >
      Theme: {theme}
    </button>
  );
}

export function Logo() {
  return (
    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
      <circle cx="5" cy="5" r="2" />
      <circle cx="11" cy="5" r="2" />
      <path d="M1.5 13c0-2 1.6-3.5 3.5-3.5S8.5 11 8.5 13M7.5 13c0-2 1.6-3.5 3.5-3.5s3.5 1.5 3.5 3.5" strokeLinecap="round" />
    </svg>
  );
}

export function Layout() {
  const location = useLocation();
  useEffect(() => {
    document.getElementById("main")?.focus({ preventScroll: true });
  }, [location.pathname]);
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="topbar">
        <div className="topbar-inner">
          <div className="topbar-row">
            <NavLink
              to="/executive"
              className="brand"
              aria-label="Workforce Intelligence, executive overview"
            >
              <span className="brand-mark">
                <Logo />
              </span>
              <span>
                <span className="brand-name">Workforce Intelligence</span>
                <br />
                <span className="brand-sub">IBM HR attrition data · fictional, 1,470 employees</span>
              </span>
            </NavLink>
            <span className="deployment">Associations only</span>
            <ThemeToggle />
          </div>
          <nav className="tabs" aria-label="Sections">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                className={({ isActive }) => (isActive ? "active" : "")}
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main id="main" className="main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
