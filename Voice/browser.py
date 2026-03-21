import subprocess
from dataclasses import dataclass

@dataclass
class Tab:
    window: int
    index: int
    title: str
    url: str

    def __str__(self):
        return f"[W{self.window}·T{self.index}] {self.title}"

def _osascript(script: str) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=6)
    return r.stdout.strip()

def get_tabs() -> list[Tab]:
    raw = _osascript("""
tell application "Google Chrome"
    set out to ""
    set wi to 0
    repeat with w in windows
        set wi to wi + 1
        set ti to 0
        repeat with t in tabs of w
            set ti to ti + 1
            set out to out & wi & "|" & ti & "|" & (title of t) & "|" & (URL of t) & "\n"
        end repeat
    end repeat
    return out
end tell""")
    tabs = []
    for line in raw.splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            try:
                tabs.append(Tab(int(parts[0]), int(parts[1]), parts[2], parts[3]))
            except ValueError:
                pass
    return tabs

def switch_tab(tab: Tab) -> bool:
    try:
        _osascript(f"""
tell application "Google Chrome"
    set active tab index of window {tab.window} to {tab.index}
    set index of window {tab.window} to 1
    activate
end tell""")
        return True
    except Exception:
        return False
