'use client';

import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import {
    Grid,
    Card,
    CardContent,
    Typography,
    Box,
    Button,
    IconButton,
    Menu,
    MenuItem,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Fab,
    Tooltip,
    Alert,
    Snackbar
} from '@mui/material';
import {
    Add as AddIcon,
    Settings as SettingsIcon,
    Share as ShareIcon,
    Download as DownloadIcon,
    Refresh as RefreshIcon,
    MoreVert as MoreVertIcon,
    DragIndicator as DragIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    Fullscreen as FullscreenIcon
} from '@mui/icons-material';
import { DashboardWidget } from './components/DashboardWidget';
import { WidgetSelector } from './components/WidgetSelector';
import { DashboardSettings } from './components/DashboardSettings';
import { useDashboard } from './hooks/useDashboard';
import { useWebSocket } from './hooks/useWebSocket';

interface WidgetPosition {
    id: string;
    x: number;
    y: number;
    width: number;
    height: number;
    widget: any;
}

export default function DashboardPage() {
    const {
        layout,
        widgets,
        loading,
        error,
        updateLayout,
        addWidget,
        removeWidget,
        updateWidgetPosition,
        refreshWidget,
        exportDashboard
    } = useDashboard();

    const { isConnected, lastUpdate } = useWebSocket();

    const [widgetSelectorOpen, setWidgetSelectorOpen] = useState(false);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [selectedWidget, setSelectedWidget] = useState<string | null>(null);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' as 'info' | 'success' | 'warning' | 'error' });

    // Auto-refresh widgets every 5 minutes
    useEffect(() => {
        const interval = setInterval(() => {
            widgets.forEach(widget => {
                if (widget.auto_refresh) {
                    refreshWidget(widget.id);
                }
            });
        }, 5 * 60 * 1000);

        return () => clearInterval(interval);
    }, [widgets, refreshWidget]);

    const handleDragEnd = (result: any) => {
        if (!result.destination) return;

        const sourceIndex = result.source.index;
        const destinationIndex = result.destination.index;

        if (sourceIndex === destinationIndex) return;

        const newWidgets = Array.from(widgets);
        const [reorderedWidget] = newWidgets.splice(sourceIndex, 1);
        newWidgets.splice(destinationIndex, 0, reorderedWidget);

        // Update positions
        newWidgets.forEach((widget, index) => {
            updateWidgetPosition(widget.id, {
                order: index,
                x: widget.x,
                y: widget.y,
                width: widget.width,
                height: widget.height
            });
        });
    };

    const handleWidgetMenuClick = (event: React.MouseEvent<HTMLElement>, widgetId: string) => {
        setAnchorEl(event.currentTarget);
        setSelectedWidget(widgetId);
    };

    const handleWidgetMenuClose = () => {
        setAnchorEl(null);
        setSelectedWidget(null);
    };

    const handleAddWidget = () => {
        setWidgetSelectorOpen(true);
    };

    const handleWidgetSelect = (widget: any) => {
        addWidget(widget.id, {
            x: 0,
            y: 0,
            width: 2,
            height: 2
        });
        setWidgetSelectorOpen(false);
        setSnackbar({
            open: true,
            message: 'Widget added successfully',
            severity: 'success'
        });
    };

    const handleRemoveWidget = () => {
        if (selectedWidget) {
            removeWidget(selectedWidget);
            setSnackbar({
                open: true,
                message: 'Widget removed successfully',
                severity: 'success'
            });
        }
        handleWidgetMenuClose();
    };

    const handleRefreshWidget = () => {
        if (selectedWidget) {
            refreshWidget(selectedWidget);
            setSnackbar({
                open: true,
                message: 'Widget refreshed',
                severity: 'info'
            });
        }
        handleWidgetMenuClose();
    };

    const handleExportDashboard = async () => {
        try {
            await exportDashboard('pdf');
            setSnackbar({
                open: true,
                message: 'Dashboard exported successfully',
                severity: 'success'
            });
        } catch (error) {
            setSnackbar({
                open: true,
                message: 'Export failed',
                severity: 'error'
            });
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <Typography>Loading dashboard...</Typography>
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
        <Box sx={{ p: 3 }}>
            {/* Dashboard Header */}
            <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
                <Box>
                    <Typography variant="h4" component="h1" gutterBottom>
                        {layout?.name || 'Dashboard'}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body2" color="text.secondary">
                            Last updated: {lastUpdate ? new Date(lastUpdate).toLocaleTimeString() : 'Never'}
                        </Typography>
                        {isConnected && (
                            <Box
                                sx={{
                                    width: 8,
                                    height: 8,
                                    borderRadius: '50%',
                                    backgroundColor: 'success.main'
                                }}
                            />
                        )}
                    </Box>
                </Box>

                <Box display="flex" gap={1}>
                    <Tooltip title="Refresh All">
                        <IconButton onClick={() => window.location.reload()}>
                            <RefreshIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Export Dashboard">
                        <IconButton onClick={handleExportDashboard}>
                            <DownloadIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Share Dashboard">
                        <IconButton>
                            <ShareIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="Dashboard Settings">
                        <IconButton onClick={() => setSettingsOpen(true)}>
                            <SettingsIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {/* Dashboard Grid */}
            <DragDropContext onDragEnd={handleDragEnd}>
                <Droppable droppableId="dashboard" direction="vertical">
                    {(provided) => (
                        <Grid
                            container
                            spacing={2}
                            {...provided.droppableProps}
                            ref={provided.innerRef}
                        >
                            {widgets.map((widget, index) => (
                                <Draggable
                                    key={widget.id}
                                    draggableId={widget.id}
                                    index={index}
                                >
                                    {(provided, snapshot) => (
                                        <Grid
                                            item
                                            xs={12}
                                            sm={widget.width * 2}
                                            md={widget.width * 2}
                                            lg={widget.width}
                                            ref={provided.innerRef}
                                            {...provided.draggableProps}
                                        >
                                            <Card
                                                sx={{
                                                    height: widget.height * 200,
                                                    position: 'relative',
                                                    opacity: snapshot.isDragging ? 0.8 : 1,
                                                    transform: snapshot.isDragging ? 'rotate(5deg)' : 'none',
                                                    transition: 'all 0.2s ease'
                                                }}
                                            >
                                                <Box
                                                    sx={{
                                                        position: 'absolute',
                                                        top: 8,
                                                        right: 8,
                                                        zIndex: 1,
                                                        display: 'flex',
                                                        gap: 0.5
                                                    }}
                                                >
                                                    <IconButton
                                                        size="small"
                                                        {...provided.dragHandleProps}
                                                        sx={{ cursor: 'grab' }}
                                                    >
                                                        <DragIcon fontSize="small" />
                                                    </IconButton>
                                                    <IconButton
                                                        size="small"
                                                        onClick={(e) => handleWidgetMenuClick(e, widget.id)}
                                                    >
                                                        <MoreVertIcon fontSize="small" />
                                                    </IconButton>
                                                </Box>

                                                <CardContent sx={{ height: '100%', p: 2 }}>
                                                    <DashboardWidget
                                                        widget={widget}
                                                        onRefresh={() => refreshWidget(widget.id)}
                                                    />
                                                </CardContent>
                                            </Card>
                                        </Grid>
                                    )}
                                </Draggable>
                            ))}
                            {provided.placeholder}
                        </Grid>
                    )}
                </Droppable>
            </DragDropContext>

            {/* Empty State */}
            {widgets.length === 0 && (
                <Box
                    display="flex"
                    flexDirection="column"
                    alignItems="center"
                    justifyContent="center"
                    minHeight="400px"
                    textAlign="center"
                >
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                        No widgets added yet
                    </Typography>
                    <Typography variant="body2" color="text.secondary" mb={3}>
                        Add your first widget to get started with your dashboard
                    </Typography>
                    <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={handleAddWidget}
                    >
                        Add Widget
                    </Button>
                </Box>
            )}

            {/* Floating Add Button */}
            {widgets.length > 0 && (
                <Fab
                    color="primary"
                    aria-label="add widget"
                    sx={{ position: 'fixed', bottom: 24, right: 24 }}
                    onClick={handleAddWidget}
                >
                    <AddIcon />
                </Fab>
            )}

            {/* Widget Context Menu */}
            <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleWidgetMenuClose}
            >
                <MenuItem onClick={handleRefreshWidget}>
                    <RefreshIcon fontSize="small" sx={{ mr: 1 }} />
                    Refresh
                </MenuItem>
                <MenuItem onClick={() => { }}>
                    <EditIcon fontSize="small" sx={{ mr: 1 }} />
                    Edit
                </MenuItem>
                <MenuItem onClick={() => { }}>
                    <FullscreenIcon fontSize="small" sx={{ mr: 1 }} />
                    Fullscreen
                </MenuItem>
                <MenuItem onClick={handleRemoveWidget} sx={{ color: 'error.main' }}>
                    <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
                    Remove
                </MenuItem>
            </Menu>

            {/* Widget Selector Dialog */}
            <Dialog
                open={widgetSelectorOpen}
                onClose={() => setWidgetSelectorOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>Add Widget</DialogTitle>
                <DialogContent>
                    <WidgetSelector onSelect={handleWidgetSelect} />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setWidgetSelectorOpen(false)}>
                        Cancel
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Dashboard Settings Dialog */}
            <Dialog
                open={settingsOpen}
                onClose={() => setSettingsOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>Dashboard Settings</DialogTitle>
                <DialogContent>
                    <DashboardSettings
                        layout={layout}
                        onSave={(settings) => {
                            updateLayout(settings);
                            setSettingsOpen(false);
                            setSnackbar({
                                open: true,
                                message: 'Settings saved successfully',
                                severity: 'success'
                            });
                        }}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setSettingsOpen(false)}>
                        Cancel
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Snackbar for notifications */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={4000}
                onClose={() => setSnackbar({ ...snackbar, open: false })}
            >
                <Alert
                    onClose={() => setSnackbar({ ...snackbar, open: false })}
                    severity={snackbar.severity}
                    sx={{ width: '100%' }}
                >
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
}