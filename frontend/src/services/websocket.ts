import type { DashboardEvent } from '@/types'

type EventHandler = (event: DashboardEvent) => void

class DashboardWebSocket {
  private socket: WebSocket | null = null
  private handlers: EventHandler[] = []
  private reconnectTimer: number | null = null

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.host
    const url = `${protocol}://${host}/api/v1/dashboard/ws`

    this.socket = new WebSocket(url)

    this.socket.onmessage = (message) => {
      try {
        const data = JSON.parse(message.data)

        if (data.type === 'snapshot' && Array.isArray(data.events)) {
          data.events.forEach((event: DashboardEvent) => this.emit(event))
          return
        }

        this.emit(data as DashboardEvent)
      } catch {
        // ignore malformed payloads
      }
    }

    this.socket.onclose = () => {
      this.scheduleReconnect()
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.socket?.close()
    this.socket = null
  }

  subscribe(handler: EventHandler) {
    this.handlers.push(handler)

    return () => {
      this.handlers = this.handlers.filter((item) => item !== handler)
    }
  }

  private emit(event: DashboardEvent) {
    this.handlers.forEach((handler) => handler(event))
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, 3000)
  }
}

export const dashboardWebSocket = new DashboardWebSocket()

export default dashboardWebSocket
