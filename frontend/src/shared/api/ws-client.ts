export type WsStatus =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error";

export interface WsMessage<T = unknown> {
  type: string;
  payload: T;
}

type MessageHandler<T = unknown> = (payload: T) => void;

// Задержки переподключения: 1s, 2s, 5s, 10s, 30s
const RECONNECT_DELAYS = [1_000, 2_000, 5_000, 10_000, 30_000];

class WsClient {
  private ws: WebSocket | null = null;
  private url = "";
  private handlers = new Map<string, Set<MessageHandler>>();
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = false;

  onStatusChange: ((status: WsStatus) => void) | null = null;

  connect(url: string) {
    if (this.ws) this._close();
    this.url = url;
    this.shouldReconnect = true;
    this.reconnectAttempt = 0;
    this._open();
  }

  disconnect() {
    this.shouldReconnect = false;
    this._clearReconnectTimer();
    this._close();
    this.onStatusChange?.("disconnected");
  }

  send<T>(type: string, payload: T) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    }
  }

  /** Подписка на сообщения по типу. Возвращает функцию отписки. */
  on<T = unknown>(type: string, handler: MessageHandler<T>): () => void {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set());
    this.handlers.get(type)!.add(handler as MessageHandler);
    return () => this.handlers.get(type)?.delete(handler as MessageHandler);
  }

  private _open() {
    this.onStatusChange?.("connecting");
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.onStatusChange?.("connected");
    };

    this.ws.onmessage = (event: MessageEvent<string>) => {
      try {
        const msg = JSON.parse(event.data) as WsMessage;
        this.handlers.get(msg.type)?.forEach((h) => h(msg.payload));
        // "*" — подписка на все сообщения
        this.handlers.get("*")?.forEach((h) => h(msg));
      } catch {
        // игнорируем не-JSON фреймы
      }
    };

    this.ws.onclose = () => {
      this.ws = null;
      if (this.shouldReconnect) {
        this.onStatusChange?.("reconnecting");
        this._scheduleReconnect();
      } else {
        this.onStatusChange?.("disconnected");
      }
    };

    this.ws.onerror = () => {
      this.onStatusChange?.("error");
    };
  }

  private _close() {
    if (this.ws) {
      // Снимаем обработчики, чтобы не сработало onclose → reconnect
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.close();
      this.ws = null;
    }
  }

  private _scheduleReconnect() {
    const delay =
      RECONNECT_DELAYS[Math.min(this.reconnectAttempt, RECONNECT_DELAYS.length - 1)];
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => this._open(), delay);
  }

  private _clearReconnectTimer() {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

export const wsClient = new WsClient();
