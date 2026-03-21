import React, { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Settings from "./pages/Settings";
import GeneralSettings from "./pages/GeneralSettings";

export default function App() {
    const [currentPath, setCurrentPath] = useState("dashboard");

    return (
        <div className="flex h-screen bg-[#f2f2f7] text-black overflow-hidden font-sans">
            <main className="flex-1 overflow-y-auto relative h-full">
                {currentPath === "general" && <GeneralSettings navigate={setCurrentPath} />}
                {currentPath === "settings" && <Settings navigate={setCurrentPath} />}
                {currentPath === "dashboard" && <Dashboard navigate={setCurrentPath} />}
            </main>
        </div>
    );
}
