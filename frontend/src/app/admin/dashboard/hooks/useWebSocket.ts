'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

interface WebSocketMessage {
  event_type: string;
  dashboard_id?: string;
  widget_id?: string;
  user_id?: string;
  data: any;
  timestamp: string;
}

export function useWebSocket() {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    try {
      // In a real implementation, you would use WebSocket
      // For now, we'll simulate with polling
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/`;
      
      // Simulate WebSocket connection with polling
      const pollForUpdates = async () => {
        try {
          const response = await fetch('/api/admin/dashboard/realtime/');
          if (response.ok) {
            const data = await response.json();
            setIsConnected(true);
            setLastUpdate(data.timestamp);
            
            if (data.updates && data.updates.length > 0) {
              setMessages(prev => [...prev, ...data.updates].slice(-50)); // Keep last 50 messages
            }
            
            reconnectAttempts.current = 0;
          }
        } catch (error) {
          console.error('Failed to poll for updates:', error);
          setIsConnected(false);
          
          // Retry with exponential backoff
          if (reconnectAttempts.current < maxReconnectAttempts) {
            const delay = Math.pow(2, reconnectAttempts.current) * 1000;
            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectAttempts.current++;
              connect();
            }, delay);
          }
        }
      };

      // Poll every 30 seconds
      const interval = setInterval(pollForUpdates, 30000);
      
      // Initial poll
      pollForUpdates();

      return () => {
        clearInterval(interval);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      setIsConnected(false);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      // Fallback to HTTP API
      fetch('/api/admin/dashboard/realtime/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(message)
      }).catch(error => {
        console.error('Failed to send message:', error);
      });
    }
  }, []);

  // Track user activity
  const trackActivity = useCallback((action: string, metadata: any = {}) => {
    sendMessage({
      action,
      metadata,
      timestamp: new Date().toISOString()
    });
  }, [sendMessage]);

  useEffect(() => {
    const cleanup = connect();
    
    return () => {
      if (cleanup) cleanup();
      disconnect();
    };
  }, [connect, disconnect]);

  // Track page visibility to pause/resume connection
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        disconnect();
      } else {
        connect();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastUpdate,
    messages,
    sendMessage,
    trackActivity,
    connect,
    disconnect
  };
}