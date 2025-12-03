import { useState } from 'react'

interface QueryInputProps {
    onSubmit: (query: string, usePlanExecute: boolean, useWikiSearch: boolean) => void
    isQuerying: boolean
    isConnected: boolean
}

export function QueryInput({ onSubmit, isQuerying, isConnected }: QueryInputProps) {
    const [query, setQuery] = useState('')
    const [usePlanExecute, setUsePlanExecute] = useState(false)
    const [useWikiSearch, setUseWikiSearch] = useState(false)

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (query.trim() && !isQuerying) {
            onSubmit(query, usePlanExecute, useWikiSearch)
        }
    }

    return (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-2xl font-bold mb-4">FinAgent Research</h2>

            <form onSubmit={handleSubmit}>
                <div className="mb-4">
                    <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
                        Enter your research question
                    </label>
                    <textarea
                        id="query"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        disabled={isQuerying}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                        rows={3}
                        placeholder="例如：玉山銀行2020年洗錢防制裁罰"
                    />
                </div>

                <div className="flex gap-4 mb-4">
                    <label className="flex items-center">
                        <input
                            type="checkbox"
                            checked={usePlanExecute}
                            onChange={(e) => {
                                setUsePlanExecute(e.target.checked)
                                if (e.target.checked) setUseWikiSearch(false)
                            }}
                            disabled={isQuerying}
                            className="mr-2"
                        />
                        <span className="text-sm">Plan-and-Execute Mode</span>
                    </label>

                    <label className="flex items-center">
                        <input
                            type="checkbox"
                            checked={useWikiSearch}
                            onChange={(e) => {
                                setUseWikiSearch(e.target.checked)
                                if (e.target.checked) setUsePlanExecute(false)
                            }}
                            disabled={isQuerying}
                            className="mr-2"
                        />
                        <span className="text-sm">Wiki Search Mode</span>
                    </label>
                </div>

                <div className="flex items-center justify-between">
                    <button
                        type="submit"
                        disabled={isQuerying || !isConnected || !query.trim()}
                        className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                        {isQuerying ? 'Processing...' : 'Submit Query'}
                    </button>

                    <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="text-sm text-gray-600">
                            {isConnected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>
                </div>
            </form>
        </div>
    )
}
