import { X, FileText } from 'lucide-react'
import type { DocumentContent } from '../../types/documents'

interface ContentViewerModalProps {
  content: DocumentContent | null
  onClose: () => void
  isLoading: boolean
}

export function ContentViewerModal({
  content,
  onClose,
  isLoading,
}: ContentViewerModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[80vh] flex flex-col">
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center">
            <FileText className="h-5 w-5 text-gray-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">
              文件內容
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
          {isLoading ? (
            <div className="text-center text-gray-500 py-8">載入內容中...</div>
          ) : content ? (
            <>
              <div className="mb-4 text-sm text-gray-500">
                字元數: {content.size_chars.toLocaleString()}
              </div>
              <pre className="bg-gray-50 p-4 rounded-lg text-sm whitespace-pre-wrap font-mono overflow-x-auto">
                {content.content}
              </pre>
            </>
          ) : (
            <div className="text-center text-gray-500 py-8">無法載入內容</div>
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
