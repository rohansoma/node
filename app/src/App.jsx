import React, { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";

export default function App() {
    const [trackingState, setTrackingState] = useState({
        status: "stopped",
        python: null,
        pid: null,
        startedAt: null,
        lastExitCode: null,
        lastError: null,
        logs: [],
        telemetry: null,
        settings: { mouseSpeed: 3, scrollSpeed: 3 },
    });

    useEffect(() => {
        if (!window.handsfree) return undefined;

        window.handsfree.getTrackingState().then(setTrackingState);

        const unsubState = window.handsfree.onTrackingState(setTrackingState);
        const unsubLog = window.handsfree.onTrackingLog((nextLog) => {
            setTrackingState((cur) => ({
                ...cur,
                logs: [...cur.logs, nextLog].slice(-100),
            }));
        });

        return () => { unsubState?.(); unsubLog?.(); };
    }, []);

    const controls = {
        startTracking:  () => window.handsfree?.startTracking(),
        stopTracking:   () => window.handsfree?.stopTracking(),
        updateSettings: (updates) => window.handsfree?.updateSettings(updates),
    };

    return (
        <div className="h-screen bg-[#f2f2f7] text-black overflow-hidden font-sans">
            <Dashboard trackingState={trackingState} controls={controls} />
        </div>
    );
}
