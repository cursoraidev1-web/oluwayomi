"use client";

import { Loader2, Terminal } from "lucide-react";
import { useEffect, useRef } from "react";

interface ProcessingStatusProps {
  state: "ANALYZING" | "CLIPPING";
  logs: string[];
}

export function ProcessingStatus({ state, logs }: ProcessingStatusProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="flex flex-col items-center w-full max-w-lg">
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-blue-500 blur-xl opacity-20 rounded-full animate-pulse"></div>
        <Loader2 className="w-16 h-16 text-blue-500 animate-spin relative z-10" />
      </div>

      <h3 className="text-xl font-bold mb-2">
        {state === "ANALYZING" ? "Analyzing Content..." : "Generating Clips..."}
      </h3>
      <p className="text-neutral-400 mb-6 text-center">
        {state === "ANALYZING" 
          ? "AI is watching your video to find viral moments." 
          : "Cutting and formatting clips for social media."}
      </p>

      <div className="w-full bg-neutral-950 rounded-lg border border-neutral-800 p-4 font-mono text-xs text-neutral-400 h-48 overflow-hidden flex flex-col">
        <div className="flex items-center gap-2 border-b border-neutral-800 pb-2 mb-2">
          <Terminal size={12} />
          <span>Processing Logs</span>
        </div>
        <div ref={scrollRef} className="overflow-y-auto flex-1 space-y-1">
          {logs.map((log, i) => (
            <div key={i} className="break-words">
              <span className="text-neutral-600 mr-2">{`>`}</span>
              {log}
            </div>
          ))}
          <div className="animate-pulse">_</div>
        </div>
      </div>
    </div>
  );
}
