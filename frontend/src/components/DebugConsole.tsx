import { useState } from 'react'

interface DebugConsoleProps {
    logs: Array<{ timestamp: string; type: string; data: any }>
}

export function DebugConsole({ logs }: DebugConsoleProps) {
    const [isExpanded, setIsExpanded] = useState(false)

    return (
        <div className="bg-gray-900 text-gray-100 rounded-lg shadow mt-6">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-2 text-left font-mono text-sm bg-gray-800 rounded-t-lg hover:bg-gray-700 flex items-center justify-between"
            >
                <span>🔍 Debug Console ({logs.length} messages)</span>
                <span>{isExpanded ? '▼' : '▶'}</span>
            </button>

            {isExpanded && (
                <div className="p-4 max-h-96 overflow-y-auto font-mono text-xs">
                    {logs.length === 0 ? (
                        <div className="text-gray-500">No messages received yet...</div>
                    ) : (
                        logs.map((log, idx) => (
                            <div key={idx} className="mb-2 pb-2 border-b border-gray-700">
                                <div className="text-gray-400">
                                    [{new Date(log.timestamp).toLocaleTimeString()}]
                                </div>
                                <div className="text-blue-400">Type: {log.type}</div>
                                <pre className="mt-1 text-gray-300 overflow-x-auto">
                                    {JSON.stringify(log.data, null, 2)}
                                </pre>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    )
}
