const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("path");

const APP_ROOT = path.resolve(__dirname, "..");
const TRACKING_DIR = path.join(APP_ROOT, "Tracking");
const TRACKING_ENTRY = path.join(TRACKING_DIR, "main.py");

let mainWindow = null;
let trackingProcess = null;
let trackingState = {
    status: "stopped",
    python: null,
    pid: null,
    startedAt: null,
    lastExitCode: null,
    lastError: null,
    logs: [],
    telemetry: null,
};

function pushLog(message, stream = "stdout") {
    const line = String(message ?? "").trim();
    if (!line) {
        return;
    }

    trackingState.logs = [...trackingState.logs, { message: line, stream, at: Date.now() }].slice(-200);

    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send("tracking:log", trackingState.logs[trackingState.logs.length - 1]);
        mainWindow.webContents.send("tracking:state", trackingState);
    }
}

function handleTelemetryLine(line) {
    if (!line.startsWith("__HANDSFREE__")) {
        return false;
    }

    try {
        const payload = JSON.parse(line.slice("__HANDSFREE__".length));
        if (payload.type === "telemetry") {
            trackingState = {
                ...trackingState,
                telemetry: payload,
            };
            emitState();
        }
        return true;
    } catch (error) {
        pushLog(`Failed to parse telemetry: ${error.message}`, "stderr");
        return true;
    }
}

function attachOutput(stream, streamName) {
    let buffer = "";
    stream.on("data", (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split(/\r?\n/);
        buffer = lines.pop() ?? "";

        for (const rawLine of lines) {
            const line = rawLine.trim();
            if (!line) {
                continue;
            }
            if (!handleTelemetryLine(line)) {
                pushLog(line, streamName);
            }
        }
    });
}

function emitState() {
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send("tracking:state", trackingState);
    }
}

function getPythonCandidates() {
    const venvDir = path.join(APP_ROOT, ".venv");
    const candidates = process.platform === "win32"
        ? [
            path.join(venvDir, "Scripts", "python.exe"),
            "python",
            "py",
        ]
        : [
            path.join(venvDir, "bin", "python"),
            "python3",
            "python",
        ];

    return candidates;
}

function resolvePythonCommand() {
    for (const candidate of getPythonCandidates()) {
        if (candidate.includes(path.sep)) {
            if (fs.existsSync(candidate)) {
                return candidate;
            }
            continue;
        }

        return candidate;
    }

    return null;
}

function startTracking() {
    if (trackingProcess) {
        return trackingState;
    }

    if (!fs.existsSync(TRACKING_ENTRY)) {
        trackingState = {
            ...trackingState,
            status: "error",
            lastError: `Tracking entrypoint not found at ${TRACKING_ENTRY}`,
        };
        emitState();
        return trackingState;
    }

    const python = resolvePythonCommand();
    if (!python) {
        trackingState = {
            ...trackingState,
            status: "error",
            lastError: "Python was not found. Create .venv or install python3.",
        };
        emitState();
        return trackingState;
    }

    trackingState = {
        ...trackingState,
        status: "starting",
        python,
        pid: null,
        startedAt: Date.now(),
        lastExitCode: null,
        lastError: null,
        telemetry: null,
    };
    emitState();

    const args = python === "py" ? ["-3", "-u", TRACKING_ENTRY] : ["-u", TRACKING_ENTRY];
    trackingProcess = spawn(python, args, {
        cwd: TRACKING_DIR,
        env: {
            ...process.env,
            HANDSFREE_EMBEDDED: "1",
            PYTHONUNBUFFERED: "1",
        },
    });

    trackingState = {
        ...trackingState,
        status: "running",
        pid: trackingProcess.pid ?? null,
    };
    pushLog(`Started Tracking/main.py with ${python}`, "system");
    emitState();

    attachOutput(trackingProcess.stdout, "stdout");
    attachOutput(trackingProcess.stderr, "stderr");

    trackingProcess.on("error", (error) => {
        trackingState = {
            ...trackingState,
            status: "error",
            lastError: error.message,
        };
        pushLog(error.message, "stderr");
        trackingProcess = null;
        emitState();
    });

    trackingProcess.on("close", (code) => {
        trackingState = {
            ...trackingState,
            status: code === 0 ? "stopped" : "error",
            pid: null,
            lastExitCode: code,
            lastError: code === 0 ? null : `Tracking process exited with code ${code}`,
        };
        pushLog(`Tracking process exited with code ${code}`, "system");
        trackingProcess = null;
        emitState();
    });

    return trackingState;
}

function stopTracking() {
    if (!trackingProcess) {
        return trackingState;
    }

    trackingState = {
        ...trackingState,
        status: "stopping",
    };
    pushLog("Stopping Tracking/main.py", "system");
    emitState();

    trackingProcess.kill("SIGINT");
    return trackingState;
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 700,
        height: 750,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
            contextIsolation: true,
            nodeIntegration: false,
        },
    });

    // Load Vite dev server
    mainWindow.loadURL("http://localhost:5173");

    // Optional: open dev tools
    // win.webContents.openDevTools();
}

app.whenReady().then(() => {
    createWindow();
    startTracking();
});

ipcMain.handle("tracking:get-state", () => trackingState);
ipcMain.handle("tracking:start", () => startTracking());
ipcMain.handle("tracking:stop", () => stopTracking());

app.on("window-all-closed", () => {
    if (trackingProcess) {
        trackingProcess.kill("SIGINT");
    }
    if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
