"use client";

import { useDropzone } from "react-dropzone";
import { Upload, FileVideo } from "lucide-react";
import { useCallback } from "react";

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
}

export function FileUploader({ onFileSelect }: FileUploaderProps) {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "video/*": [".mp4", ".mov", ".webm"],
    },
    maxFiles: 1,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        w-full max-w-lg h-64 border-2 border-dashed rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all
        ${
          isDragActive
            ? "border-blue-500 bg-blue-500/10"
            : "border-neutral-700 hover:border-neutral-500 hover:bg-neutral-800/50"
        }
      `}
    >
      <input {...getInputProps()} />
      <div className="bg-neutral-800 p-4 rounded-full mb-4">
        <Upload className="w-8 h-8 text-neutral-400" />
      </div>
      <p className="text-lg font-medium text-neutral-300">
        {isDragActive ? "Drop the video here" : "Drag & drop video here"}
      </p>
      <p className="text-sm text-neutral-500 mt-2">
        or click to select file
      </p>
      <div className="mt-4 flex gap-2 text-xs text-neutral-600">
        <span className="bg-neutral-800 px-2 py-1 rounded">MP4</span>
        <span className="bg-neutral-800 px-2 py-1 rounded">MOV</span>
        <span className="bg-neutral-800 px-2 py-1 rounded">WEBM</span>
      </div>
    </div>
  );
}
