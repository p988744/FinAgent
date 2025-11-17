import { useState } from 'react'
import { Wifi, WifiOff, RefreshCw, CheckCircle2, XCircle } from 'lucide-react'
import type { ConnectionTestResult } from '../../types/models'

interface ConnectionTesterProps {
  onTest: () => Promise<ConnectionTestResult>
}

export function ConnectionTester({ onTest }: ConnectionTesterProps) {
  const [isTesting, setIsTesting] = useState(false)
  const [result, setResult] = useState<ConnectionTestResult | null>(null)

  const handleTest = async () => {
    setIsTesting(true)
    setResult(null)

    try {
      const testResult = await onTest()
      setResult(testResult)
    } catch (err) {
      setResult({
        success: false,
        message: '測試失敗',
        latency_ms: null,
        model: null,
      })
    } finally {
      setIsTesting(false)
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {result === null ? (
            <Wifi className="h-5 w-5 text-gray-400" />
          ) : result.success ? (
            <CheckCircle2 className="h-5 w-5 text-green-500" />
          ) : (
            <XCircle className="h-5 w-5 text-red-500" />
          )}
          <h3 className="font-medium text-gray-900">連線測試</h3>
        </div>

        <button
          onClick={handleTest}
          disabled={isTesting}
          className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isTesting ? (
            <>
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              測試中...
            </>
          ) : (
            <>
              <Wifi className="h-4 w-4 mr-2" />
              測試連線
            </>
          )}
        </button>
      </div>

      {result && (
        <div
          className={`mt-4 p-3 rounded-md ${
            result.success
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          <div className="flex items-center">
            {result.success ? (
              <CheckCircle2 className="h-5 w-5 text-green-500 mr-2" />
            ) : (
              <WifiOff className="h-5 w-5 text-red-500 mr-2" />
            )}
            <div>
              <p
                className={`font-medium ${
                  result.success ? 'text-green-800' : 'text-red-800'
                }`}
              >
                {result.message}
              </p>
              {result.model && (
                <p className="text-sm text-gray-600 mt-1">模型: {result.model}</p>
              )}
              {result.latency_ms && (
                <p className="text-sm text-gray-600">
                  延遲: {result.latency_ms.toFixed(0)}ms
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
