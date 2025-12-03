import { useEffect, useRef, useState, useCallback } from 'react'
import type { QueryState, PlanTask, QueryResult } from '../types'

export function useWebSocket() {
    const [state, setState] = useState<QueryState>({
        isQuerying: false,
        plan: null,
        results: null,
        error: null,
    })

    const wsRef = useRef<WebSocket | null>(null)
    const [isConnected, setIsConnected] = useState(false)
    const [logs, setLogs] = useState<Array<{ timestamp: string, type: string, data: any }>>([])


    // Send query to backend
    const sendQuery = useCallback((query: string, usePlanExecute: boolean, useWikiSearch: boolean) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected')
            return
        }

        // Reset state
        setState({
            isQuerying: true,
            plan: null,
            results: null,
            error: null,
        })

        // Send query - MUST match backend format
        const payload = {
            type: 'query',  // Backend expects this field!
            text: query,     // Backend expects "text" not "query"
            use_plan_execute: usePlanExecute,
            use_wiki_search: useWikiSearch,
        }

        console.log('Sending query:', payload)
        wsRef.current.send(JSON.stringify(payload))
    }, [])

    useEffect(() => {
        // Connect to WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/query`

        console.log('Connecting to WebSocket:', wsUrl)
        const ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
            console.log('WebSocket connected')
            setIsConnected(true)
            // Clear any previous connection errors
            setState(prev => ({ ...prev, error: null }))
        }

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data)
                console.log('Received message:', message)

                // Log message for debugging
                setLogs(prev => [...prev.slice(-19), {
                    timestamp: new Date().toISOString(),
                    type: message.type,
                    data: message
                }])

                handleMessage(message)
            } catch (error) {
                console.error('Failed to parse message:', error)
            }
        }

        ws.onerror = (error) => {
            console.error('WebSocket error:', error)
            setState(prev => ({ ...prev, error: 'Connection error' }))
        }

        ws.onclose = () => {
            console.log('WebSocket closed')
            setIsConnected(false)
        }

        return () => {
            ws.close()
        }
    }, [])

    const handleMessage = (message: any) => {
        const { type, payload } = message  // Backend sends "payload" not "data"

        switch (type) {
            case 'query_started':
                setState(prev => ({ ...prev, isQuerying: true }))
                break

            case 'plan_created':
                // Parse plan tasks
                if (payload?.plan) {
                    const tasks: PlanTask[] = payload.plan.map((task: any, index: number) => ({
                        task_number: index + 1,
                        description: task.description || task,
                        status: 'pending' as const,
                    }))
                    setState(prev => ({ ...prev, plan: tasks }))
                }
                break

            case 'step_start':
                // Update task status to in_progress
                if (payload?.step && state.plan) {
                    setState(prev => {
                        if (!prev.plan) return prev
                        const updated = prev.plan.map((task, idx) => {
                            if (idx + 1 === payload.task_number || task.description === payload.step) {
                                return { ...task, status: 'in_progress' as const }
                            }
                            return task
                        })
                        return { ...prev, plan: updated }
                    })
                }
                break

            case 'step_complete':
                // Update task status to complete
                if (payload?.step && state.plan) {
                    setState(prev => {
                        if (!prev.plan) return prev
                        const updated = prev.plan.map((task, idx) => {
                            if (idx + 1 === payload.task_number || task.description === payload.step) {
                                return { ...task, status: 'complete' as const, result: payload.result }
                            }
                            return task
                        })
                        return { ...prev, plan: updated }
                    })
                }
                break

            case 'query_complete':
                // Display final results
                // Backend sends payload with nested 'result' object
                console.log('🎯 query_complete received:', payload)

                // Unwrap the result object if it exists
                const data = payload?.result || payload
                console.log('📦 Unwrapped data:', data)
                console.log('  - detailed_analysis:', data?.detailed_analysis)
                console.log('  - summary:', data?.summary)
                console.log('  - citations:', data?.citations)

                // ALWAYS set isQuerying to false when query completes
                if (data?.detailed_analysis || data?.summary) {
                    const result: QueryResult = {
                        answer: data.detailed_analysis || data.summary || 'No answer generated',
                        references: (data.citations || []).map((cite: any, idx: number) => ({
                            doc_id: cite.doc_id || cite.id || `cite-${idx}`,
                            title: cite.source || cite.title,
                            content: cite.content || cite.text || '',
                            score: cite.score || cite.relevance,
                        })),
                        confidence: data.confidence,
                    }
                    console.log('✅ Setting results:', result)
                    setState(prev => ({
                        ...prev,
                        isQuerying: false,
                        results: result,
                    }))
                } else {
                    console.warn('⚠️ No detailed_analysis or summary in unwrapped data, but stopping query')
                    // Even if no valid data, stop showing "Processing..."
                    setState(prev => ({
                        ...prev,
                        isQuerying: false,
                        error: 'Query completed but no results received'
                    }))
                }
                break

            case 'error':
            case 'query_failed':
                // Handle both error and query_failed messages
                const errorMsg = payload?.error || payload?.message || 'An error occurred'
                console.error('❌ Query failed:', errorMsg)
                setState(prev => ({
                    ...prev,
                    isQuerying: false,
                    error: errorMsg,
                }))
                break

            // Informational messages we can log but don't need to handle
            case 'step_update':
            case 'activity_log':
                // These are handled by the backend for detailed logging
                // We don't need to do anything with them in this simple UI
                break

            default:
                console.log('Unhandled message type:', type)
        }
    }

    return {
        ...state,
        isConnected,
        sendQuery,
        logs,
    }
}
