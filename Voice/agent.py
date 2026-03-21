"""
Voice/agent.py — Gemini-powered voice command agent.

Architecture:
  - Uses google-genai SDK with manual function-calling control.
  - Runs an agentic loop: Gemini may call multiple tools in sequence before
    returning a final text response (e.g. get_chrome_tabs → switch_chrome_tab).
  - Maintains a rolling conversation history across commands so the model
    remembers context: "do it again", "now search for the same thing", etc.
  - History is trimmed to MAX_HISTORY_TURNS to stay within context limits.

Adding a new command:
  1. Write the function in commands.py.
  2. Import it here and add it to TOOLS.
"""

from __future__ import annotations

from google import genai
from google.genai import types

from .commands import (
    open_website,
    search_web,
    navigate_and_search,
    find_on_page,
    wait,
    open_application,
    type_text,
    press_keys,
    recalibrate,
    get_chrome_tabs,
    switch_chrome_tab,
    get_tracker_config,
    change_tracker_config,
)


# ── Tool registry ─────────────────────────────────────────────────────────────
# Import and list every command function here.  The SDK auto-generates JSON
# schemas from type annotations + docstrings, so no extra boilerplate needed.

TOOLS: list = [
    open_website,
    search_web,
    navigate_and_search,
    find_on_page,
    wait,
    open_application,
    type_text,
    press_keys,
    recalibrate,
    get_chrome_tabs,
    switch_chrome_tab,
    get_tracker_config,
    change_tracker_config,
]

_TOOL_MAP: dict[str, object] = {fn.__name__: fn for fn in TOOLS}


# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM = """
You are a concise voice command assistant for a head-tracking accessibility mouse controller.
The user controls their computer entirely with head movements, so precise, fast execution of voice commands is critical.

Behaviour rules:
- Always take action immediately — do not ask clarifying questions unless truly ambiguous.
- Keep responses to 1–2 short sentences; they are printed to a terminal, not spoken aloud.
- When the user says "do it again", "repeat that", or similar — look at conversation history and replay the exact same function call(s).
- When switching browser tabs: always call get_chrome_tabs first, then switch_chrome_tab with the best match.
- After completing an action, confirm it in one sentence (e.g. "Done — opened Spotify.").

Multi-step command rules:
- If a command requires several actions, call the functions one after another in the same response turn.
- "Go to X and search Y" or "search Y on X" → call navigate_and_search(site, query). Never open_website + wait + type for site searches.
- "Go to X and do Y" where Y is NOT a search (e.g. "go to GitHub and press enter") → open_website, then wait(2), then the next action.
- "Open X, search Y, and press enter" → navigate_and_search(X, Y), then press_keys("enter").
- "Find X on this page" or "search for X here" → find_on_page(X).
- "Type X and press enter" → type_text(X), then press_keys("enter").
- "Select all and copy" → press_keys("cmd+a"), then press_keys("cmd+c").
- "Undo" → press_keys("cmd+z"). "Redo" → press_keys("cmd+shift+z").
- "Save" → press_keys("cmd+s"). "Close tab" → press_keys("cmd+w"). "New tab" → press_keys("cmd+t").
- Always use wait() when a page needs time to load before the next interaction.
""".strip()


# ── Agent ─────────────────────────────────────────────────────────────────────

class VoiceAgent:
    """
    Stateful Gemini agent that retains conversation history across calls.

    Usage:
        agent = VoiceAgent(cfg)
        reply = agent.process("open youtube")
        print(reply)   # "Done — opened YouTube."
    """

    def __init__(self, cfg) -> None:
        if not cfg.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set.\n"
                "  export GEMINI_API_KEY='your_key'  or edit Voice/config.py"
            )

        self._cfg    = cfg
        self._client = genai.Client(api_key=cfg.GEMINI_API_KEY)
        self._model  = cfg.GEMINI_MODEL

        # GenerateContentConfig is reused for every send; tools are fixed.
        self._gen_cfg = types.GenerateContentConfig(
            system_instruction=_SYSTEM,
            tools=TOOLS,
            # Disable auto-execution so we control the loop and see each step.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )

        # Start a chat session with empty history.
        self._chat = self._client.chats.create(
            model=self._model,
            config=self._gen_cfg,
        )

    # ── Public ────────────────────────────────────────────────────────────────

    def process(self, text: str) -> str:
        """
        Process a transcribed voice command and return the assistant's reply.

        Runs the agentic function-call loop until Gemini returns a plain text
        response with no further tool calls.
        """
        response = self._chat.send_message(text)

        # ── Agentic loop ──────────────────────────────────────────────────────
        # Gemini may call tools multiple times before giving a final answer
        # (e.g. first get_chrome_tabs, then switch_chrome_tab).
        while response.function_calls:
            result_parts: list[types.Part] = []

            for fc in response.function_calls:
                fn = _TOOL_MAP.get(fc.name)
                if fn is None:
                    result = f"Unknown function: {fc.name}"
                else:
                    try:
                        result = fn(**fc.args)
                    except Exception as exc:
                        result = f"Error in {fc.name}: {exc}"

                args_str = ", ".join(f"{v!r}" for v in fc.args.values())
                print(f"   {fc.name}({args_str})")

                result_parts.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={"result": result},
                    )
                )

            # Return all function results to Gemini in a single turn.
            response = self._chat.send_message(result_parts)

        # ── Trim history ──────────────────────────────────────────────────────
        self._trim_history()

        return (response.text or "").strip()

    # ── Private ───────────────────────────────────────────────────────────────

    def _trim_history(self) -> None:
        """
        Keep the chat history within MAX_HISTORY_TURNS turns.

        Each "turn" is roughly 2 Content items (user + model), but function-
        call turns add more.  We use 6× as a conservative multiplier.
        When the limit is exceeded, a new chat is created seeded with the most
        recent slice of history.
        """
        max_items = self._cfg.MAX_HISTORY_TURNS * 6
        history   = self._chat.get_history()

        if len(history) > max_items:
            trimmed   = history[-max_items:]
            self._chat = self._client.chats.create(
                model=self._model,
                config=self._gen_cfg,
                history=trimmed,
            )
