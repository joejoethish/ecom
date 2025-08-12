'use client';

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Popover,
  Button,
  TextField,
  Grid
} from '@mui/material';

interface ColorPickerProps {
  label: string;
  value: string;
  onChange: (color: string) => void;
}

const predefinedColors = [
  '#1976d2', '#dc004e', '#388e3c', '#f57c00',
  '#7b1fa2', '#d32f2f', '#1976d2', '#00796b',
  '#5d4037', '#616161', '#455a64', '#e65100',
  '#ad1457', '#6a1b9a', '#283593', '#1565c0',
  '#0277bd', '#00838f', '#00695c', '#2e7d32',
  '#558b2f', '#9e9d24', '#f9a825', '#ff8f00',
  '#ef6c00', '#d84315', '#bf360c', '#3e2723'
];

export function ColorPicker({ label, value, onChange }: ColorPickerProps) {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null);
  const [customColor, setCustomColor] = useState(value);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleColorSelect = (color: string) => {
    onChange(color);
    setCustomColor(color);
    handleClose();
  };

  const handleCustomColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const color = event.target.value;
    setCustomColor(color);
    if (color.match(/^#[0-9A-F]{6}$/i)) {
      onChange(color);
    }
  };

  const open = Boolean(anchorEl);

  return (
    <Box>
      <Typography variant="caption" display="block" gutterBottom>
        {label}
      </Typography>
      <Button
        variant="outlined"
        onClick={handleClick}
        sx={{
          width: '100%',
          height: 40,
          backgroundColor: value,
          border: '2px solid #ddd',
          '&:hover': {
            backgroundColor: value,
            opacity: 0.8
          }
        }}
      >
        <Box
          sx={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: getContrastColor(value),
            fontWeight: 'bold',
            fontSize: '0.75rem'
          }}
        >
          {value}
        </Box>
      </Button>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
      >
        <Box sx={{ p: 2, width: 280 }}>
          <Typography variant="subtitle2" gutterBottom>
            Choose Color
          </Typography>
          
          <Grid container spacing={1} sx={{ mb: 2 }}>
            {predefinedColors.map((color) => (
              <Grid {...({ item: true, xs: 3 } as any)} key={color}>
                <Button
                  onClick={() => handleColorSelect(color)}
                  sx={{
                    width: '100%',
                    height: 40,
                    minWidth: 0,
                    backgroundColor: color,
                    border: value === color ? '3px solid #000' : '1px solid #ddd',
                    '&:hover': {
                      backgroundColor: color,
                      opacity: 0.8
                    }
                  }}
                />
              </Grid>
            ))}
          </Grid>

          <TextField
            fullWidth
            label="Custom Color"
            value={customColor}
            onChange={handleCustomColorChange}
            placeholder="#000000"
            size="small"
            InputProps={{
              startAdornment: (
                <Box
                  sx={{
                    width: 20,
                    height: 20,
                    backgroundColor: customColor,
                    border: '1px solid #ddd',
                    borderRadius: 1,
                    mr: 1
                  }}
                />
              )
            }}
          />
        </Box>
      </Popover>
    </Box>
  );
}

function getContrastColor(hexColor: string): string {
  // Convert hex to RGB
  const r = parseInt(hexColor.slice(1, 3), 16);
  const g = parseInt(hexColor.slice(3, 5), 16);
  const b = parseInt(hexColor.slice(5, 7), 16);
  
  // Calculate luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  
  // Return black or white based on luminance
  return luminance > 0.5 ? '#000000' : '#ffffff';
}