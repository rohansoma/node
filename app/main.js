const { app, BrowserWindow } = require("electron");
const path = require("path");

function createWindow() {
    const win = new BrowserWindow({
        width: 400,
        height: 450,
        webPreferences: {
            preload: path.join(__dirname, "preload.js"),
        },
    });

    // Load Vite dev server
    win.loadURL("http://localhost:5173");

    // Optional: open dev tools
    // win.webContents.openDevTools();
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
