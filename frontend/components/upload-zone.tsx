"use client"

import { useState, useCallback } from "react"
import { Upload, FileText, X, AlertCircle, CheckCircle } from "lucide-react"
import type { Transaction, AnalyticsSummary } from "@/lib/types"

interface UploadZoneProps {
  onUploadSuccess: (data: { transactions: Transaction[], summary: AnalyticsSummary }) => void
}

function isCsv(file: File): boolean {
  return file.type === "text/csv" || file.name.toLowerCase().endsWith(".csv")
}

export function UploadZone({ onUploadSuccess }: UploadZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Add new selections to the staged list, de-duping by name + size.
  const addFiles = useCallback((incoming: File[]) => {
    const csvs = incoming.filter(isCsv)
    if (csvs.length === 0) {
      setError("Please upload a valid CSV file")
      return
    }
    setError(null)
    setFiles((prev) => {
      const seen = new Set(prev.map((f) => `${f.name}:${f.size}`))
      return [...prev, ...csvs.filter((f) => !seen.has(`${f.name}:${f.size}`))]
    })
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    addFiles(Array.from(e.dataTransfer.files))
  }, [addFiles])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    addFiles(Array.from(e.target.files ?? []))
    e.target.value = "" // allow re-selecting the same file
  }, [addFiles])

  const removeFile = (key: string) => {
    setFiles((prev) => prev.filter((f) => `${f.name}:${f.size}` !== key))
  }

  const handleUpload = async () => {
    if (files.length === 0) return

    setIsUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      files.forEach((file) => formData.append("files", file))

      const response = await fetch("/api/transactions/upload", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage =
          errorData.detail || errorData.message || `Upload failed: ${response.status}`
        throw new Error(errorMessage)
      }

      const data = await response.json()

      if (data.success) {
        onUploadSuccess(data)
        setFiles([])
      } else {
        setError(data.message || "Upload failed")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed")
    } finally {
      setIsUploading(false)
    }
  }

  const hasFiles = files.length > 0

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Upload Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragOver
            ? "border-primary bg-primary/5"
            : "border-border hover:border-primary/50"
          }
          ${hasFiles ? "bg-muted/50" : ""}
        `}
      >
        <input
          type="file"
          accept=".csv"
          multiple
          onChange={handleFileSelect}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        {!hasFiles ? (
          <div className="space-y-4">
            <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
            <div>
              <p className="text-lg font-medium">
                Drop your CSV files here
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                or click to browse files
              </p>
            </div>
            <p className="text-xs text-muted-foreground">
              Supports multiple bank CSV exports up to 10MB each
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {files.map((file) => (
              <div key={`${file.name}:${file.size}`} className="flex items-center justify-center gap-3">
                <FileText className="h-8 w-8 text-primary shrink-0" />
                <div className="text-left">
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(`${file.name}:${file.size}`)}
                  aria-label={`Remove ${file.name}`}
                  className="ml-2 p-1 hover:bg-muted rounded relative z-10"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
            <p className="text-xs text-muted-foreground pt-1">
              Drop or browse to add more files
            </p>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-destructive" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Upload Button */}
      {hasFiles && (
        <div className="mt-6 flex justify-center">
          <button
            onClick={handleUpload}
            disabled={isUploading}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground ring-offset-background transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
          >
            {isUploading ? (
              <>
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Uploading...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4" />
                Upload &amp; Analyze {files.length > 1 ? `(${files.length} files)` : ""}
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}
