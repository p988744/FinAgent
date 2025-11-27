import { X, Clock, Upload, AlertCircle } from 'lucide-react'
import type { DocumentVersion } from '../../types/documents'

interface DuplicateInfo {
  filename: string
  size: number
  modified: string
  path: string
}

interface VersionHistoryModalProps {
  documentId: string
  documentName: string
  versions: DocumentVersion[]
  onClose: () => void
  onUploadNewVersion: (file: File, action?: 'version' | 'replace') => Promise<void>
  isUploading: boolean
  // Duplicate detection mode
  duplicateMode?: boolean
  duplicateInfo?: DuplicateInfo
  pendingFile?: File
}

export function VersionHistoryModal({
  documentName,
  versions,
  onClose,
  onUploadNewVersion,
  isUploading,
  duplicateMode = false,
  duplicateInfo,
  pendingFile,
}: VersionHistoryModalProps) {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('zh-TW')
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const file = files[0]
    if (!file.name.endsWith('.txt')) {
      alert('只支援 .txt 文字檔案')
      return
    }

    try {
      await onUploadNewVersion(file)
    } catch (err) {
      alert(err instanceof Error ? err.message : '上傳失敗')
    }

    e.target.value = ''
  }

  const handleDuplicateAction = async (action: 'version' | 'replace') => {
    if (!pendingFile) return

    try {
      await onUploadNewVersion(pendingFile, action)
      onClose()
    } catch (err) {
      alert(err instanceof Error ? err.message : '上傳失敗')
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center">
            <Clock className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              版本歷史 - {documentName}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4 flex-1 overflow-y-auto">
          {duplicateMode && duplicateInfo && (
            <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-yellow-800 mb-1">
                    檔案已存在
                  </h4>
                  <p className="text-sm text-yellow-700 mb-3">
                    文件「{duplicateInfo.filename}」已存在於系統中。請選擇處理方式：
                  </p>
                  <div className="space-y-2">
                    <button
                      onClick={() => handleDuplicateAction('version')}
                      disabled={isUploading}
                      className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      建立新版本 (推薦)
                    </button>
                    <button
                      onClick={() => handleDuplicateAction('replace')}
                      disabled={isUploading}
                      className="w-full px-4 py-2 text-sm font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      視為新檔案 (保留兩者)
                    </button>
                    <button
                      onClick={onClose}
                      disabled={isUploading}
                      className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      取消上傳
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {!duplicateMode && (
            <div className="mb-4">
              <label className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 cursor-pointer">
                <Upload className="h-4 w-4 mr-2" />
                {isUploading ? '上傳中...' : '上傳新版本'}
                <input
                  type="file"
                  accept=".txt"
                  onChange={handleFileSelect}
                  className="hidden"
                  disabled={isUploading}
                />
              </label>
            </div>
          )}

          {versions.length === 0 ? (
            <p className="text-gray-500 text-center py-4">無版本歷史</p>
          ) : (
            <div className="space-y-3">
              {versions.map((version) => (
                <div
                  key={version.version}
                  className="border border-gray-200 rounded-lg p-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-gray-900">
                      版本 {version.version}
                      {version.version === versions.length && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          最新
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-500">
                      {formatSize(version.size_bytes)}
                    </div>
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    建立於 {formatDate(version.created_at)}
                  </div>
                  <div className="mt-1 text-xs text-gray-400 truncate">
                    {version.file_path}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  )
}
