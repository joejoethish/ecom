import { useEffect, useState, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import useWebSocket, { ConnectionState } from './useWebSocket';
import { getAuthToken } from '@/utils/auth';

interface ChatMessage {
  id: string;
  content: string;
  userId: string;
  timestamp: string;
  isRead: boolean;
}

interface UseChatReturn {
  isConnected: boolean;
  messages: ChatMessage[];
  sendMessage: (content: string) => boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * Custom hook for real-time chat functionality
 * @param roomId Chat room ID
 * @returns Chat state and methods
 */
export const useChat = (roomId: string): UseChatReturn => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Get current user from Redux store
  const user = useSelector((state: RootState) => state.auth.user);
  
  // Get API URL from environment
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace(/^http/, 'ws');
  
  // Get auth token for WebSocket authentication
  const token = getAuthToken();
  
  // Connect to WebSocket for chat
  const { connectionState, lastMessage, sendMessage } = useWebSocket({
    url: `${wsUrl}/ws/chat/${roomId}/?token=${token}`,
    autoConnect: true,
    reconnectOnUnmount: false,
    onOpen: () => {
      setError(null);
      setIsLoading(false);
    },
    onClose: () => {
      setError('Connection to chat server lost. Please refresh the page.');
    },
    onError: () => {
      setError('Error connecting to chat server.');
    },
  });
  
  // Process incoming chat messages
  useEffect(() => {
    if (lastMessage && lastMessage.message) {
      const newMessage: ChatMessage = {
        id: lastMessage.id || Date.now().toString(),
        content: lastMessage.message,
        userId: lastMessage.user_id,
        timestamp: lastMessage.timestamp || new Date().toISOString(),
        isRead: lastMessage.user_id === user?.id, // Mark own messages as read
      };
      
      setMessages((prevMessages) => [...prevMessages, newMessage]);
    }
  }, [lastMessage, user?.id]);
  
  // Send a chat message
  const sendChatMessage = useCallback(
    (content: string): boolean => {
      if (!user) {
        setError('You must be logged in to send messages');
        return false;
      }
      
      return sendMessage({
        message: content,
        user_id: user.id,
        timestamp: new Date().toISOString(),
      });
    },
    [sendMessage, user]
  );
  
  // Determine if connected
  const isConnected = connectionState === ConnectionState.OPEN;
  
  return {
    isConnected,
    messages,
    sendMessage: sendChatMessage,
    isLoading,
    error,
  };
};

export default useChat;