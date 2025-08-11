import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ChatMessage {
  id: string;
  content: string;
  userId: string;
  timestamp: string;
  isRead: boolean;
}

export interface ChatRoom {
  id: string;
  name: string;
  roomType: string;
  participants: string[];
  messages: ChatMessage[];
  unreadCount: number;
  isActive: boolean;
}

interface ChatState {
  rooms: Record<string, ChatRoom>;
  activeRoomId: string | null;
  loading: boolean;
  error: string | null;
}

interface UpdateChatMessagesPayload {
  roomId: string;
  message: ChatMessage;
}

  rooms: {},
  activeRoomId: null,
  loading: false,
  error: null,
};

const chatSlice = createSlice({
  name: &apos;chat&apos;,
  initialState,
  reducers: {
    setChatRooms: (state, action: PayloadAction<ChatRoom[]>) => {
      action.payload.forEach((room) => {
        rooms[room.id] = room;
      });
      state.rooms = rooms;
      state.loading = false;
      state.error = null;
    },
    setActiveRoom: (state, action: PayloadAction<string>) => {
      state.activeRoomId = action.payload;
      
      // Mark all messages in the active room as read
      if (state.rooms[action.payload]) {
        state.rooms[action.payload].messages.forEach((message) => {
          message.isRead = true;
        });
        state.rooms[action.payload].unreadCount = 0;
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
      state.loading = false;
    },
    updateChatMessages: (state, action: PayloadAction<UpdateChatMessagesPayload>) => {
      
      if (!state.rooms[roomId]) {
        // Room doesn&apos;t exist yet, create it
        state.rooms[roomId] = {
          id: roomId,
          name: `Room ${roomId}`,
          roomType: &apos;UNKNOWN&apos;,
          participants: [],
          messages: [],
          unreadCount: 0,
          isActive: false,
        };
      }
      
      // Add message to room
      state.rooms[roomId].messages.push(message);
      
      // Update unread count if not the active room
      if (state.activeRoomId !== roomId && !message.isRead) {
        state.rooms[roomId].unreadCount += 1;
      }
    },
    markRoomMessagesRead: (state, action: PayloadAction<string>) => {
      const roomId = action.payload;
      
      if (state.rooms[roomId]) {
        state.rooms[roomId].messages.forEach((message) => {
          message.isRead = true;
        });
        state.rooms[roomId].unreadCount = 0;
      }
    },
    clearChat: (state) => {
      state.rooms = {};
      state.activeRoomId = null;
      state.loading = false;
      state.error = null;
    },
  },
});

export const {
  setChatRooms,
  setActiveRoom,
  setLoading,
  setError,
  updateChatMessages,
  markRoomMessagesRead,
  clearChat,
} = chatSlice.actions;

export default chatSlice.reducer;