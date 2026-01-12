"use client";

import { Download, Share2, RefreshCw, Copy, Check } from "lucide-react";
import { useState } from "react";

export interface Clip {
  id: string;
  url: string;
  filename: string;
  caption: string;
  hashtags: string[];
  startTime: number;
  endTime: number;
  explanation: string;
}

interface ResultsViewProps {
  clips: Clip[];
  onReset: () => void;
}

export function ResultsView({ clips, onReset }: ResultsViewProps) {
  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Ready to Post ✨</h2>
        <button 
          onClick={onReset}
          className="flex items-center gap-2 text-sm text-neutral-400 hover:text-white transition-colors"
        >
          <RefreshCw size={16} />
          Process Another
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 overflow-y-auto pr-2 pb-20">
        {clips.map((clip) => (
          <ClipCard key={clip.id} clip={clip} />
        ))}
      </div>
    </div>
  );
}

function ClipCard({ clip }: { clip: Clip }) {
  const [copied, setCopied] = useState(false);

  const copyCaption = () => {
    const text = `${clip.caption}\n\n${clip.hashtags.join(" ")}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-neutral-950 border border-neutral-800 rounded-xl overflow-hidden flex flex-col">
      <div className="aspect-video bg-black relative group">
        <video 
          src={clip.url} 
          controls 
          className="w-full h-full object-contain" 
        />
      </div>
      
      <div className="p-4 flex flex-col flex-1">
        <div className="flex justify-between items-start mb-3">
            <div>
                <h4 className="font-medium text-neutral-200">Clip {clip.id}</h4>
                <p className="text-xs text-neutral-500">{formatTime(clip.startTime)} - {formatTime(clip.endTime)}</p>
            </div>
            <a
                href={clip.url}
                download={clip.filename}
                className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors"
                title="Download Video"
            >
                <Download size={18} />
            </a>
        </div>

        <div className="bg-neutral-900 rounded-lg p-3 text-sm text-neutral-300 mb-4 flex-1">
            <p className="mb-2">{clip.caption}</p>
            <p className="text-blue-400">{clip.hashtags.join(" ")}</p>
        </div>

        <div className="flex gap-2">
            <button 
                onClick={copyCaption}
                className="flex-1 flex items-center justify-center gap-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 py-2 rounded-lg text-sm transition-colors"
            >
                {copied ? <Check size={16} /> : <Copy size={16} />}
                {copied ? "Copied" : "Copy Caption"}
            </button>
            {/* Placeholder for future integrations */}
        </div>
      </div>
    </div>
  );
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}
