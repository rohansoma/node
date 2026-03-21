import React from "react";

function formatStatus(status) {
    switch (status) {
        case "running":
            return "Running";
        case "starting":
            return "Starting";
        case "stopping":
            return "Stopping";
        case "error":
            return "Error";
        default:
            return "Stopped";
    }
}

export default function Dashboard({ navigate, trackingState, controls }) {
    const isRunning = trackingState.status === "running" || trackingState.status === "starting";
    const lastLog = trackingState.logs?.[trackingState.logs.length - 1];
    const telemetry = trackingState.telemetry;

    return (
        <div className="px-5 py-6 max-w-[800px] mx-auto font-sans">
            <h1 className="text-[26px] font-semibold mb-6 tracking-tight text-black">Welcome</h1>
            <div className="bg-[#ffffff] rounded-xl border border-[#e5e5ea] p-6 shadow-sm mb-6">
                <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                        <h2 className="text-[14px] font-medium mb-1.5 text-black">System Status</h2>
                        <p className="text-[#8a8a8e] text-[13px] mb-4">
                            The tracker and voice listener start automatically when the app opens.
                        </p>
                        <div className="flex flex-wrap items-center gap-3">
                            <div className="flex items-center gap-2 text-[13px] font-medium text-black/90 bg-[#f2f2f7] px-3 py-1.5 rounded-md border border-[#e5e5ea]">
                                <span
                                    className={`w-2 h-2 rounded-full ${
                                        trackingState.status === "running"
                                            ? "bg-[#34c759]"
                                            : trackingState.status === "error"
                                              ? "bg-[#ff3b30]"
                                              : "bg-[#8a8a8e]"
                                    }`}
                                />
                                {formatStatus(trackingState.status)}
                            </div>
                            {trackingState.pid && (
                                <div className="text-[12px] text-[#8a8a8e] bg-[#f2f2f7] px-3 py-1.5 rounded-md border border-[#e5e5ea]">
                                    PID {trackingState.pid}
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-3">
                        <div className="flex items-center gap-2">
                            <button
                                onClick={controls.startTracking}
                                disabled={isRunning}
                                className="px-3 py-1.5 rounded-md text-[13px] font-medium bg-[#007aff] text-white disabled:bg-[#b8d7ff] disabled:cursor-not-allowed"
                            >
                                Start
                            </button>
                            <button
                                onClick={controls.stopTracking}
                                disabled={!isRunning && trackingState.status !== "stopping"}
                                className="px-3 py-1.5 rounded-md text-[13px] font-medium bg-[#e5e5ea] text-black disabled:text-[#8a8a8e] disabled:cursor-not-allowed"
                            >
                                Stop
                            </button>
                        </div>
                        <TrackerMiniMap telemetry={telemetry} compact />
                    </div>
                </div>
                <p className="text-[#8a8a8e] text-[13px] mb-4">
                    Tracking/main.py runs in the background without opening the OpenCV debug window.
                </p>
                {trackingState.lastError && (
                    <p className="text-[#c1272d] text-[12px] mt-3">{trackingState.lastError}</p>
                )}
                {lastLog && (
                    <p className="mt-3 text-[12px] text-[#6e6e73] whitespace-pre-wrap break-words">
                        {lastLog.message}
                    </p>
                )}
            </div>

            <div className="flex flex-col gap-4">
                <button 
                    onClick={() => navigate('general')}
                    className="bg-[#ffffff] hover:bg-[#f2f2f7] transition-colors rounded-xl border border-[#e5e5ea] p-5 text-left flex flex-col items-start gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.05)] group"
                >
                    <span className="text-[#8a8a8e] mb-1 group-hover:text-[#007aff] transition-colors">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    </span>
                    <span className="text-[14px] font-medium text-black">General</span>
                    <span className="text-[#8a8a8e] text-[12px] leading-snug">System preferences, network, and general options.</span>
                </button>

                <button 
                    onClick={() => navigate('settings')}
                    className="bg-[#ffffff] hover:bg-[#f2f2f7] transition-colors rounded-xl border border-[#e5e5ea] p-5 text-left flex flex-col items-start gap-2 shadow-[0_1px_2px_rgba(0,0,0,0.05)] group"
                >
                    <span className="text-[#8a8a8e] mb-1 group-hover:text-[#007aff] transition-colors">
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="5" y="2" width="14" height="20" rx="7"></rect><path d="M12 6v4"></path></svg>
                    </span>
                    <span className="text-[14px] font-medium text-black">Pointer Control</span>
                    <span className="text-[#8a8a8e] text-[12px] leading-snug">Configure mouse and trackpad behavior.</span>
                </button>
            </div>
        </div>
    );
}

function TrackerMiniMap({ telemetry, compact = false }) {
    const mapWidth = compact ? 120 : 240;
    const mapHeight = compact ? 80 : 160;
    const screenW = telemetry?.screen_w ?? 1;
    const screenH = telemetry?.screen_h ?? 1;
    const cursorLeft = telemetry
        ? clamp((telemetry.cursor_x / screenW) * mapWidth, 6, mapWidth - 6)
        : mapWidth / 2;
    const cursorTop = telemetry
        ? clamp((telemetry.cursor_y / screenH) * mapHeight, 6, mapHeight - 6)
        : mapHeight / 2;
    const targetLeft = telemetry?.magnet_target
        ? clamp((telemetry.magnet_target.cx / screenW) * mapWidth, 6, mapWidth - 6)
        : null;
    const targetTop = telemetry?.magnet_target
        ? clamp((telemetry.magnet_target.cy / screenH) * mapHeight, 6, mapHeight - 6)
        : null;

    return (
        <div className={`rounded-xl border border-[#2d2d2f] bg-[#2a2a2d] ${compact ? "p-2" : "p-3"}`}>
            <div
                className="relative overflow-hidden rounded-lg border border-[#5a5a60] bg-[#28282b]"
                style={{ width: mapWidth, height: mapHeight }}
            >
                <div className="absolute inset-x-0 top-1/2 h-px bg-[#4a4a50]" />
                <div className="absolute inset-y-0 left-1/2 w-px bg-[#4a4a50]" />
                {targetLeft !== null && targetTop !== null && (
                    <div
                        className="absolute h-3 w-3 border border-[#00c878]"
                        style={{
                            left: targetLeft - 6,
                            top: targetTop - 6,
                            transform: "rotate(45deg)",
                        }}
                    />
                )}
                <div
                    className={`absolute ${compact ? "h-3 w-3 border" : "h-4 w-4 border-2"} rounded-full ${
                        telemetry?.face_found ? "border-[#00c8ff] bg-[#00c8ff]" : "border-[#8a8a8e] bg-[#8a8a8e]"
                    }`}
                    style={{
                        left: cursorLeft - (compact ? 6 : 8),
                        top: cursorTop - (compact ? 6 : 8),
                    }}
                />
            </div>
            {compact ? (
                <div className="mt-2 text-[11px] text-[#b7b7bc]">
                    {telemetry?.face_found ? "Face detected" : "Waiting for face"}
                </div>
            ) : (
                <div className="mt-3 flex flex-wrap gap-2 text-[12px] text-[#b7b7bc]">
                    <span className="rounded-md border border-[#3b3b40] bg-[#222225] px-2 py-1">
                        Cursor {Math.round(telemetry?.cursor_x ?? 0)}, {Math.round(telemetry?.cursor_y ?? 0)}
                    </span>
                    {telemetry?.magnet_target && (
                        <span className="rounded-md border border-[#3b3b40] bg-[#222225] px-2 py-1">
                            Target {Math.round(telemetry.magnet_target.cx)}, {Math.round(telemetry.magnet_target.cy)}
                        </span>
                    )}
                </div>
            )}
        </div>
    );
}

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}
