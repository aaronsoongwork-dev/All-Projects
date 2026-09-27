import { useState, useEffect } from "react";
import { Link } from "react-router";
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Brain, Mic, Upload } from "lucide-react";
import { Button } from "./ui/button";
import { useUser } from "../contexts/UserContext";
import { getTimeBasedGreeting, getSessionQuote } from "../utils/userProfile";
import { useSessionStore } from "../utils/emotionEngine";
import type { Emotion } from "../utils/emotionEngine";

const EMOTION_COLORS: { [key in Emotion]: string } = {
    happy: "#c07c20",
    sad: "#1e5f8a",
    angry: "#b8312f",
    neutral: "#786c5c",
};

const serif = "'Playfair Display', Georgia, serif";
const sans = "'IBM Plex Sans', system-ui, sans-serif";

function SectionRule({ label }: { label: string }) {
    return (
        <div className="flex items-center gap-3 mb-5">
      <span
          className="text-xs tracking-[0.2em] uppercase text-muted-foreground"
          style={{ fontFamily: sans }}
      >
        — {label}
      </span>
            <div className="flex-1 border-t" style={{ borderColor: "var(--border)" }} />
        </div>
    );
}

function StatBlock({
                       label, value, sub,
                   }: { label: string; value: string | number; sub: string }) {
    return (
        <div className="border-l-2 pl-4 py-1" style={{ borderColor: "var(--border)" }}>
            <p className="text-xs tracking-[0.18em] uppercase text-muted-foreground mb-1.5" style={{ fontFamily: sans }}>
                {label}
            </p>
            <div
                className="text-3xl font-bold text-foreground leading-none mb-1.5"
                style={{ fontFamily: serif, letterSpacing: "-0.02em" }}
            >
                {value}
            </div>
            <p className="text-xs text-muted-foreground/75" style={{ fontFamily: sans }}>{sub}</p>
        </div>
    );
}

