"use client";

import React, { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { Upload, FileText, CheckCircle2, AlertCircle, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { apiUrl } from "@/lib/api";

interface UploadProgress {
  file: string;
  progress: number;
  status: "pending" | "uploading" | "processing" | "completed" | "error";
  message?: string;
}

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [progresses, setProgresses] = useState<Record<string, UploadProgress>>({});
  const router = useRouter();

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(apiUrl("invoices/upload"), {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText || "Upload failed");
      }
      return res.json();
    },
    onSuccess: (data, file) => {
      setProgresses((prev) => ({
        ...prev,
        [file.name]: { file: file.name, progress: 100, status: "completed" },
      }));
      setTimeout(() => router.push(`/invoices/${data.invoice_id}`), 2000);
    },
    onError: (error: any, file) => {
      setProgresses((prev) => ({
        ...prev,
        [file.name]: { file: file.name, progress: 100, status: "error", message: error.message },
      }));
    },
  });

  const handleFiles = useCallback(
    (newFiles: FileList | null) => {
      if (!newFiles) return;
      const fileArray = Array.from(newFiles).filter((f) => f.type === "application/pdf" || f.type.startsWith("image/"));
      setFiles((prev) => [...prev, ...fileArray]);
      fileArray.forEach((file) => {
        setProgresses((prev) => ({
          ...prev,
          [file.name]: { file: file.name, progress: 0, status: "pending" },
        }));
        uploadMutation.mutate(file);
      });
    },
    [uploadMutation]
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const removeFile = (fileName: string) => {
    setFiles((prev) => prev.filter((f) => f.name !== fileName));
    setProgresses((prev) => {
      const newProgress = { ...prev };
      delete newProgress[fileName];
      return newProgress;
    });
  };

  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-50">
      <div className="flex-1 flex flex-col">
        <header className="h-16 border-b border-zinc-900 px-6 flex items-center justify-between sticky top-0 bg-zinc-950/80 backdrop-blur-md">
          <h1 className="text-xl font-semibold tracking-tight">Document Upload Center</h1>
        </header>

        <div className="p-6 flex-1 flex flex-col gap-6">
          <div
            className={`flex-1 rounded-2xl border-2 border-dashed transition-all flex flex-col items-center justify-center p-12 ${
              isDragging ? "border-indigo-500 bg-indigo-500/5" : "border-zinc-800 bg-zinc-900/20"
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="p-6 rounded-2xl bg-gradient-to-tr from-indigo-600 to-blue-500 mb-6">
              <Upload className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Drop PDF or Image Files Here</h2>
            <p className="text-sm text-zinc-400 mb-6 text-center max-w-sm">
              Upload invoices, contracts, or purchase orders for AI-powered processing and 3-way matching.
            </p>
            <label className="cursor-pointer">
              <input
                type="file"
                accept="application/pdf,image/*"
                multiple
                className="hidden"
                onChange={(e) => handleFiles(e.target.files)}
              />
              <span className="px-6 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-medium transition-colors">
                Browse Files
              </span>
            </label>
          </div>

          {Object.keys(progresses).length > 0 && (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-zinc-300">Upload Queue</h3>
              {Object.values(progresses).map((progress) => (
                <div
                  key={progress.file}
                  className="p-4 rounded-xl bg-zinc-900/40 border border-zinc-800/80 flex items-center gap-4"
                >
                  <div className="p-2 rounded-lg bg-zinc-800">
                    <FileText className="w-4 h-4 text-zinc-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-zinc-200">{progress.file}</span>
                      <span className="text-[10px] text-zinc-500">
                        {progress.status === "completed" ? "Done" : progress.status === "error" ? "Failed" : "Processing"}
                      </span>
                    </div>
                    <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          progress.status === "error"
                            ? "bg-rose-500"
                            : progress.status === "completed"
                            ? "bg-emerald-500"
                            : "bg-indigo-500"
                        }`}
                        style={{ width: `${progress.progress}%` }}
                      />
                    </div>
                    {progress.message && (
                      <p className="text-[10px] text-rose-400 mt-1">{progress.message}</p>
                    )}
                  </div>
                  <button
                    onClick={() => removeFile(progress.file)}
                    className="p-1 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}