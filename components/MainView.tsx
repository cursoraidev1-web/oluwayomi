"use client";

import { useState, useEffect } from "react";
import { Upload, Scissors, Share2, Sparkles, Settings } from "lucide-react";
import { FileUploader } from "./FileUploader";
import { ProcessingStatus } from "./ProcessingStatus";
import { ResultsView, Clip } from "./ResultsView";
import { SettingsModal } from "./SettingsModal";
import { useFFmpeg } from "@/hooks/use-ffmpeg";
import { fetchFile } from "@ffmpeg/util";
import { analyzeVideoContent } from "@/utils/gemini";

export type AppState = "IDLE" | "ANALYZING" | "CLIPPING" | "DONE";

export default function MainView() {
  const [state, setState] = useState<AppState>("IDLE");
  const [logs, setLogs] = useState<string[]>([]);
  const [clips, setClips] = useState<Clip[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  
  const { ffmpeg, loaded: ffmpegLoaded } = useFFmpeg();

  const addLog = (msg: string) => setLogs(prev => [...prev, msg]);

  const handleFileSelect = (selectedFile: File) => {
    if (!ffmpegLoaded) {
      alert("Video engine is still loading. Please wait a moment.");
      return;
    }
    
    const apiKey = localStorage.getItem("gemini_api_key");
    if (!apiKey) {
      setShowSettings(true);
      addLog("Please configure your API Key first.");
      return;
    }

    startProcessing(selectedFile, apiKey);
  };

  const startProcessing = async (videoFile: File, apiKey: string) => {
    if (!ffmpeg) return;

    try {
      setState("ANALYZING");
      setLogs([]);
      addLog("Loading video into engine...");

      // 1. Write file to FFmpeg FS
      const inputName = "input.mp4";
      await ffmpeg.writeFile(inputName, await fetchFile(videoFile));
      addLog("Video loaded.");

      // 2. Extract Audio
      addLog("Extracting audio track...");
      const audioName = "audio.mp3";
      // Using -vn (no video), -ac 1 (mono), -ar 16000 (16khz) for compact audio
      await ffmpeg.exec(['-i', inputName, '-vn', '-ac', '1', '-ar', '16000', '-ab', '64k', audioName]);
      
      const audioData = await ffmpeg.readFile(audioName);
      const audioBlob = new Blob([audioData as any], { type: "audio/mp3" });
      const audioFile = new File([audioBlob], "audio.mp3", { type: "audio/mp3" });
      addLog("Audio extracted.");

      // 3. AI Analysis
      addLog("Sending to AI for highlight detection...");
      const analysis = await analyzeVideoContent(apiKey, audioFile);
      addLog(`AI identified ${analysis.length} highlights.`);

      // 4. Clipping
      setState("CLIPPING");
      const newClips: Clip[] = [];

      for (let i = 0; i < analysis.length; i++) {
        const item = analysis[i];
        const clipName = `clip_${i + 1}.mp4`;
        
        addLog(`Generating Clip ${i + 1}: ${item.caption.substring(0, 30)}...`);
        
        // Use -ss (start) and -to (end) with -c copy for speed, or re-encode if precise
        // -c copy is fast but inaccurate on start times. 
        // Re-encoding ensures precision but is slower. 
        // Let's try fast preset re-encoding for web compatibility.
        await ffmpeg.exec([
            '-i', inputName,
            '-ss', item.start.toString(),
            '-to', item.end.toString(),
            '-c:v', 'libx264', // Re-encode video
            '-preset', 'ultrafast', // Fast encoding
            '-c:a', 'copy', // Copy audio
            clipName
        ]);

        const clipData = await ffmpeg.readFile(clipName);
        const clipBlob = new Blob([clipData as any], { type: "video/mp4" });
        const clipUrl = URL.createObjectURL(clipBlob);

        newClips.push({
          id: (i + 1).toString(),
          url: clipUrl,
          filename: `autoclip_${i + 1}.mp4`,
          caption: item.caption,
          hashtags: item.hashtags,
          startTime: item.start,
          endTime: item.end,
          explanation: item.explanation
        });
      }

      setClips(newClips);
      setState("DONE");
      addLog("All processing complete!");

      // Cleanup
      await ffmpeg.deleteFile(inputName);
      await ffmpeg.deleteFile(audioName);
      for (let i = 0; i < analysis.length; i++) {
        await ffmpeg.deleteFile(`clip_${i+1}.mp4`);
      }

    } catch (error) {
      console.error(error);
      addLog(`Error: ${error instanceof Error ? error.message : "Unknown error"}`);
      setState("IDLE"); // Or ERROR state
    }
  };

  return (
    <div className="w-full space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${state === 'IDLE' ? 'bg-blue-500/20 text-blue-400' : 'bg-neutral-800 text-neutral-500'}`}>1. Upload</span>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${state === 'ANALYZING' ? 'bg-purple-500/20 text-purple-400' : 'bg-neutral-800 text-neutral-500'}`}>2. Analyze</span>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${state === 'CLIPPING' ? 'bg-orange-500/20 text-orange-400' : 'bg-neutral-800 text-neutral-500'}`}>3. Clip</span>
        </div>
        <button 
          onClick={() => setShowSettings(!showSettings)}
          className="p-2 hover:bg-neutral-800 rounded-full transition-colors flex items-center gap-2"
        >
            <span className="text-xs text-neutral-500 hidden sm:inline">Settings</span>
            <Settings size={20} className="text-neutral-400" />
        </button>
      </div>

      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}

      <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-6 min-h-[400px] flex flex-col justify-center items-center relative overflow-hidden">
        {state === "IDLE" && (
          <div className="w-full flex flex-col items-center">
             {!ffmpegLoaded && <p className="text-yellow-500 text-sm mb-4 animate-pulse">Initializing Video Engine...</p>}
             <FileUploader onFileSelect={handleFileSelect} />
          </div>
        )}

        {(state === "ANALYZING" || state === "CLIPPING") && (
            <ProcessingStatus state={state} logs={logs} />
        )}

        {state === "DONE" && (
            <ResultsView clips={clips} onReset={() => setState("IDLE")} />
        )}
      </div>
    </div>
  );
}
