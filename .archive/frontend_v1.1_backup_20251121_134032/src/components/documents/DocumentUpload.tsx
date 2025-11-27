import { useState, useCallback } from 'react'
import { Upload, File, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'

interface UploadFile {
  file: File
  id: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
  stage?: string  // e.g., "uploading", "uploaded", "metadata_saved", "indexing", "indexed"
  message?: string  // Progress message from WebSocket
  chunks?: number  // Number of indexed chunks
}

interface DuplicateDetection {
  filename: string
  size: number
  modified: string
  path: string
}

interface DocumentUploadProps {
  onUpload: (files: File[]) => Promise<void>
  isUploading: boolean
  onDuplicateDetected?: (file: File, duplicateInfo: DuplicateDetection) => void
}

export function DocumentUpload({ onUpload, isUploading, onDuplicateDetected }: DocumentUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([])
  const [globalError, setGlobalError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const addFiles = useCallback((newFiles: File[]) => {
    setGlobalError(null)
    const validFiles: File[] = []
    const errors: string[] = []

    for (const file of newFiles) {
      if (!file.name.endsWith('.txt')) {
        errors.push(`${file.name}: 只支援 .txt 文字檔案`)
        continue
      }
      validFiles.push(file)
    }

    if (errors.length > 0) {
      setGlobalError(errors.join(', '))
    }

    if (validFiles.length > 0) {
      const uploadFileObjects: UploadFile[] = validFiles.map((file) => ({
        file,
        id: `${file.name}-${Date.now()}-${Math.random()}`,
        status: 'pending',
        progress: 0,
      }))
      setUploadFiles((prev) => [...prev, ...uploadFileObjects])
    }
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)

      const files = Array.from(e.dataTransfer.files)
      if (files.length === 0) return

      addFiles(files)
    },
    [addFiles]
  )

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files
      if (!files || files.length === 0) return

      addFiles(Array.from(files))

      // Reset input
      e.target.value = ''
    },
    [addFiles]
  )

  const removeFile = useCallback((id: string) => {
    setUploadFiles((prev) => prev.filter((f) => f.id !== id))
  }, [])

  const clearCompleted = useCallback(() => {
    setUploadFiles((prev) => prev.filter((f) => f.status !== 'success'))
  }, [])

  const uploadFileViaPolling = useCallback(
    async (uploadFile: UploadFile): Promise<void> => {
      try {
        // Step 1: Upload file and get job ID (Google Drive style)
        const formData = new FormData()
        formData.append('file', uploadFile.file)
        formData.append('auto_index', 'true')
        formData.append('extract_metadata', 'true')

        const uploadResponse = await fetch('http://localhost:8000/api/v1/documents/upload-with-progress', {
          method: 'POST',
          body: formData,
        })

        if (!uploadResponse.ok) {
          throw new Error('Upload failed')
        }

        const responseData = await uploadResponse.json()

        // Check for duplicate detection
        if (responseData.status === 'duplicate_detected') {
          // Remove file from upload list
          setUploadFiles((prev) => prev.filter((f) => f.id !== uploadFile.id))

          // Notify parent to show duplicate modal
          if (onDuplicateDetected) {
            onDuplicateDetected(uploadFile.file, responseData.duplicate_info)
          }

          return Promise.resolve()
        }

        const { job_id } = responseData

        // Step 2: Poll for progress updates (every 500ms)
        return new Promise((resolve, reject) => {
          const pollInterval = setInterval(async () => {
            try {
              const progressResponse = await fetch(
                `http://localhost:8000/api/v1/documents/upload-progress/${job_id}`
              )

              if (!progressResponse.ok) {
                clearInterval(pollInterval)
                reject(new Error('Progress polling failed'))
                return
              }

              const progress = await progressResponse.json()

              // Update UI with progress
              setUploadFiles((prev) =>
                prev.map((f) =>
                  f.id === uploadFile.id
                    ? {
                        ...f,
                        status: progress.stage === 'error' ? 'error' : 'uploading',
                        progress: progress.progress,
                        stage: progress.stage,
                        message: progress.message,
                        chunks: progress.chunks || 0,
                        error: progress.error,
                      }
                    : f
                )
              )

              // Check if complete or error
              if (progress.stage === 'complete') {
                clearInterval(pollInterval)
                setUploadFiles((prev) =>
                  prev.map((f) =>
                    f.id === uploadFile.id
                      ? {
                          ...f,
                          status: 'success',
                          progress: 100,
                          message: progress.message,
                          chunks: progress.chunks,
                        }
                      : f
                  )
                )

                // Clean up job from server
                await fetch(`http://localhost:8000/api/v1/documents/upload-progress/${job_id}`, {
                  method: 'DELETE',
                })

                resolve()
              } else if (progress.stage === 'error') {
                clearInterval(pollInterval)
                reject(new Error(progress.error || 'Upload failed'))
              }
            } catch (err) {
              clearInterval(pollInterval)
              reject(err)
            }
          }, 500) // Poll every 500ms
        })
      } catch (err) {
        setUploadFiles((prev) =>
          prev.map((f) =>
            f.id === uploadFile.id
              ? {
                  ...f,
                  status: 'error',
                  progress: 0,
                  error: err instanceof Error ? err.message : '上傳失敗',
                }
              : f
          )
        )
        throw err
      }
    },
    []
  )

  const handleUploadAll = useCallback(async () => {
    const pendingFiles = uploadFiles.filter((f) => f.status === 'pending')
    if (pendingFiles.length === 0) return

    try {
      // Mark all as uploading
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.status === 'pending' ? { ...f, status: 'uploading', progress: 0 } : f
        )
      )

      // Upload all files via HTTP polling (parallel, like Google Drive)
      await Promise.all(pendingFiles.map((f) => uploadFileViaPolling(f)))

      // Trigger parent refresh to show newly uploaded documents
      if (onUpload) {
        await onUpload([])  // Empty array - files already processed via polling
      }

      setGlobalError(null)
    } catch (err) {
      // Individual file errors are already handled in uploadFileViaPolling
      console.error('Upload error:', err)
    }
  }, [uploadFiles, uploadFileViaPolling, onUpload])

  const pendingCount = uploadFiles.filter((f) => f.status === 'pending').length
  const uploadingCount = uploadFiles.filter((f) => f.status === 'uploading').length
  const successCount = uploadFiles.filter((f) => f.status === 'success').length
  const errorCount = uploadFiles.filter((f) => f.status === 'error').length

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Upload className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">上傳文件</h3>
          </div>
          {successCount > 0 && (
            <button
              onClick={clearCompleted}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              清除已完成
            </button>
          )}
        </div>
      </div>

      <div className="p-4">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            isDragOver
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          } ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
        >
          <File className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-2">
            {isUploading ? '上傳中...' : '拖曳檔案至此處，或點擊選擇檔案'}
          </p>
          <p className="text-sm text-gray-500 mb-4">支援多檔案上傳 (.txt 文字檔案)</p>

          <label className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 cursor-pointer">
            <Upload className="h-4 w-4 mr-2" />
            選擇檔案
            <input
              type="file"
              accept=".txt"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              disabled={isUploading}
            />
          </label>
        </div>

        {globalError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center text-red-700">
            <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
            <span className="text-sm">{globalError}</span>
          </div>
        )}

        {/* File List */}
        {uploadFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-700">
                待上傳檔案 ({uploadFiles.length})
              </p>
              {pendingCount > 0 && !isUploading && (
                <button
                  onClick={handleUploadAll}
                  className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  <Upload className="h-3.5 w-3.5 mr-1.5" />
                  上傳全部 ({pendingCount})
                </button>
              )}
            </div>

            <div className="space-y-2 max-h-64 overflow-y-auto">
              {uploadFiles.map((uploadFile) => (
                <div
                  key={uploadFile.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                >
                  <div className="flex items-center flex-1 min-w-0">
                    {uploadFile.status === 'pending' && (
                      <File className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                    )}
                    {uploadFile.status === 'uploading' && (
                      <Loader2 className="h-4 w-4 text-blue-600 mr-2 flex-shrink-0 animate-spin" />
                    )}
                    {uploadFile.status === 'success' && (
                      <CheckCircle2 className="h-4 w-4 text-green-600 mr-2 flex-shrink-0" />
                    )}
                    {uploadFile.status === 'error' && (
                      <AlertCircle className="h-4 w-4 text-red-600 mr-2 flex-shrink-0" />
                    )}

                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 truncate">
                        {uploadFile.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {(uploadFile.file.size / 1024).toFixed(2)} KB
                        {uploadFile.chunks !== undefined && uploadFile.chunks > 0 && (
                          <span className="ml-2 text-green-600">
                            • {uploadFile.chunks} 個區塊
                          </span>
                        )}
                      </p>
                      {uploadFile.message && uploadFile.status === 'uploading' && (
                        <p className="text-xs text-blue-600 mt-1">{uploadFile.message}</p>
                      )}
                      {uploadFile.message && uploadFile.status === 'success' && (
                        <p className="text-xs text-green-600 mt-1">{uploadFile.message}</p>
                      )}
                      {uploadFile.error && (
                        <p className="text-xs text-red-600 mt-1">{uploadFile.error}</p>
                      )}
                    </div>
                  </div>

                  {uploadFile.status === 'pending' && (
                    <button
                      onClick={() => removeFile(uploadFile.id)}
                      className="ml-2 text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}

                  {uploadFile.status === 'uploading' && (
                    <div className="ml-2 w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-600 transition-all duration-300"
                        style={{ width: `${uploadFile.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Status Summary */}
            {(successCount > 0 || errorCount > 0 || uploadingCount > 0) && (
              <div className="mt-3 pt-3 border-t border-gray-200 flex items-center justify-between text-sm">
                <div className="flex items-center space-x-4">
                  {uploadingCount > 0 && (
                    <span className="text-blue-600">上傳中: {uploadingCount}</span>
                  )}
                  {successCount > 0 && (
                    <span className="text-green-600">成功: {successCount}</span>
                  )}
                  {errorCount > 0 && (
                    <span className="text-red-600">失敗: {errorCount}</span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
