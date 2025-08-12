'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Switch,
  FormControlLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Divider,
  Grid,
  Card,
  CardContent,
  Slider,
  Alert
} from '@mui/material';
import { ColorPicker } from './ColorPicker';

interface DashboardLayout {
  id: string;
  name: string;
  description: string;
  is_shared: boolean;
  shared_with_roles: string[];
  layout_config: any;
}

interface DashboardSettingsProps {
  layout: DashboardLayout | null;
  onSave: (settings: any) => void;
}

export function DashboardSettings({ layout, onSave }: DashboardSettingsProps) {
  const [settings, setSettings] = useState({
    name: '',
    description: '',
    is_shared: false,
    shared_with_roles: [] as string[],
    theme: 'light',
    grid_size: 12,
    compact_mode: false,
    auto_refresh: true,
    refresh_interval: 300,
    show_animations: true,
    background_color: '#ffffff',
    primary_color: '#1976d2',
    secondary_color: '#dc004e'
  });

  const [userPreferences, setUserPreferences] = useState({
    theme: 'light',
    show_animations: true,
    auto_refresh: true,
    refresh_interval: 300,
    show_notifications: true,
    notification_position: 'top-right',
    date_format: 'YYYY-MM-DD',
    time_format: 'HH:mm:ss',
    timezone: 'UTC',
    currency: 'USD'
  });

  const availableRoles = [
    'super_admin',
    'admin',
    'manager',
    'analyst',
    'support',
    'viewer'
  ];

  const themes = [
    { value: 'light', label: 'Light' },
    { value: 'dark', label: 'Dark' },
    { value: 'auto', label: 'Auto (System)' }
  ];

  const notificationPositions = [
    { value: 'top-left', label: 'Top Left' },
    { value: 'top-right', label: 'Top Right' },
    { value: 'bottom-left', label: 'Bottom Left' },
    { value: 'bottom-right', label: 'Bottom Right' }
  ];

  const dateFormats = [
    { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
    { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
    { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
    { value: 'DD-MM-YYYY', label: 'DD-MM-YYYY' }
  ];

  const timeFormats = [
    { value: 'HH:mm:ss', label: '24 Hour (HH:mm:ss)' },
    { value: 'hh:mm:ss A', label: '12 Hour (hh:mm:ss AM/PM)' },
    { value: 'HH:mm', label: '24 Hour (HH:mm)' },
    { value: 'hh:mm A', label: '12 Hour (hh:mm AM/PM)' }
  ];

  const currencies = [
    { value: 'USD', label: 'US Dollar ($)' },
    { value: 'EUR', label: 'Euro (€)' },
    { value: 'GBP', label: 'British Pound (£)' },
    { value: 'JPY', label: 'Japanese Yen (¥)' },
    { value: 'CAD', label: 'Canadian Dollar (C$)' },
    { value: 'AUD', label: 'Australian Dollar (A$)' }
  ];

  useEffect(() => {
    if (layout) {
      setSettings({
        name: layout.name || '',
        description: layout.description || '',
        is_shared: layout.is_shared || false,
        shared_with_roles: layout.shared_with_roles || [],
        theme: layout.layout_config?.theme || 'light',
        grid_size: layout.layout_config?.grid_size || 12,
        compact_mode: layout.layout_config?.compact_mode || false,
        auto_refresh: layout.layout_config?.auto_refresh || true,
        refresh_interval: layout.layout_config?.refresh_interval || 300,
        show_animations: layout.layout_config?.show_animations || true,
        background_color: layout.layout_config?.background_color || '#ffffff',
        primary_color: layout.layout_config?.primary_color || '#1976d2',
        secondary_color: layout.layout_config?.secondary_color || '#dc004e'
      });
    }
    
    fetchUserPreferences();
  }, [layout]);

  const fetchUserPreferences = async () => {
    try {
      const response = await fetch('/api/admin/dashboard/preferences/my/');
      if (response.ok) {
        const data = await response.json();
        setUserPreferences({
          theme: data.theme || 'light',
          show_animations: data.show_animations || true,
          auto_refresh: data.auto_refresh || true,
          refresh_interval: data.refresh_interval || 300,
          show_notifications: data.show_notifications || true,
          notification_position: data.notification_position || 'top-right',
          date_format: data.date_format || 'YYYY-MM-DD',
          time_format: data.time_format || 'HH:mm:ss',
          timezone: data.timezone || 'UTC',
          currency: data.currency || 'USD'
        });
      }
    } catch (error) {
      console.error('Failed to fetch user preferences:', error);
    }
  };

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handlePreferenceChange = (key: string, value: any) => {
    setUserPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSave = async () => {
    try {
      // Save dashboard settings
      const dashboardSettings = {
        ...settings,
        layout_config: {
          theme: settings.theme,
          grid_size: settings.grid_size,
          compact_mode: settings.compact_mode,
          auto_refresh: settings.auto_refresh,
          refresh_interval: settings.refresh_interval,
          show_animations: settings.show_animations,
          background_color: settings.background_color,
          primary_color: settings.primary_color,
          secondary_color: settings.secondary_color
        }
      };

      // Save user preferences
      await fetch('/api/admin/dashboard/preferences/my/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userPreferences)
      });

      onSave(dashboardSettings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  return (
    <Box sx={{ maxHeight: '70vh', overflow: 'auto' }}>
      <Grid container spacing={3}>
        {/* Dashboard Settings */}
        <Grid {...({ item: true, xs: 12, md: 6 } as any)}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Dashboard Settings
              </Typography>

              <TextField
                fullWidth
                label="Dashboard Name"
                value={settings.name}
                onChange={(e) => handleSettingChange('name', e.target.value)}
                margin="normal"
              />

              <TextField
                fullWidth
                label="Description"
                value={settings.description}
                onChange={(e) => handleSettingChange('description', e.target.value)}
                margin="normal"
                multiline
                rows={3}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.is_shared}
                    onChange={(e) => handleSettingChange('is_shared', e.target.checked)}
                  />
                }
                label="Share Dashboard"
                sx={{ mt: 2 }}
              />

              {settings.is_shared && (
                <FormControl fullWidth margin="normal">
                  <InputLabel>Share with Roles</InputLabel>
                  <Select
                    multiple
                    value={settings.shared_with_roles}
                    onChange={(e) => handleSettingChange('shared_with_roles', e.target.value)}
                    renderValue={(selected) => selected.join(', ')}
                  >
                    {availableRoles.map((role) => (
                      <MenuItem key={role} value={role}>
                        {role.replace('_', ' ').toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              <Divider sx={{ my: 3 }} />

              <Typography variant="subtitle1" gutterBottom>
                Layout Configuration
              </Typography>

              <Box sx={{ mt: 2 }}>
                <Typography gutterBottom>Grid Size: {settings.grid_size}</Typography>
                <Slider
                  value={settings.grid_size}
                  onChange={(_, value) => handleSettingChange('grid_size', value)}
                  min={6}
                  max={24}
                  step={2}
                  marks
                  valueLabelDisplay="auto"
                />
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.compact_mode}
                    onChange={(e) => handleSettingChange('compact_mode', e.target.checked)}
                  />
                }
                label="Compact Mode"
                sx={{ mt: 2 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.auto_refresh}
                    onChange={(e) => handleSettingChange('auto_refresh', e.target.checked)}
                  />
                }
                label="Auto Refresh"
                sx={{ mt: 1 }}
              />

              {settings.auto_refresh && (
                <Box sx={{ mt: 2 }}>
                  <Typography gutterBottom>
                    Refresh Interval: {settings.refresh_interval}s
                  </Typography>
                  <Slider
                    value={settings.refresh_interval}
                    onChange={(_, value) => handleSettingChange('refresh_interval', value)}
                    min={30}
                    max={3600}
                    step={30}
                    valueLabelDisplay="auto"
                  />
                </Box>
              )}

              <Divider sx={{ my: 3 }} />

              <Typography variant="subtitle1" gutterBottom>
                Appearance
              </Typography>

              <FormControl fullWidth margin="normal">
                <InputLabel>Theme</InputLabel>
                <Select
                  value={settings.theme}
                  onChange={(e) => handleSettingChange('theme', e.target.value)}
                >
                  {themes.map((theme) => (
                    <MenuItem key={theme.value} value={theme.value}>
                      {theme.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.show_animations}
                    onChange={(e) => handleSettingChange('show_animations', e.target.checked)}
                  />
                }
                label="Show Animations"
                sx={{ mt: 2 }}
              />

              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Colors
                </Typography>
                <Grid container spacing={2}>
                  <Grid {...({ item: true, xs: 4 } as any)}>
                    <ColorPicker
                      label="Background"
                      value={settings.background_color}
                      onChange={(color) => handleSettingChange('background_color', color)}
                    />
                  </Grid>
                  <Grid {...({ item: true, xs: 4 } as any)}>
                    <ColorPicker
                      label="Primary"
                      value={settings.primary_color}
                      onChange={(color) => handleSettingChange('primary_color', color)}
                    />
                  </Grid>
                  <Grid {...({ item: true, xs: 4 } as any)}>
                    <ColorPicker
                      label="Secondary"
                      value={settings.secondary_color}
                      onChange={(color) => handleSettingChange('secondary_color', color)}
                    />
                  </Grid>
                </Grid>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* User Preferences */}
        <Grid {...({ item: true, xs: 12, md: 6 } as any)}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                User Preferences
              </Typography>

              <FormControl fullWidth margin="normal">
                <InputLabel>Theme</InputLabel>
                <Select
                  value={userPreferences.theme}
                  onChange={(e) => handlePreferenceChange('theme', e.target.value)}
                >
                  {themes.map((theme) => (
                    <MenuItem key={theme.value} value={theme.value}>
                      {theme.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={userPreferences.show_animations}
                    onChange={(e) => handlePreferenceChange('show_animations', e.target.checked)}
                  />
                }
                label="Show Animations"
                sx={{ mt: 2 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={userPreferences.auto_refresh}
                    onChange={(e) => handlePreferenceChange('auto_refresh', e.target.checked)}
                  />
                }
                label="Auto Refresh"
                sx={{ mt: 1 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={userPreferences.show_notifications}
                    onChange={(e) => handlePreferenceChange('show_notifications', e.target.checked)}
                  />
                }
                label="Show Notifications"
                sx={{ mt: 1 }}
              />

              {userPreferences.show_notifications && (
                <FormControl fullWidth margin="normal">
                  <InputLabel>Notification Position</InputLabel>
                  <Select
                    value={userPreferences.notification_position}
                    onChange={(e) => handlePreferenceChange('notification_position', e.target.value)}
                  >
                    {notificationPositions.map((position) => (
                      <MenuItem key={position.value} value={position.value}>
                        {position.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              )}

              <Divider sx={{ my: 3 }} />

              <Typography variant="subtitle1" gutterBottom>
                Data Formatting
              </Typography>

              <FormControl fullWidth margin="normal">
                <InputLabel>Date Format</InputLabel>
                <Select
                  value={userPreferences.date_format}
                  onChange={(e) => handlePreferenceChange('date_format', e.target.value)}
                >
                  {dateFormats.map((format) => (
                    <MenuItem key={format.value} value={format.value}>
                      {format.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth margin="normal">
                <InputLabel>Time Format</InputLabel>
                <Select
                  value={userPreferences.time_format}
                  onChange={(e) => handlePreferenceChange('time_format', e.target.value)}
                >
                  {timeFormats.map((format) => (
                    <MenuItem key={format.value} value={format.value}>
                      {format.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Timezone"
                value={userPreferences.timezone}
                onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                margin="normal"
                placeholder="UTC"
              />

              <FormControl fullWidth margin="normal">
                <InputLabel>Currency</InputLabel>
                <Select
                  value={userPreferences.currency}
                  onChange={(e) => handlePreferenceChange('currency', e.target.value)}
                >
                  {currencies.map((currency) => (
                    <MenuItem key={currency.value} value={currency.value}>
                      {currency.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button variant="contained" onClick={handleSave}>
          Save Settings
        </Button>
      </Box>
    </Box>
  );
}