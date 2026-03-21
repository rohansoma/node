import React, { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";
import GeneralSettings from "./pages/GeneralSettings";

export default function App() {
    const [currentPath, setCurrentPath] = useState("dashboard");
    const [trackingState, setTrackingState] = useState({
        status: "stopped",
        python: null,
        pid: null,
        startedAt: null,
        lastExitCode: null,
        lastError: null,
        logs: [],
        telemetry: null,
    });

    useEffect(() => {
        if (!window.handsfree) {
            return undefined;
        }

        window.handsfree.getTrackingState().then(setTrackingState);

        const unsubscribeState = window.handsfree.onTrackingState((nextState) => {
            setTrackingState(nextState);
        });

        const unsubscribeLog = window.handsfree.onTrackingLog((nextLog) => {
            setTrackingState((current) => ({
                ...current,
                logs: [...current.logs, nextLog].slice(-200),
            }));
        });

        return () => {
            unsubscribeState?.();
            unsubscribeLog?.();
        };
    }, []);

    const controls = {
        startTracking: () => window.handsfree?.startTracking(),
        stopTracking: () => window.handsfree?.stopTracking(),
    };

    return (
        <div className="flex h-screen bg-[#f2f2f7] text-black overflow-hidden font-sans">
            <main className="flex-1 overflow-y-auto relative h-full">
                {currentPath === "general" && <GeneralSettings navigate={setCurrentPath} />}
                {currentPath === "settings" && (
                    <Settings
                        navigate={setCurrentPath}
                        trackingState={trackingState}
                        controls={controls}
                    />
                )}
                {currentPath === "dashboard" && (
                    <Dashboard
                        navigate={setCurrentPath}
                        trackingState={trackingState}
                        controls={controls}
                    />
                )}
            </main>
        </div>
    );
}
