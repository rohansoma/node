const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("handsfree", {
    getTrackingState: () => ipcRenderer.invoke("tracking:get-state"),
    startTracking: () => ipcRenderer.invoke("tracking:start"),
    stopTracking: () => ipcRenderer.invoke("tracking:stop"),
    onTrackingState: (callback) => {
        const listener = (_event, state) => callback(state);
        ipcRenderer.on("tracking:state", listener);
        return () => ipcRenderer.removeListener("tracking:state", listener);
    },
    onTrackingLog: (callback) => {
        const listener = (_event, log) => callback(log);
        ipcRenderer.on("tracking:log", listener);
        return () => ipcRenderer.removeListener("tracking:log", listener);
    },
});
