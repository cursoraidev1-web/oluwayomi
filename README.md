# AutoClip: Zero-Maintenance Video Clipper

AutoClip is a client-side web application that automatically extracts viral-worthy clips from long videos using AI.

## Features

- **No Server Costs:** Runs entirely in your browser using WebAssembly (FFmpeg.wasm).
- **Free AI:** Uses Google Gemini's free tier (Bring Your Own Key) for intelligent highlight detection.
- **Social Ready:** Generates captions and hashtags automatically.
- **Privacy:** Your video files never leave your device (only audio is sent to AI for analysis).

## How to Use

1. **Get an API Key:**
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Create a free API key.
   - Enter it in the AutoClip settings (gear icon).

2. **Upload a Video:**
   - Drag and drop an MP4 file.
   - Wait for the magic to happen.

3. **Share:**
   - Download the generated clips.
   - Copy the captions and hashtags.
   - Post to TikTok, Shorts, or Reels.

## Installation / Development

1. Clone the repo.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run locally:
   ```bash
   npm run dev
   ```

## Deployment (Zero Maintenance)

This app is built with Next.js and can be deployed for free on Vercel, Netlify, or GitHub Pages.

1. Push to GitHub.
2. Connect to Vercel.
3. Deploy!

## Tech Stack

- **Next.js** (React Framework)
- **FFmpeg.wasm** (In-browser video processing)
- **Google Gemini API** (Multimodal AI)
- **Tailwind CSS** (Styling)
