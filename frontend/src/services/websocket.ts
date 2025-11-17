type MessageHandler = (data: unknown) => void
type ConnectionHandler = () => void

interface WebSocketConfig {
  url: string
  reconnectAttempts?: number
  reconnectDelay?: number
}

export class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts: number
  private reconnectDelay: number
  private currentAttempt = 0
  private handlers: Map<string, MessageHandler[]> = new Map()
  private onConnectHandlers: ConnectionHandler[] = []
  private onDisconnectHandlers: ConnectionHandler[] = []
  private shouldReconnect = true

  constructor(config: WebSocketConfig) {
    this.url = config.url
    this.reconnectAttempts = config.reconnectAttempts ?? 5
    this.reconnectDelay = config.reconnectDelay ?? 1000
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.currentAttempt = 0
      this.onConnectHandlers.forEach((handler) => handler())
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const type = data.type as string
        const handlers = this.handlers.get(type) || []
        handlers.forEach((handler) => handler(data.payload))
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      this.onDisconnectHandlers.forEach((handler) => handler())

      if (this.shouldReconnect && this.currentAttempt < this.reconnectAttempts) {
        const delay = this.reconnectDelay * Math.pow(2, this.currentAttempt)
        console.log(`Reconnecting in ${delay}ms...`)
        setTimeout(() => {
          this.currentAttempt++
          this.connect()
        }, delay)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  disconnect(): void {
    this.shouldReconnect = false
    this.ws?.close()
    this.ws = null
  }

  send(type: string, payload: unknown): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected')
      return
    }

    this.ws.send(JSON.stringify({ type, payload }))
  }

  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, [])
    }
    this.handlers.get(type)!.push(handler)

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(type)
      if (handlers) {
        const index = handlers.indexOf(handler)
        if (index > -1) {
          handlers.splice(index, 1)
        }
      }
    }
  }

  onConnect(handler: ConnectionHandler): () => void {
    this.onConnectHandlers.push(handler)
    return () => {
      const index = this.onConnectHandlers.indexOf(handler)
      if (index > -1) {
        this.onConnectHandlers.splice(index, 1)
      }
    }
  }

  onDisconnect(handler: ConnectionHandler): () => void {
    this.onDisconnectHandlers.push(handler)
    return () => {
      const index = this.onDisconnectHandlers.indexOf(handler)
      if (index > -1) {
        this.onDisconnectHandlers.splice(index, 1)
      }
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

// Default WebSocket service instance
export const wsService = new WebSocketService({
  url: `ws://${window.location.host}/ws/query`,
})
