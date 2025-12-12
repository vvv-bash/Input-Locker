import axios, { AxiosInstance } from 'axios';
import type { 
  Device, 
  Statistics, 
  Timer, 
  SystemStatus, 
  Settings,
  WhitelistEntry,
  ApiResponse 
} from '../types';

// Detect if running in Electron
const isElectron = typeof window !== 'undefined' && 
  (window.location.protocol === 'file:' || 
   (window as any).electronAPI !== undefined ||
   navigator.userAgent.toLowerCase().includes('electron'));

// In Electron, use full URL with /api prefix. In browser dev, use proxy
const API_BASE_URL = isElectron 
  ? 'http://127.0.0.1:8080' 
  : (import.meta.env.VITE_API_URL || '');

console.log('API Configuration:', { isElectron, API_BASE_URL });

class DeviceBlockerAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  // ═══════════════════════════════════════════════════════════════
  // Device Management
  // ═══════════════════════════════════════════════════════════════

  async getDevices(): Promise<Device[]> {
    const response = await this.client.get<ApiResponse<Device[]>>('/api/devices/list');
    return response.data.data || [];
  }

  async getDeviceStatus(devicePath: string): Promise<Device> {
    const response = await this.client.get<ApiResponse<Device>>(`/api/devices/status/${encodeURIComponent(devicePath)}`);
    if (!response.data.data) throw new Error('Device not found');
    return response.data.data;
  }

  async blockDevice(devicePath: string): Promise<boolean> {
    const response = await this.client.post<ApiResponse<boolean>>('/api/device/block', { 
      device_path: devicePath 
    });
    return response.data.success;
  }

  async unblockDevice(devicePath: string): Promise<boolean> {
    const response = await this.client.post<ApiResponse<boolean>>('/api/device/unblock', { 
      device_path: devicePath 
    });
    return response.data.success;
  }

  async toggleBlock(devicePath: string): Promise<boolean> {
    const response = await this.client.post<ApiResponse<boolean>>('/api/device/toggle', { 
      device_path: devicePath 
    });
    return response.data.success;
  }

  async blockAll(): Promise<boolean> {
    const response = await this.client.post<ApiResponse<boolean>>('/api/devices/block-all');
    return response.data.success;
  }

  async unblockAll(): Promise<boolean> {
    const response = await this.client.post<ApiResponse<boolean>>('/api/devices/unblock-all');
    return response.data.success;
  }

  async lockByTypes(types: string[]): Promise<boolean> {
    const response = await this.client.post<ApiResponse<{ types: string[] }>>('/api/devices/lock-by-types', { 
      types 
    });
    return response.data.success;
  }

  // ═══════════════════════════════════════════════════════════════
  // Timer Management
  // ═══════════════════════════════════════════════════════════════

  async setTimer(minutes: number, devicePath?: string): Promise<Timer> {
    const response = await this.client.post<ApiResponse<Timer>>('/api/timer/set', {
      minutes,
      device_path: devicePath,
    });
    if (!response.data.data) throw new Error('Failed to set timer');
    return response.data.data;
  }

  async cancelTimer(): Promise<boolean> {
    const response = await this.client.post<ApiResponse<boolean>>('/api/timer/cancel');
    return response.data.success;
  }

  async getTimerStatus(): Promise<Timer> {
    const response = await this.client.get<ApiResponse<Timer>>('/api/timer/status');
    return response.data.data || { active: false, remainingSeconds: 0, totalSeconds: 0 };
  }

  // ═══════════════════════════════════════════════════════════════
  // Statistics
  // ═══════════════════════════════════════════════════════════════

  async getStats(): Promise<Statistics> {
    const response = await this.client.get<ApiResponse<Statistics>>('/api/stats');
    return response.data.data || {
      totalBlockedTime: 0,
      blockedEvents: 0,
      blockHistory: [],
      deviceStats: [],
    };
  }

  async clearStats(): Promise<boolean> {
    const response = await this.client.post<ApiResponse<boolean>>('/api/stats/clear');
    return response.data.success;
  }

  // ═══════════════════════════════════════════════════════════════
  // System Status
  // ═══════════════════════════════════════════════════════════════

  async getSystemStatus(): Promise<SystemStatus> {
    const response = await this.client.get<ApiResponse<SystemStatus>>('/api/system/status');
    return response.data.data || {
      running: false,
      activeBlocks: 0,
      connectedDevices: 0,
      uptime: 0,
    };
  }

  // ═══════════════════════════════════════════════════════════════
  // Settings
  // ═══════════════════════════════════════════════════════════════

  async getSettings(): Promise<Settings> {
    const response = await this.client.get<ApiResponse<Settings>>('/api/settings');
    return response.data.data || {
      hotkey: ['Ctrl', 'Alt', 'L'],
      emergencyPattern: ['Up', 'Up', 'Down', 'Down', 'Enter'],
      autoBlockOnStart: false,
      showNotifications: true,
      allowTouchscreenUnlock: true,
      theme: 'dark',
    };
  }

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    const response = await this.client.put<ApiResponse<Settings>>('/api/settings', settings);
    if (!response.data.data) throw new Error('Failed to update settings');
    return response.data.data;
  }

  // ═══════════════════════════════════════════════════════════════
  // Whitelist
  // ═══════════════════════════════════════════════════════════════

  async getWhitelist(): Promise<WhitelistEntry[]> {
    const response = await this.client.get<ApiResponse<WhitelistEntry[]>>('/api/whitelist');
    return response.data.data || [];
  }

  async addToWhitelist(entry: Omit<WhitelistEntry, 'id'>): Promise<WhitelistEntry> {
    const response = await this.client.post<ApiResponse<WhitelistEntry>>('/api/whitelist', entry);
    if (!response.data.data) throw new Error('Failed to add to whitelist');
    return response.data.data;
  }

  async removeFromWhitelist(id: string): Promise<boolean> {
    const response = await this.client.delete<ApiResponse<boolean>>(`/api/whitelist/${id}`);
    return response.data.success;
  }

  async toggleWhitelistEntry(id: string): Promise<WhitelistEntry> {
    const response = await this.client.post<ApiResponse<WhitelistEntry>>(`/api/whitelist/${id}/toggle`);
    if (!response.data.data) throw new Error('Failed to toggle whitelist entry');
    return response.data.data;
  }
}

// Singleton instance
export const api = new DeviceBlockerAPI();
export default api;
