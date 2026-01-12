"use client";

import { useState, useRef, useEffect } from "react";
import { FFmpeg } from "@ffmpeg/ffmpeg";
import { toBlobURL } from "@ffmpeg/util";

export function useFFmpeg() {
  const [loaded, setLoaded] = useState(false);
  const ffmpegRef = useRef<FFmpeg | null>(null);
  const messageRef = useRef<string>("");

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    const baseURL = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/umd";
    const ffmpeg = new FFmpeg();
    ffmpegRef.current = ffmpeg;

    ffmpeg.on("log", ({ message }) => {
      messageRef.current = message;
      console.log(message);
    });

    try {
      // Load ffmpeg.wasm from CDN
      await ffmpeg.load({
        coreURL: await toBlobURL(`${baseURL}/ffmpeg-core.js`, "text/javascript"),
        wasmURL: await toBlobURL(`${baseURL}/ffmpeg-core.wasm`, "application/wasm"),
      });
      setLoaded(true);
    } catch (error) {
      console.error("Failed to load FFmpeg", error);
    }
  };

  return { ffmpeg: ffmpegRef.current, loaded };
}
