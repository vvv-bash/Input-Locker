// Device types
export type DeviceType = 'keyboard' | 'mouse' | 'touchpad' | 'touchscreen' | 'other';

export interface Device {
  path: string;
  name: string;
  type: DeviceType;
  blocked: boolean;
  vendor?: string;
  capabilities?: string[];
  phys?: string;
}

// Statistics types
export interface Statistics {
  totalBlockedTime: number; // in seconds
  blockedEvents: number;
  blockHistory: BlockEvent[];
  deviceStats: DeviceStats[];
}

export interface BlockEvent {
  timestamp: string;
  devicePath: string;
  deviceName: string;
  action: 'block' | 'unblock';
  duration?: number;
}

export interface DeviceStats {
  devicePath: string;
  deviceName: string;
  totalBlocks: number;
  totalBlockedTime: number;
}

// Timer types
export interface Timer {
  active: boolean;
  remainingSeconds: number;
  totalSeconds: number;
  devicePath?: string;
}

// System status
export interface SystemStatus {
  running: boolean;
  activeBlocks: number;
  connectedDevices: number;
  uptime: number;
}

// API Response types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// WebSocket message types
export type WSMessageType = 
  | 'device_update'
  | 'block_status'
  | 'timer_update'
  | 'system_status'
  | 'error';

export interface WSMessage {
  type: WSMessageType;
  payload: unknown;
  timestamp: string;
}

// Settings types
export interface Settings {
  hotkey: string[];
  emergencyPattern: string[];
  autoBlockOnStart: boolean;
  showNotifications: boolean;
  allowTouchscreenUnlock: boolean;
  theme: 'dark' | 'light';
}

// Whitelist types
export interface WhitelistEntry {
  id: string;
  type: 'device' | 'application';
  name: string;
  path?: string;
  enabled: boolean;
}
