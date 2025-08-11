'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Search as SearchIcon,
  BarChart as BarChartIcon,
  PieChart as PieChartIcon,
  ShowChart as LineChartIcon,
  TableChart as TableIcon,
  List as ListIcon,
  Dashboard as MetricIcon
} from '@mui/icons-material';

interface Widget {
  id: string;
  name: string;
  title: string;
  description: string;
  widget_type: string;
  chart_type?: string;
  is_public: boolean;
  created_by_username: string;
}

interface WidgetSelectorProps {
  onSelect: (widget: Widget) => void;
}

export function WidgetSelector({ onSelect }: WidgetSelectorProps) {
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [filteredWidgets, setFilteredWidgets] = useState<Widget[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTab, setSelectedTab] = useState(0);

  const widgetTypes = [
    { value: 'all', label: 'All Widgets' },
    { value: 'metric', label: 'Metrics', icon: <MetricIcon /> },
    { value: 'chart', label: 'Charts', icon: <LineChartIcon /> },
    { value: 'table', label: 'Tables', icon: <TableIcon /> },
    { value: 'list', label: 'Lists', icon: <ListIcon /> }
  ];

  useEffect(() => {
    fetchWidgets();
  }, []);

  useEffect(() => {
    filterWidgets();
  }, [widgets, searchTerm, selectedTab]);

  const fetchWidgets = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/admin/dashboard/widgets/');
      if (!response.ok) {
        throw new Error('Failed to fetch widgets');
      }
      const data = await response.json();
      setWidgets(data.results || data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const filterWidgets = () => {
    let filtered = widgets;

    // Filter by widget type
    if (selectedTab > 0) {
      const selectedType = widgetTypes[selectedTab].value;
      filtered = filtered.filter(widget => widget.widget_type === selectedType);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(widget =>
        widget.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        widget.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        widget.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredWidgets(filtered);
  };

  const getWidgetIcon = (widget: Widget) => {
    switch (widget.widget_type) {
      case 'metric':
        return <MetricIcon color="primary" />;
      case 'chart':
        switch (widget.chart_type) {
          case 'bar':
            return <BarChartIcon color="primary" />;
          case 'pie':
            return <PieChartIcon color="primary" />;
          default:
            return <LineChartIcon color="primary" />;
        }
      case 'table':
        return <TableIcon color="primary" />;
      case 'list':
        return <ListIcon color="primary" />;
      default:
        return <MetricIcon color="primary" />;
    }
  };

  const getWidgetTypeLabel = (type: string) => {
    const widgetType = widgetTypes.find(t => t.value === type);
    return widgetType ? widgetType.label : type;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Search and Filter */}
      <Box mb={3}>
        <TextField
          fullWidth
          placeholder="Search widgets..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            )
          }}
          sx={{ mb: 2 }}
        />

        <Tabs
          value={selectedTab}
          onChange={(_, newValue) => setSelectedTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {widgetTypes.map((type, index) => (
            <Tab
              key={type.value}
              label={type.label}
              icon={type.icon}
              iconPosition="start"
            />
          ))}
        </Tabs>
      </Box>

      {/* Widget Grid */}
      <Grid container spacing={2}>
        {filteredWidgets.map((widget) => (
          <Grid item xs={12} sm={6} md={4} key={widget.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                '&:hover': {
                  transform: 'translateY(-2px)',
                  boxShadow: 4
                }
              }}
            >
              <CardContent sx={{ flex: 1 }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  {getWidgetIcon(widget)}
                  <Typography variant="h6" component="h3" noWrap>
                    {widget.title}
                  </Typography>
                </Box>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    mb: 2,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: 'vertical'
                  }}
                >
                  {widget.description || 'No description available'}
                </Typography>

                <Box display="flex" gap={1} flexWrap="wrap">
                  <Chip
                    label={getWidgetTypeLabel(widget.widget_type)}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                  {widget.chart_type && (
                    <Chip
                      label={widget.chart_type}
                      size="small"
                      variant="outlined"
                    />
                  )}
                  {widget.is_public && (
                    <Chip
                      label="Public"
                      size="small"
                      color="success"
                      variant="outlined"
                    />
                  )}
                </Box>

                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Created by: {widget.created_by_username}
                </Typography>
              </CardContent>

              <CardActions>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={() => onSelect(widget)}
                >
                  Add Widget
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Empty State */}
      {filteredWidgets.length === 0 && (
        <Box
          display="flex"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          minHeight="200px"
          textAlign="center"
        >
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No widgets found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {searchTerm
              ? 'Try adjusting your search terms or filters'
              : 'No widgets are available for the selected category'
            }
          </Typography>
        </Box>
      )}
    </Box>
  );
}