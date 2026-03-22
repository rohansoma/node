import React, { useEffect, useMemo } from "react";

// ── helpers ──────────────────────────────────────────────────────────────────

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function formatLog(logs) {
    return logs
        .filter((l) => l.message && !l.message.startsWith("Started Tracking") && !l.message.startsWith("__HANDSFREE__"))
        .slice(-8);
}

// ── SpeedSelector ─────────────────────────────────────────────────────────────

function SpeedSelector({ label, value, onChange }) {
    return (
        <div className="flex items-center gap-3">
            <span className="text-[12px] text-[#8a8a8e] w-[90px] shrink-0">{label}</span>
            <div className="flex gap-1.5">
                {[1, 2, 3, 4, 5].map((n) => (
                    <button
                        key={n}
                        onClick={() => onChange(n)}
                        className={`w-8 h-7 rounded-md text-[12px] font-medium transition-colors border ${
                            value === n
                                ? "bg-[#007aff] text-white border-[#007aff]"
                                : "bg-[#f2f2f7] text-[#3a3a3c] border-[#d1d1d6] hover:bg-[#e5e5ea]"
                        }`}
                    >
                        {n}
                    </button>
                ))}
            </div>
        </div>
    );
}

// ── GazeMap ───────────────────────────────────────────────────────────────────

const MAP_W = 330;
const MAP_H = 200;

function GazeMap({ telemetry }) {
    const screenW = telemetry?.screen_w ?? 1;
    const screenH = telemetry?.screen_h ?? 1;

    const cx = telemetry
        ? clamp((telemetry.cursor_x / screenW) * MAP_W, 6, MAP_W - 6)
        : MAP_W / 2;
    const cy = telemetry
        ? clamp((telemetry.cursor_y / screenH) * MAP_H, 6, MAP_H - 6)
        : MAP_H / 2;

    const targetX = telemetry?.magnet_target
        ? clamp((telemetry.magnet_target.cx / screenW) * MAP_W, 6, MAP_W - 6)
        : null;
    const targetY = telemetry?.magnet_target
        ? clamp((telemetry.magnet_target.cy / screenH) * MAP_H, 6, MAP_H - 6)
        : null;

    const faceOk = telemetry?.face_found;

    return (
        <div
            className="relative rounded-xl overflow-hidden border border-[#2d2d30] bg-[#1c1c1e] select-none shrink-0"
            style={{ width: MAP_W, height: MAP_H }}
        >
            {/* grid — thirds */}
            {[1/3, 2/3].map((f) => (
                <React.Fragment key={f}>
                    <div className="absolute bg-[#ffffff0a]" style={{ left: f * MAP_W - 0.5, top: 0, width: 1, height: MAP_H }} />
                    <div className="absolute bg-[#ffffff0a]" style={{ top: f * MAP_H - 0.5, left: 0, height: 1, width: MAP_W }} />
                </React.Fragment>
            ))}
            {/* centre cross */}
            <div className="absolute bg-[#ffffff1a]" style={{ left: MAP_W / 2 - 0.5, top: 0, width: 1, height: MAP_H }} />
            <div className="absolute bg-[#ffffff1a]" style={{ top: MAP_H / 2 - 0.5, left: 0, height: 1, width: MAP_W }} />

            {/* magnet target diamond */}
            {targetX !== null && (
                <div
                    className="absolute border border-[#00c878]"
                    style={{ width: 10, height: 10, left: targetX - 5, top: targetY - 5, transform: "rotate(45deg)" }}
                />
            )}

            {/* cursor dot */}
            <div
                className={`absolute rounded-full transition-all duration-75 ${
                    faceOk ? "bg-[#00c8ff] shadow-[0_0_8px_#00c8ff88]" : "bg-[#48484a]"
                }`}
                style={{ width: 10, height: 10, left: cx - 5, top: cy - 5 }}
            />

            {/* face status */}
            <div className={`absolute bottom-2 left-2.5 text-[10px] ${faceOk ? "text-[#636366]" : "text-[#ff453a]"}`}>
                {faceOk ? "face detected" : "no face"}
            </div>
        </div>
    );
}

// ── LogPanel ──────────────────────────────────────────────────────────────────