export function Dashboard() {
    const { user } = useUser();
    const sessions = useSessionStore();
    const [quote, setQuote] = useState<{ text: string; author: string } | null>(null);
    const [greeting] = useState(getTimeBasedGreeting());

    // getSessionQuote() now hits the backend (/api/quote) the first time it's
    // called each day, so it's async — fetch it in an effect rather than
    // calling it straight in useState, and render nothing in the quote slot
    // until it resolves rather than blocking the rest of the page
    useEffect(() => {
        let cancelled = false;
        getSessionQuote().then((q) => {
            if (!cancelled) setQuote(q);
        });
        return () => {
            cancelled = true;
        };
    }, []);

    const totalSessions = sessions.length;
    const totalDuration = sessions.reduce((sum, s) => sum + s.duration, 0);
    const avgConfidence =
        sessions.length > 0
            ? sessions.reduce((sum, s) => sum + s.summary.averageConfidence, 0) / sessions.length
            : 0;

    const emotionDistribution: { [key in Emotion]: number } = {
        happy: 0, sad: 0, angry: 0, neutral: 0,
    };
    sessions.forEach((session) => {
        Object.entries(session.summary.emotionDistribution).forEach(([emotion, value]) => {
            emotionDistribution[emotion as Emotion] += value;
        });
    });

    // Average across sessions, so this is a clean 0..1 fraction of "how much
    // each emotion shows up across all sessions"
    const sessionCount = sessions.length || 1;

    const pieData = Object.entries(emotionDistribution).filter(([, value]) => value > 0).map(([emotion, value]) => ({
        name: emotion.charAt(0).toUpperCase() + emotion.slice(1),
        value: value / sessionCount,
        color: EMOTION_COLORS[emotion as Emotion],
    }));

    const timelineData = sessions.slice(0, 10).reverse().map((session, index) => ({
        name: `S${index + 1}`,
        confidence: parseFloat((session.summary.averageConfidence * 100).toFixed(1)),
    }));

    const trendData = sessions.slice(0, 8).reverse().map((session, index) => {
        const data: any = { name: `S${index + 1}` };
        Object.entries(session.summary.emotionDistribution).forEach(([emotion, value]) => {
            data[emotion] = parseFloat((value * 100).toFixed(1));
        });
        return data;
    });

    const tooltipStyle = {
        background: "var(--card)",
        border: "1px solid var(--border)",
        borderRadius: 0,
        boxShadow: "none",
        color: "var(--card-foreground)",
        fontSize: 12,
        fontFamily: sans,
    };

    const axisStyle = { fontSize: 11, fill: "var(--muted-foreground)", fontFamily: sans };

    return (
        <div className="p-8 min-h-full bg-background">
          <div className="max-w-7xl mx-auto">

            {/* Masthead header */}
            <div className="border-b mb-8 pb-6" style={{ borderColor: "var(--border)" }}>
                <h1
                    className="font-bold text-foreground leading-tight mb-2"
                    style={{
                        fontFamily: serif,
                        fontSize: "clamp(2rem, 4vw, 3rem)",
                        letterSpacing: "-0.02em",
                    }}
                >
                    {greeting},&nbsp;
                    <em style={{ color: "var(--primary)", fontStyle: "italic" }}>{user.name}.</em>
                </h1>
                <p
                    className="text-sm text-muted-foreground max-w"
                    style={{ fontFamily: sans, fontWeight: 300, lineHeight: 1.6 }}
                >
                    Your emotion monitoring console is live and ready. Analysis is running in real time.
                </p>
            </div>

            {/* Status + quote row */}
            <div className="flex flex-wrap items-start mb-8">
                {quote && (
                    <div
                        className="flex-1 pl-5 italic text text-muted-foreground leading-relaxed min-w-[240px]"
                        style={{ fontFamily: serif, borderColor: "var(--border)" }}
                    >
                        "{quote.text}"
                        <span
                            className="not-italic ml-2 text-xs tracking-wider uppercase text-muted-foreground/60"
                            style={{ fontFamily: sans }}
                        >
              — {quote.author}
            </span>
                    </div>
                )}
            </div>

            {/* Quick actions */}
            <div className="mb-8">
                <SectionRule label="Quick Access" />
                <div className="flex flex-wrap gap-3">
                    <Link to="/live">
                        <Button
                            className="gap-2.5 text-xs font-semibold tracking-[0.12em] uppercase px-5 py-3"
                            style={{
                                fontFamily: sans,
                                backgroundColor: "var(--foreground)",
                                color: "var(--background)",
                                borderRadius: 0,
                                height: "auto",
                            }}
                        >
                            <Mic className="size-4" />
                            Start Live Analysis
                        </Button>
                    </Link>
                    <Link to="/upload">
                        <Button
                            variant="outline"
                            className="gap-2.5 text-xs font-semibold tracking-[0.12em] uppercase px-5 py-3"
                            style={{
                                fontFamily: sans,
                                borderColor: "var(--border)",
                                color: "var(--foreground)",
                                borderRadius: 0,
                                height: "auto",
                            }}
                        >
                            <Upload className="size-4" />
                            Upload Audio File
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Stats */}
            <div className="mb-8">
                <SectionRule label="Session Statistics" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <StatBlock label="Total Sessions" value={totalSessions} sub="All time" />
                    <StatBlock
                        label="Total Duration"
                        value={`${Math.round(totalDuration / 60)}m`}
                        sub="Minutes analyzed"
                    />
                    <StatBlock
                        label="Avg Confidence"
                        value={`${(avgConfidence * 100).toFixed(1)}%`}
                        sub="Model accuracy"
                    />
                </div>
            </div>

            {/* Charts */}
            {sessions.length === 0 ? (
                <div className="border py-20 text-center" style={{ borderColor: "var(--border)" }}>
                    <Brain
                        className="mx-auto mb-4 text-muted-foreground/40"
                        style={{ width: 40, height: 40 }}
                    />
                    <h3
                        className="text-xl font-bold text-foreground mb-2"
                        style={{ fontFamily: serif }}
                    >
                        No sessions recorded yet.
                    </h3>
                    <p
                        className="text-sm text-muted-foreground mb-6 max-w-xs mx-auto"
                        style={{ fontFamily: sans, fontWeight: 300 }}
                    >
                        Start a live analysis or upload an audio file to begin analysis.
                    </p>
                    <div className="flex gap-3 justify-center">
                        <Link to="/live">
                            <Button
                                style={{
                                    fontFamily: sans,
                                    fontSize: 12,
                                    letterSpacing: "0.1em",
                                    textTransform: "uppercase",
                                    backgroundColor: "var(--foreground)",
                                    color: "var(--background)",
                                    borderRadius: 0,
                                    fontWeight: 600,
                                }}
                            >
                                Start Live Analysis
                            </Button>
                        </Link>
                        <Link to="/upload">
                            <Button
                                variant="outline"
                                style={{
                                    fontFamily: sans,
                                    fontSize: 12,
                                    letterSpacing: "0.1em",
                                    textTransform: "uppercase",
                                    borderColor: "var(--border)",
                                    color: "var(--foreground)",
                                    borderRadius: 0,
                                    fontWeight: 600,
                                }}
                            >
                                Upload File
                            </Button>
                        </Link>
                    </div>
                </div>
            ) : (
                <div>
                    <SectionRule label="Visualisations" />
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Emotion Distribution */}
                        <div>
                            <p
                                className="text-xs tracking-[0.2em] uppercase text-muted-foreground mb-3"
                                style={{ fontFamily: sans }}
                            >
                                Emotion Distribution
                            </p>
                            <div className="border p-5" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
                                <ResponsiveContainer width="100%" height={240}>
                                    <PieChart margin={{ top: 8, right: 12, bottom: 8, left: 12 }}>
                                        <Pie
                                            data={pieData}
                                            cx="50%"
                                            cy="50%"
                                            outerRadius={80}
                                            dataKey="value"
                                        >
                                            {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                                        </Pie>
                                        <Legend
                                            verticalAlign="bottom"
                                            iconType="circle"
                                            wrapperStyle={{ fontSize: 10, fontFamily: sans, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted-foreground)" }}
                                        />
                                        <Tooltip
                                            contentStyle={tooltipStyle}
                                            formatter={(value: number) => `${(value * 100).toFixed(0)}%`}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Session Confidence */}
                        <div>
                            <p
                                className="text-xs tracking-[0.2em] uppercase text-muted-foreground mb-3"
                                style={{ fontFamily: sans }}
                            >
                                Session Confidence
                            </p>
                            <div className="border p-5" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
                                <ResponsiveContainer width="100%" height={240}>
                                    <BarChart data={timelineData} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
                                        <CartesianGrid vertical={false} strokeDasharray="2 2" stroke="var(--border)" />
                                        <XAxis dataKey="name" tick={axisStyle} />
                                        <YAxis domain={[0, 100]} tick={axisStyle} />
                                        <Tooltip contentStyle={tooltipStyle} />
                                        <Bar dataKey="confidence" fill="var(--primary)" radius={0} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        {/* Emotion Trends */}
                        <div className="lg:col-span-2">
                            <p
                                className="text-xs tracking-[0.2em] uppercase text-muted-foreground mb-3"
                                style={{ fontFamily: sans }}
                            >
                                Emotion Trends — Session Timeline
                            </p>
                            <div className="border p-5" style={{ borderColor: "var(--border)", backgroundColor: "var(--card)" }}>
                                <ResponsiveContainer width="100%" height={240}>
                                    <LineChart data={trendData} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
                                        <CartesianGrid vertical={false} strokeDasharray="2 2" stroke="var(--border)" />
                                        <XAxis dataKey="name" tick={axisStyle} />
                                        <YAxis domain={[0, 100]} tick={axisStyle} />
                                        <Tooltip contentStyle={tooltipStyle} />
                                        <Legend wrapperStyle={{ fontSize: 11, fontFamily: sans, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--muted-foreground)" }} />
                                        {(["happy", "sad", "angry", "neutral"] as Emotion[]).map((e) => (
                                            <Line key={e} type="monotone" dataKey={e} stroke={EMOTION_COLORS[e]} strokeWidth={1.5} dot={false} />
                                        ))}
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                </div>
            )}
          </div>
        </div>
    );
}
