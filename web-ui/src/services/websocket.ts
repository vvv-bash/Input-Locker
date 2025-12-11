import { io, Socket } from 'socket.io-client';
import type { WSMessage, Device, Timer, SystemStatus, Statistics } from '../types';

type MessageHandler = (message: WSMessage) => void;
type DeviceUpdateHandler = (device: Device) => void;
type DevicesUpdateHandler = (devices: Device[]) => void;
type TimerUpdateHandler = (timer: Timer) => void;
type StatusUpdateHandler = (status: SystemStatus) => void;
type StatsUpdateHandler = (stats: Statistics) => void;
type HotkeyActionHandler = (action: { type: string; action: string }) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  
  // Typed event handlers
  private deviceHandlers: Set<DeviceUpdateHandler> = new Set();
  private devicesHandlers: Set<DevicesUpdateHandler> = new Set();
  private timerHandlers: Set<TimerUpdateHandler> = new Set();
  private statusHandlers: Set<StatusUpdateHandler> = new Set();
  private statsHandlers: Set<StatsUpdateHandler> = new Set();
  private hotkeyHandlers: Set<HotkeyActionHandler> = new Set();

  connect(): void {
    if (this.socket?.connected) return;

    // Detect if running in Electron
    const isElectron = typeof window !== 'undefined' && 
      (window.location.protocol === 'file:' || 
       (window as any).electronAPI !== undefined ||
       navigator.userAgent.toLowerCase().includes('electron'));

    // In Electron, use direct URL to API server
    const wsUrl = isElectron 
      ? 'http://127.0.0.1:8080'
      : (import.meta.env.VITE_WS_URL || 'http://localhost:8080');
    
    console.log('WebSocket Configuration:', { isElectron, wsUrl });
    
    this.socket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.reconnectAttempts++;
    });

    // Handle incoming messages
    this.socket.on('message', (data: WSMessage) => {
      this.handleMessage(data);
    });

    // Specific event handlers
    this.socket.on('device_update', (device: Device) => {
      this.deviceHandlers.forEach(handler => handler(device));
    });

    this.socket.on('devices_update', (devices: Device[]) => {
      console.log('📡 Received devices_update:', devices.length, 'devices');
      this.devicesHandlers.forEach(handler => handler(devices));
    });

    this.socket.on('timer_update', (timer: Timer) => {
      this.timerHandlers.forEach(handler => handler(timer));
    });

    this.socket.on('status_update', (status: SystemStatus) => {
      this.statusHandlers.forEach(handler => handler(status));
    });

    this.socket.on('stats_update', (stats: Statistics) => {
      this.statsHandlers.forEach(handler => handler(stats));
    });

    this.socket.on('hotkey_action', (data: { type: string; action: string }) => {
      console.log('🔑 Received hotkey_action:', data);
      this.hotkeyHandlers.forEach(handler => handler(data));
    });

    // Legacy event name support
    this.socket.on('system_status', (status: SystemStatus) => {
      this.statusHandlers.forEach(handler => handler(status));
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  private handleMessage(message: WSMessage): void {
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => handler(message));
    }
  }

  // Generic message subscription
  subscribe(messageType: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(messageType)) {
      this.handlers.set(messageType, new Set());
    }
    this.handlers.get(messageType)!.add(handler);

    return () => {
      this.handlers.get(messageType)?.delete(handler);
    };
  }

  // Typed subscriptions
  onDeviceUpdate(handler: DeviceUpdateHandler): () => void {
    this.deviceHandlers.add(handler);
    return () => this.deviceHandlers.delete(handler);
  }

  onDevicesUpdate(handler: DevicesUpdateHandler): () => void {
    this.devicesHandlers.add(handler);
    return () => this.devicesHandlers.delete(handler);
  }

  onTimerUpdate(handler: TimerUpdateHandler): () => void {
    this.timerHandlers.add(handler);
    return () => this.timerHandlers.delete(handler);
  }

  onStatusUpdate(handler: StatusUpdateHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  onHotkeyAction(handler: HotkeyActionHandler): () => void {
    this.hotkeyHandlers.add(handler);
    return () => this.hotkeyHandlers.delete(handler);
  }

  onStatsUpdate(handler: StatsUpdateHandler): () => void {
    this.statsHandlers.add(handler);
    return () => this.statsHandlers.delete(handler);
  }

  // Send message
  emit(event: string, data: unknown): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

// Singleton instance
export const wsService = new WebSocketService();
export default wsService;