function LogPanel({ logs }) {
    const lines = useMemo(() => formatLog(logs), [logs]);

    return (
        <div className="flex-1 rounded-xl border border-[#d1d1d6] bg-white overflow-hidden flex flex-col">
            <div className="px-3 pt-2.5 pb-2 border-b border-[#f2f2f7] shrink-0">
                <span className="text-[10px] font-semibold text-[#8a8a8e] uppercase tracking-widest">Log</span>
            </div>
            <div className="flex-1 overflow-hidden px-3 py-2 flex flex-col justify-end gap-0.5">
                {lines.length === 0 ? (
                    <span className="text-[11px] text-[#c7c7cc]">waiting…</span>
                ) : (
                    lines.map((l, i) => (
                        <div
                            key={i}
                            className={`text-[11px] leading-snug truncate ${
                                l.stream === "stderr" ? "text-[#ff453a]" : "text-[#3a3a3c]"
                            }`}
                        >
                            {l.message}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export default function Dashboard({ trackingState, controls }) {
    const isRunning = trackingState.status === "running" || trackingState.status === "starting";
    const settings  = trackingState.settings ?? { mouseSpeed: 3, scrollSpeed: 3 };

    // R key → recalibrate
    useEffect(() => {
        function onKey(e) {
            if (e.key === "r" || e.key === "R") {
                window.handsfree?.recalibrate();
            }
        }
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, []);

    return (
        <div className="flex flex-col h-full px-5 py-5 gap-4">

            {/* ── Header ──────────────────────────────────────────────────── */}
            <div className="flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                        trackingState.status === "running"  ? "bg-[#34c759]" :
                        trackingState.status === "error"    ? "bg-[#ff3b30]" :
                        trackingState.status === "starting" ||
                        trackingState.status === "stopping" ? "bg-[#ff9f0a]" :
                                                              "bg-[#8a8a8e]"
                    }`} />
                    <span className="text-[13px] font-medium text-[#3a3a3c] capitalize">
                        {trackingState.status}
                    </span>
                    {trackingState.pid && (
                        <span className="text-[12px] text-[#8a8a8e]">· PID {trackingState.pid}</span>
                    )}
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={controls.startTracking}
                        disabled={isRunning}
                        className="px-3.5 py-1.5 rounded-md text-[13px] font-medium bg-[#007aff] text-white disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        Start
                    </button>
                    <button
                        onClick={controls.stopTracking}
                        disabled={!isRunning}
                        className="px-3.5 py-1.5 rounded-md text-[13px] font-medium bg-[#e5e5ea] text-[#3a3a3c] disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                        Stop
                    </button>
                </div>
            </div>

            {/* ── Main body: two columns ───────────────────────────────────── */}
            <div className="flex gap-4">

                {/* Left column: gaze map + settings */}
                <div className="flex flex-col gap-3 shrink-0" style={{ width: MAP_W }}>
                    <GazeMap telemetry={trackingState.telemetry} />

                    {/* Settings */}
                    <div className="bg-white rounded-xl border border-[#d1d1d6] px-4 py-3.5 flex flex-col gap-3">
                        <SpeedSelector
                            label="Mouse Speed"
                            value={settings.mouseSpeed}
                            onChange={(n) => controls.updateSettings({ mouseSpeed: n })}
                        />
                        <div className="border-t border-[#f2f2f7]" />
                        <SpeedSelector
                            label="Scroll Speed"
                            value={settings.scrollSpeed}
                            onChange={(n) => controls.updateSettings({ scrollSpeed: n })}
                        />
                        <div className="border-t border-[#f2f2f7]" />
                        <button
                            onClick={() => window.handsfree?.recalibrate()}
                            className="text-left text-[12px] text-[#007aff] hover:text-[#005bb5] transition-colors"
                        >
                            Recalibrate
                        </button>
                    </div>
                </div>

                {/* Right column: log */}
                <LogPanel logs={trackingState.logs} />
            </div>

            {/* ── Error ───────────────────────────────────────────────────── */}
            {trackingState.lastError && (
                <div className="shrink-0 text-[12px] text-[#ff3b30] px-1">
                    {trackingState.lastError}
                </div>
            )}

        </div>
    );
}
