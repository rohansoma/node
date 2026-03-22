# Node

Node is a hands-free desktop control. It combines head tracking, blink gestures, and voice commands so a user can move the cursor, click, scroll, and trigger actions without relying on a traditional mouse and keyboard.

## What It Does

- Moves the cursor using head movement
- Triggers left click with a double blink
- Toggles scroll mode with a triple blink
- Runs voice commands through a Gemini-powered assistant
- Shows live tracking state, cursor position, and logs in a desktop UI

## Project Structure

- [Tracking](https://github.com/rohansoma/node/tree/main/Tracking): Python tracking engine for webcam input, head pose, blink detection, cursor movement, and scrolling
- [Voice](https://github.com/rohansoma/node/tree/main/Voice): Voice-command system, wake-word flow, tool execution, and Gemini agent integration
- [app](https://github.com/rohansoma/node/tree/main/app): Electron + React desktop app and landing page

## How It Works

The tracking system uses the webcam to estimate head pose and facial landmarks in real time. Yaw and pitch are mapped to an on-screen cursor, blink gestures are interpreted as click or scroll-toggle actions, and cursor magnetism helps pull the pointer toward likely UI targets.

In parallel, the voice layer listens for speech, transcribes the command, checks for the wake phrase, and sends the command into a Gemini-based tool-calling agent. That agent can open apps, search the web, press keys, adjust tracker settings, and carry context across turns.

The desktop app wraps everything into a single interface with live status, speed controls, recalibration, and logs.

## How We Built It

We built Node as a hybrid desktop system with an Electron frontend and a Python tracking backend.

The desktop UI was built to manage the experience from one place, while the tracking engine handles computer-vision and input control in real time. MediaPipe is used to estimate head pose and facial landmarks, OpenCV processes the webcam feed, and custom logic maps yaw, pitch, and eye aspect ratio into cursor movement and click gestures.

On the voice side, the app listens for a wake phrase, transcribes speech, and routes commands through an LLM-based Model Context Protocol (MCP) agent flow. The LLM is able to convert natural language to function calls that allow your laptop to complete tasks from opening apps/tabs, searching websites, and even control common key binds. Through MCP, these commands can be chained to allow for complex computer actions.

## Running the Project

### Prerequisites

- Python 3
- Node.js and npm
- Webcam access
- Accessibility permission for cursor and keyboard control
- Microphone access for voice commands

### Python Setup

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the repo root with:

```bash
ELEVENLABS_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

Voice features will stay disabled if the required keys are missing.

### Desktop App Setup

From [app](/Users/nathank/repos/handsfree/app):

```bash
npm install
npm run start
```

This starts the Vite dev server and launches the Electron app.

### Landing Page

To run just the landing page:

```bash
cd /Users/nathank/repos/handsfree/app
npm run dev
```

Then open [http://localhost:5173/landing/](http://localhost:5173/landing/)

## Controls

- Move head left or right: move cursor horizontally
- Move head up or down: move cursor vertically
- Double blink: left click
- Triple blink: toggle scroll mode on or off
- Voice command to recalibrate tracking
- Stop button to stop the software
## Adjustable Settings

The app currently supports:

- Mouse speed
- Scroll speed
- Recalibration
- Scroll-mode toggling

Runtime tracking settings are stored in [Tracking/config.runtime.json](/Users/nathank/repos/handsfree/Tracking/config.runtime.json).

## Technologies Used

### Frontend and Desktop

- React
- Vite
- Electron
- Tailwind CSS

### Computer Vision and Input

- OpenCV
- MediaPipe
- NumPy
- Pynput

### Voice and AI

- Google GenAI SDK
- Gemini
- ElevenLabs speech-to-text workflow
- SoundDevice
- Requests

## Next Steps

- More MCP functons
- Ability to rebind keystrokes (e.g. change from double blink to head nod for click)
- Packaging and cross compatibility
- Ability to autofill details (ex. credit card details, emails, etc)
