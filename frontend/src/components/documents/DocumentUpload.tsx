import { useState, useCallback } from 'react'
import { Upload, File, AlertCircle } from 'lucide-react'

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<void>
  isUploading: boolean
}

export function DocumentUpload({ onUpload, isUploading }: DocumentUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)
      setError(null)

      const files = Array.from(e.dataTransfer.files)
      if (files.length === 0) return

      const file = files[0]
      if (!file.name.endsWith('.txt')) {
        setError('只支援 .txt 文字檔案')
        return
      }

      try {
        await onUpload(file)
      } catch (err) {
        setError(err instanceof Error ? err.message : '上傳失敗')
      }
    },
    [onUpload]
  )

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      setError(null)
      const files = e.target.files
      if (!files || files.length === 0) return

      const file = files[0]
      if (!file.name.endsWith('.txt')) {
        setError('只支援 .txt 文字檔案')
        return
      }

      try {
        await onUpload(file)
      } catch (err) {
        setError(err instanceof Error ? err.message : '上傳失敗')
      }

      // Reset input
      e.target.value = ''
    },
    [onUpload]
  )

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center">
          <Upload className="h-5 w-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">上傳文件</h3>
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
          <p className="text-sm text-gray-500 mb-4">僅支援 .txt 文字檔案</p>

          <label className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 cursor-pointer">
            <Upload className="h-4 w-4 mr-2" />
            選擇檔案
            <input
              type="file"
              accept=".txt"
              onChange={handleFileSelect}
              className="hidden"
              disabled={isUploading}
            />
          </label>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center text-red-700">
            <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}
      </div>
    </div>
  )
}
