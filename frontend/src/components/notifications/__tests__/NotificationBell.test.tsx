import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import NotificationBell from '../NotificationBell';
import notificationReducer from '@/store/slices/notificationSlice';

// Mock store
const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      notifications: notificationReducer,
    },
    preloadedState: {
      notifications: {
        notifications: [],
        currentNotification: null,
        unreadCount: 0,
        preferences: [],
        settings: null,
        stats: null,
        isNotificationCenterOpen: false,
        filters: {},
        loading: {
          notifications: false,
          preferences: false,
          stats: false,
          settings: false,
          markingAsRead: false,
          updatingPreferences: false,
        },
        error: {
          notifications: null,
          preferences: null,
          stats: null,
          settings: null,
          markingAsRead: null,
          updatingPreferences: null,
        },
        ...initialState,
      },
    },
  });
};

describe(&apos;NotificationBell&apos;, () => {
  it(&apos;renders without crashing&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    expect(screen.getByRole(&apos;button&apos;)).toBeInTheDocument();
  });

  it(&apos;shows unread count badge when there are unread notifications&apos;, () => {
    const store = createMockStore({
      unreadCount: 5,
    });
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    expect(screen.getByText(&apos;5&apos;)).toBeInTheDocument();
  });

  it(&apos;does not show badge when showBadge is false&apos;, () => {
    const store = createMockStore({
      unreadCount: 5,
    });
    
    render(
      <Provider store={store}>
        <NotificationBell showBadge={false} />
      </Provider>
    );
    
    expect(screen.queryByText(&apos;5&apos;)).not.toBeInTheDocument();
  });

  it(&apos;shows 99+ when unread count exceeds 99&apos;, () => {
    const store = createMockStore({
      unreadCount: 150,
    });
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    expect(screen.getByText(&apos;99+&apos;)).toBeInTheDocument();
  });

  it(&apos;toggles notification center when clicked&apos;, () => {
    const store = createMockStore();
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    const button = screen.getByRole(&apos;button&apos;);
    fireEvent.click(button);
    
    // Check if the notification center state changed
    const state = store.getState();
    expect(state.notifications.isNotificationCenterOpen).toBe(true);
  });

  it(&apos;has correct accessibility attributes&apos;, () => {
    const store = createMockStore({
      unreadCount: 3,
    });
    
    render(
      <Provider store={store}>
        <NotificationBell />
      </Provider>
    );
    
    const button = screen.getByRole(&apos;button&apos;);
    expect(button).toHaveAttribute(&apos;aria-label&apos;, &apos;Notifications (3 unread)&apos;);
  });

  it(&apos;applies correct size classes&apos;, () => {
    const store = createMockStore();
    
      <Provider store={store}>
        <NotificationBell size="sm" />
      </Provider>
    );
    
    let button = screen.getByRole(&apos;button&apos;);
    expect(button).toHaveClass(&apos;h-8&apos;, &apos;w-8&apos;);
    
    rerender(
      <Provider store={store}>
        <NotificationBell size="lg" />
      </Provider>
    );
    
    button = screen.getByRole('button');
    expect(button).toHaveClass('h-12', 'w-12');
  });
});