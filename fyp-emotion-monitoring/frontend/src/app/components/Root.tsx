import { useState, useEffect } from "react";
import { Outlet, Link, useLocation, useNavigate } from "react-router";
import {
    Activity, Mic, Upload, FileText, BarChart3, Settings,
    LogOut, User, Clock, ChevronLeft, ChevronRight,
} from "lucide-react";
import { useUser } from "../contexts/UserContext";
import { useAuth } from "../contexts/AuthContext";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";

const NAV_ITEMS = [
    { path: "/", label: "Dashboard", icon: Activity },
    { path: "/live", label: "Live Analysis", icon: Mic },
    { path: "/upload", label: "File Analysis", icon: Upload },
    { path: "/analytics", label: "Analytics", icon: BarChart3 },
    { path: "/reports", label: "Reports", icon: FileText },
];

export function Root() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user } = useUser();
    const { signOut } = useAuth();

    const [collapsed, setCollapsed] = useState(
        () => localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true"
    );

    const toggleCollapsed = () => {
        setCollapsed((prev) => {
            localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(!prev));
            return !prev;
        });
    };

    // Live Date and Time State
    const [currentTime, setCurrentTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setCurrentTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    const formattedDate = currentTime.toLocaleDateString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        year: "numeric",
    });

    const formattedTime = currentTime.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });

    const isActive = (path: string) =>
        path === "/"
            ? location.pathname === "/"
            : location.pathname.startsWith(path);

    return (
        <div className="flex h-screen bg-background">
            <aside
                className="flex-shrink-0 flex flex-col border-r transition-all duration-200"
                style={{
                    width: collapsed ? 72 : 256,
                    borderColor: "var(--sidebar-border)",
                    backgroundColor: "var(--sidebar)",
                }}
            >
                {/* Masthead */}
                <div
                    className={`pt-6 pb-4 border-b flex items-center ${collapsed ? "justify-center px-2" : "justify-between pl-6 pr-3"}`}
                    style={{ borderColor: "var(--sidebar-border)" }}
                >
                    {!collapsed && (
                        <div className="mb-1">
                            <span className="text-xs tracking-[0.2em] uppercase text-muted-foreground block mb-1.5" style={{ fontFamily: "'IBM Plex Sans', sans-serif" }}>
                                — Est. 2026
                            </span>
                            <div className="text-2xl font-bold leading-tight text-foreground" style={{ fontFamily: "'Playfair Display', Georgia, serif", letterSpacing: "-0.01em" }}>
                                Emotion<br />
                                <span className="italic" style={{ color: "var(--primary)" }}>Monitor</span>
                            </div>
                        </div>
                    )}
                    <button
                        onClick={toggleCollapsed}
                        className="p-1.5 rounded-md hover:bg-sidebar-accent/50 transition-colors flex-shrink-0"
                        title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {collapsed ? (
                            <ChevronRight style={{ width: 16, height: 16, color: "var(--muted-foreground)" }} />
                        ) : (
                            <ChevronLeft style={{ width: 16, height: 16, color: "var(--muted-foreground)" }} />
                        )}
                    </button>
                </div>

                {!collapsed && (
                    <div className="pb-0">
                        <p className="px-6 py-3 text-xs text-muted-foreground tracking-[0.08em] uppercase font-semibold leading-4">
                            <span className="block">Fusion Model ·</span>
                            <span className="block">Powered Analysis</span>
                        </p>
                        <div className="border-y px-6 py-3 flex items-center justify-between gap-2 text-[11px] text-muted-foreground font-mono" style={{ borderColor: "var(--sidebar-border)" }}>
                            <span className="flex items-center gap-1.5 font-medium">
                                <Clock className="size-3 text-primary" />
                                {formattedTime}
                            </span>
                            <span className="text-[10px] uppercase tracking-tight opacity-80">{formattedDate}</span>
                        </div>
                    </div>
                )}

                {/* Navigation */}
                <nav
                    className="flex-1 px-2 pt-5 pb-6 space-y-1 overflow-y-auto"
                >
                    {NAV_ITEMS.map((item) => {
                        const Icon = item.icon;
                        const active = isActive(item.path);
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                title={collapsed ? item.label : undefined}
                                className={`flex items-center gap-3 py-2.5 text-xs tracking-wide transition-colors relative group rounded-md hover:bg-sidebar-accent/50 ${collapsed ? "justify-center px-2" : "px-3"}`}
                                style={{
                                    color: active ? "var(--foreground)" : "var(--muted-foreground)",
                                    fontFamily: "'IBM Plex Sans', sans-serif",
                                    fontWeight: active ? 600 : 500,
                                    letterSpacing: "0.05em",
                                    textTransform: "uppercase",
                                }}
                            >
                                {active && (
                                    <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r" style={{ backgroundColor: "var(--primary)" }} />
                                )}
                                <Icon
                                    className="flex-shrink-0"
                                    style={{
                                        width: 16, height: 16,
                                        color: active ? "var(--primary)" : "var(--muted-foreground)",
                                        opacity: active ? 1 : 0.7,
                                    }}
                                />
                                {!collapsed && <span>{item.label}</span>}
                            </Link>
                        );
                    })}
                </nav>

                {/* User footer */}
                <div className={`border-t py-4 space-y-1 ${collapsed ? "px-2" : "px-4"}`} style={{ borderColor: "var(--sidebar-border)" }}>
                    <Link
                        to="/profile"
                        title={collapsed ? (user?.name || "Profile") : undefined}
                        className={`flex items-center gap-3 py-2 rounded-md transition-colors hover:bg-sidebar-accent/50 ${collapsed ? "justify-center px-2" : "px-2"}`}
                        style={{ color: location.pathname === "/profile" ? "var(--foreground)" : "var(--muted-foreground)", fontFamily: "'IBM Plex Sans', sans-serif" }}
                    >
                        <Avatar className="size-7">
                            <AvatarImage src={user?.avatar} />
                            <AvatarFallback className="text-xs font-bold" style={{ backgroundColor: "var(--accent)", color: "var(--foreground)" }}>
                                {user?.name?.charAt(0).toUpperCase() || "U"}
                            </AvatarFallback>
                        </Avatar>
                        {!collapsed && (
                            <>
                                <div className="flex-1 min-w-0">
                                    <div className="text-xs uppercase tracking-wider truncate font-semibold">{user?.name || "User"}</div>
                                </div>
                                <User style={{ width: 14, height: 14, opacity: 0.5 }} />
                            </>
                        )}
                    </Link>

                    <Link
                        to="/settings"
                        title={collapsed ? "Settings" : undefined}
                        className={`flex items-center gap-3 py-2 rounded-md transition-colors hover:bg-sidebar-accent/50 ${collapsed ? "justify-center px-2" : "px-2"}`}
                        style={{ color: location.pathname === "/settings" ? "var(--foreground)" : "var(--muted-foreground)", fontFamily: "'IBM Plex Sans', sans-serif" }}
                    >
                        <Settings style={{ width: 14, height: 14, opacity: 0.7 }} />
                        {!collapsed && <span className="text-xs tracking-wider uppercase font-medium" style={{ fontFamily: "'IBM Plex Sans', sans-serif" }}>Settings</span>}
                    </Link>

                    <button
                        onClick={async () => { await signOut(); navigate("/login"); }}
                        title={collapsed ? "Sign out" : undefined}
                        className={`flex items-center gap-3 py-2 rounded-md text-xs font-medium uppercase tracking-wider text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground transition-all ${collapsed ? "justify-center px-2 w-full" : "px-2 w-full text-left"}`}
                    >
                        <LogOut style={{ width: 14, height: 14 }} />
                        {!collapsed && <span>Sign out</span>}
                    </button>
                </div>
            </aside>

            <main className="flex-1 overflow-auto bg-background">
                <Outlet />
            </main>
        </div>
    );
}
