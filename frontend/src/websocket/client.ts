/**
 * Production-ready WebSocket client with automatic reconnection,
 * message queuing, error handling, and type safety.
 */

import { useExecutionStore } from '../store/executionStore';

// Types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
  id?: string;
}

export interface WebSocketConfig {
  url: string;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
  messageQueueSize?: number;
  debug?: boolean;
}

export interface WebSocketClientState {
  connected: boolean;
  connecting: boolean;
  reconnectAttempts: number;
  lastError: string | null;
  lastHeartbeat: string | null;
  messageQueue: WebSocketMessage[];
}

export type WebSocketEventHandler = (event: WebSocketMessage) => void;
export type WebSocketErrorHandler = (error: Error) => void;
export type WebSocketStateHandler = (state: WebSocketClientState) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketConfig>;
  private state: WebSocketClientState;
  private eventHandlers: Map<string, WebSocketEventHandler[]> = new Map();
  private errorHandler?: WebSocketErrorHandler;
  private stateHandler?: WebSocketStateHandler;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageQueueTimer: NodeJS.Timeout | null = null;

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectAttempts: config.reconnectAttempts || 5,
      reconnectInterval: config.reconnectInterval || 2000,
      heartbeatInterval: config.heartbeatInterval || 30000,
      messageQueueSize: config.messageQueueSize || 100,
      debug: config.debug || false,
      ...config,
    };

    this.state = {
      connected: false,
      connecting: false,
      reconnectAttempts: 0,
      lastError: null,
      lastHeartbeat: null,
      messageQueue: [],
    };

    this.log('WebSocket client initialized with config:', this.config);
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.state.connected || this.state.connecting) {
      this.log('Already connected or connecting');
      return;
    }

    this.state.connecting = true;
    this.updateState();

    try {
      this.log(`Connecting to WebSocket: ${this.config.url}`);
      this.ws = new WebSocket(this.config.url);

      // Set up event handlers
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

      // Wait for connection to open
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 10000);

        if (this.ws) {
          this.ws.onopen = () => {
            clearTimeout(timeout);
            this.handleOpen();
            resolve();
          };

          this.ws.onerror = () => {
            clearTimeout(timeout);
            reject(new Error('Connection failed'));
          };
        }
      });

    } catch (error) {
      this.state.connecting = false;
      this.state.lastError = error instanceof Error ? error.message : 'Unknown error';
      this.updateState();
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.log('Disconnecting WebSocket');
    
    // Clear timers
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    
    if (this.messageQueueTimer) {
      clearInterval(this.messageQueueTimer);
      this.messageQueueTimer = null;
    }

    // Close WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.state.connected = false;
    this.state.connecting = false;
    this.state.reconnectAttempts = 0;
    this.updateState();
  }

  /**
   * Send message to WebSocket server
   */
  send(message: WebSocketMessage): void {
    if (!this.state.connected || !this.ws) {
      this.log('Not connected, queuing message');
      this.queueMessage(message);
      return;
    }

    try {
      const messageWithTimestamp = {
        ...message,
        timestamp: message.timestamp || new Date().toISOString(),
        id: message.id || this.generateMessageId(),
      };

      this.ws.send(JSON.stringify(messageWithTimestamp));
      this.log('Message sent:', messageWithTimestamp);
    } catch (error) {
      this.log('Failed to send message:', error);
      this.queueMessage(message);
      this.handleError(error instanceof Error ? error : new Error('Send failed'));
    }
  }

  /**
   * Subscribe to specific event type
   */
  on(eventType: string, handler: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    this.eventHandlers.get(eventType)!.push(handler);
    this.log(`Subscribed to event: ${eventType}`);
  }

  /**
   * Unsubscribe from event type
   */
  off(eventType: string, handler?: WebSocketEventHandler): void {
    if (!this.eventHandlers.has(eventType)) return;

    if (handler) {
      const handlers = this.eventHandlers.get(eventType)!;
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    } else {
      this.eventHandlers.delete(eventType);
    }

    this.log(`Unsubscribed from event: ${eventType}`);
  }

  /**
   * Set error handler
   */
  onError(handler: WebSocketErrorHandler): void {
    this.errorHandler = handler;
  }

  /**
   * Set state change handler
   */
  onStateChange(handler: WebSocketStateHandler): void {
    this.stateHandler = handler;
  }

  /**
   * Get current state
   */
  getState(): WebSocketClientState {
    return { ...this.state };
  }

  // Private methods

  private handleOpen(): void {
    this.log('WebSocket connected');
    this.state.connected = true;
    this.state.connecting = false;
    this.state.reconnectAttempts = 0;
    this.state.lastError = null;
    this.updateState();

    // Start heartbeat
    this.startHeartbeat();

    // Process message queue
    this.processMessageQueue();
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.log('Message received:', message);

      // Handle heartbeat
      if (message.type === 'heartbeat') {
        this.state.lastHeartbeat = new Date().toISOString();
        this.updateState();
        return;
      }

      // Emit to event handlers
      const handlers = this.eventHandlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            this.log('Error in event handler:', error);
          }
        });
      }

      // Update execution store if it's an execution event
      if (message.type.startsWith('execution_') || message.type.startsWith('node_')) {
        const executionStore = useExecutionStore.getState();
        if (executionStore.addEvent) {
          executionStore.addEvent({
            id: message.id || this.generateMessageId(),
            run_id: message.data?.run_id || '',
            node_id: message.data?.node_id,
            event_type: message.type,
            level: message.data?.level || 'info',
            message: message.data?.message || '',
            data: message.data,
            timestamp: message.timestamp,
            duration_ms: message.data?.duration_ms,
            token_count: message.data?.token_count,
          });
        }
      }

    } catch (error) {
      this.log('Failed to parse message:', error);
      this.handleError(error instanceof Error ? error : new Error('Message parsing failed'));
    }
  }

  private handleClose(event: CloseEvent): void {
    this.log('WebSocket closed:', event.code, event.reason);
    this.state.connected = false;
    this.state.connecting = false;
    this.updateState();

    // Clear heartbeat
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    // Attempt reconnection if not explicitly closed
    if (event.code !== 1000 && this.state.reconnectAttempts < this.config.reconnectAttempts) {
      this.attemptReconnect();
    }
  }

  private handleError(error: Event | Error): void {
    const errorMessage = error instanceof Error ? error.message : 'Unknown WebSocket error';
    this.log('WebSocket error:', errorMessage);
    
    this.state.lastError = errorMessage;
    this.updateState();

    if (this.errorHandler) {
      this.errorHandler(error instanceof Error ? error : new Error(errorMessage));
    }
  }

  private attemptReconnect(): void {
    this.state.reconnectAttempts++;
    this.updateState();

    const delay = this.config.reconnectInterval * Math.pow(2, this.state.reconnectAttempts - 1);
    this.log(`Attempting reconnection ${this.state.reconnectAttempts}/${this.config.reconnectAttempts} in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(error => {
        this.log('Reconnection failed:', error);
        if (this.state.reconnectAttempts >= this.config.reconnectAttempts) {
          this.log('Max reconnection attempts reached');
          this.state.lastError = 'Max reconnection attempts reached';
          this.updateState();
        }
      });
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.state.connected && this.ws) {
        this.send({
          type: 'heartbeat',
          data: { timestamp: new Date().toISOString() },
          timestamp: new Date().toISOString(),
        });
      }
    }, this.config.heartbeatInterval);
  }

  private queueMessage(message: WebSocketMessage): void {
    // Add to queue
    this.state.messageQueue.push({
      ...message,
      timestamp: message.timestamp || new Date().toISOString(),
      id: message.id || this.generateMessageId(),
    });

    // Limit queue size
    if (this.state.messageQueue.length > this.config.messageQueueSize) {
      this.state.messageQueue.shift();
    }

    this.log('Message queued. Queue size:', this.state.messageQueue.length);
  }

  private processMessageQueue(): void {
    if (this.messageQueueTimer) {
      clearInterval(this.messageQueueTimer);
    }

    this.messageQueueTimer = setInterval(() => {
      if (this.state.messageQueue.length > 0 && this.state.connected && this.ws) {
        const message = this.state.messageQueue.shift();
        if (message) {
          try {
            this.ws.send(JSON.stringify(message));
            this.log('Queued message sent:', message);
          } catch (error) {
            this.log('Failed to send queued message:', error);
            // Re-queue the message
            this.state.messageQueue.unshift(message);
          }
        }
      }
    }, 100);
  }

  private updateState(): void {
    if (this.stateHandler) {
      this.stateHandler(this.getState());
    }
  }

  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private log(...args: any[]): void {
    if (this.config.debug) {
      console.log('[WebSocketClient]', ...args);
    }
  }
}

// Singleton instance for the application
let wsClient: WebSocketClient | null = null;

/**
 * Get or create WebSocket client instance
 */
export function getWebSocketClient(config?: Partial<WebSocketConfig>): WebSocketClient {
  if (!wsClient) {
    const defaultConfig: WebSocketConfig = {
      url: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
      debug: process.env.NODE_ENV === 'development',
    };

    wsClient = new WebSocketClient({ ...defaultConfig, ...config });
  }

  return wsClient;
}

/**
 * Disconnect WebSocket client
 */
export function disconnectWebSocket(): void {
  if (wsClient) {
    wsClient.disconnect();
    wsClient = null;
  }
}

// Types are already exported above, no need to re-export