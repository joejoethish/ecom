'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale,
  TimeScale,
  LogarithmicScale,
} from 'chart.js';
import {
  Line,
  Bar,
  Pie,
  Doughnut,
  Radar,
  PolarArea,
  Scatter,
  Bubble,
} from 'react-chartjs-2';
import annotationPlugin from 'chartjs-plugin-annotation';
import zoomPlugin from 'chartjs-plugin-zoom';
import { ResizeObserver } from '@juggle/resize-observer';
import { 
  Download, 
  Share2, 
  Settings, 
  Maximize2, 
  RefreshCw, 
  MessageCircle,
  Bookmark,
  TrendingUp,
  Filter,
  Eye,
  EyeOff
} from 'lucide-react';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale,
  TimeScale,
  LogarithmicScale,
  annotationPlugin,
  zoomPlugin
);

interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
    fill?: boolean;
    tension?: number;
    pointRadius?: number;
    pointHoverRadius?: number;
  }>;
  metadata?: {
    total_points?: number;
    chart_type?: string;
    [key: string]: any;
  };
}

interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'radar' | 'polarArea' | 'scatter' | 'bubble';
  responsive?: boolean;
  maintainAspectRatio?: boolean;
  plugins?: {
    title?: {
      display: boolean;
      text: string;
      font?: {
        size: number;
        weight: string;
      };
    };
    legend?: {
      display: boolean;
      position: 'top' | 'bottom' | 'left' | 'right';
    };
    tooltip?: {
      enabled: boolean;
      mode?: string;
      intersect?: boolean;
    };
    zoom?: {
      zoom: {
        wheel: {
          enabled: boolean;
        };
        pinch: {
          enabled: boolean;
        };
        mode: 'x' | 'y' | 'xy';
      };
      pan: {
        enabled: boolean;
        mode: 'x' | 'y' | 'xy';
      };
    };
    annotation?: {
      annotations: any[];
    };
  };
  scales?: {
    x?: {
      type?: string;
      display?: boolean;
      title?: {
        display: boolean;
        text: string;
      };
      grid?: {
        display: boolean;
      };
    };
    y?: {
      type?: string;
      display?: boolean;
      title?: {
        display: boolean;
        text: string;
      };
      grid?: {
        display: boolean;
      };
      beginAtZero?: boolean;
    };
  };
  interaction?: {
    mode: string;
    intersect: boolean;
  };
  animation?: {
    duration: number;
    easing: string;
  };
}

interface ChartAnnotation {
  id: string;
  type: 'note' | 'highlight' | 'trend_line' | 'threshold' | 'event';
  title: string;
  content: string;
  position: {
    x?: number;
    y?: number;
    xValue?: string | number;
    yValue?: number;
  };
  style: {
    color?: string;
    backgroundColor?: string;
    borderColor?: string;
    borderWidth?: number;
  };
  isVisible: boolean;
}

interface ChartComment {
  id: string;
  content: string;
  author: {
    id: string;
    name: string;
    avatar?: string;
  };
  position?: {
    x: number;
    y: number;
  };
  createdAt: string;
  isResolved: boolean;
  replies?: ChartComment[];
}

interface AdvancedChartProps {
  id: string;
  title: string;
  description?: string;
  data: ChartData;
  config: ChartConfig;
  theme?: 'light' | 'dark' | 'custom';
  colors?: string[];
  customCss?: string;
  isRealTime?: boolean;
  refreshInterval?: number;
  annotations?: ChartAnnotation[];
  comments?: ChartComment[];
  onDataUpdate?: (data: ChartData) => void;
  onConfigChange?: (config: ChartConfig) => void;
  onExport?: (format: string, options: any) => void;
  onShare?: (shareType: string, options: any) => void;
  onDrillDown?: (dimension: string, value: string) => void;
  onAnnotationAdd?: (annotation: Omit<ChartAnnotation, 'id'>) => void;
  onCommentAdd?: (comment: Omit<ChartComment, 'id' | 'author' | 'createdAt'>) => void;
  className?: string;
  height?: number;
  width?: number;
  showControls?: boolean;
  showAnnotations?: boolean;
  showComments?: boolean;
  allowDrillDown?: boolean;
  allowZoom?: boolean;
  allowPan?: boolean;
  isEmbedded?: boolean;
}

const AdvancedChart: React.FC<AdvancedChartProps> = ({
  id,
  title,
  description,
  data,
  config,
  theme = 'light',
  colors = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6'],
  customCss,
  isRealTime = false,
  refreshInterval = 30000,
  annotations = [],
  comments = [],
  onDataUpdate,
  onConfigChange,
  onExport,
  onShare,
  onDrillDown,
  onAnnotationAdd,
  onCommentAdd,
  className = '',
  height = 400,
  width,
  showControls = true,
  showAnnotations = true,
  showComments = true,
  allowDrillDown = true,
  allowZoom = true,
  allowPan = true,
  isEmbedded = false,
}) => {
  const chartRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [showAnnotationPanel, setShowAnnotationPanel] = useState(false);
  const [showCommentPanel, setShowCommentPanel] = useState(false);
  const [visibleAnnotations, setVisibleAnnotations] = useState<string[]>(
    annotations.filter(a => a.isVisible).map(a => a.id)
  );
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [performanceMetrics, setPerformanceMetrics] = useState({
    loadTime: 0,
    renderTime: 0,
    dataSize: 0,
  });

  // Real-time data updates
  useEffect(() => {
    if (!isRealTime || !refreshInterval) return;

    const interval = setInterval(async () => {
      try {
        setIsLoading(true);
        const startTime = performance.now();
        
        // Fetch updated data
        const response = await fetch(`/api/admin/charts/${id}/data/`);
        const updatedData = await response.json();
        
        const loadTime = performance.now() - startTime;
        
        if (onDataUpdate) {
          onDataUpdate(updatedData);
        }
        
        setLastUpdate(new Date());
        setPerformanceMetrics(prev => ({
          ...prev,
          loadTime,
          dataSize: JSON.stringify(updatedData).length,
        }));
        
      } catch (err) {
        setError('Failed to update chart data');
        console.error('Chart data update error:', err);
      } finally {
        setIsLoading(false);
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [id, isRealTime, refreshInterval, onDataUpdate]);

  // Performance monitoring
  useEffect(() => {
    const startTime = performance.now();
    
    const observer = new ResizeObserver(() => {
      if (chartRef.current) {
        chartRef.current.resize();
      }
    });

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    // Record render time
    const renderTime = performance.now() - startTime;
    setPerformanceMetrics(prev => ({
      ...prev,
      renderTime,
    }));

    return () => {
      observer.disconnect();
    };
  }, [data, config]);

  // Chart configuration with theme and customization
  const chartConfig = useMemo(() => {
    const baseConfig = {
      ...config,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        ...config.plugins,
        legend: {
          display: true,
          position: 'top' as const,
          ...config.plugins?.legend,
        },
        tooltip: {
          enabled: true,
          mode: 'index' as const,
          intersect: false,
          ...config.plugins?.tooltip,
          callbacks: {
            afterLabel: (context: any) => {
              if (allowDrillDown && onDrillDown) {
                return 'Click to drill down';
              }
              return '';
            },
          },
        },
        zoom: allowZoom ? {
          zoom: {
            wheel: {
              enabled: true,
            },
            pinch: {
              enabled: true,
            },
            mode: 'xy' as const,
          },
          pan: {
            enabled: allowPan,
            mode: 'xy' as const,
          },
          ...config.plugins?.zoom,
        } : undefined,
        annotation: showAnnotations && annotations.length > 0 ? {
          annotations: annotations
            .filter(annotation => visibleAnnotations.includes(annotation.id))
            .map(annotation => ({
              type: annotation.type === 'threshold' ? 'line' : 'label',
              ...annotation.position,
              content: annotation.title,
              backgroundColor: annotation.style.backgroundColor || 'rgba(255, 255, 255, 0.8)',
              borderColor: annotation.style.borderColor || '#000',
              borderWidth: annotation.style.borderWidth || 1,
            })),
        } : undefined,
      },
      scales: {
        ...config.scales,
        x: {
          display: true,
          grid: {
            display: theme !== 'dark',
            color: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          },
          ticks: {
            color: theme === 'dark' ? '#fff' : '#000',
          },
          ...config.scales?.x,
        },
        y: {
          display: true,
          beginAtZero: true,
          grid: {
            display: theme !== 'dark',
            color: theme === 'dark' ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
          },
          ticks: {
            color: theme === 'dark' ? '#fff' : '#000',
          },
          ...config.scales?.y,
        },
      },
      onClick: (event: any, elements: any[]) => {
        if (elements.length > 0 && allowDrillDown && onDrillDown) {
          const element = elements[0];
          const datasetIndex = element.datasetIndex;
          const index = element.index;
          const label = data.labels[index];
          const dataset = data.datasets[datasetIndex];
          
          onDrillDown(dataset.label, label);
        }
      },
      animation: {
        duration: 750,
        easing: 'easeInOutQuart',
        ...config.animation,
      },
    };

    return baseConfig;
  }, [config, theme, allowZoom, allowPan, showAnnotations, annotations, visibleAnnotations, allowDrillDown, onDrillDown, data]);

  // Apply custom colors to datasets
  const processedData = useMemo(() => {
    const processed = { ...data };
    
    processed.datasets = data.datasets.map((dataset, index) => ({
      ...dataset,
      backgroundColor: dataset.backgroundColor || colors[index % colors.length],
      borderColor: dataset.borderColor || colors[index % colors.length],
    }));

    return processed;
  }, [data, colors]);

  // Chart component selection
  const ChartComponent = useMemo(() => {
    switch (config.type) {
      case 'line':
        return Line;
      case 'bar':
        return Bar;
      case 'pie':
        return Pie;
      case 'doughnut':
        return Doughnut;
      case 'radar':
        return Radar;
      case 'polarArea':
        return PolarArea;
      case 'scatter':
        return Scatter;
      case 'bubble':
        return Bubble;
      default:
        return Line;
    }
  }, [config.type]);

  // Export functionality
  const handleExport = useCallback(async (format: string) => {
    if (!chartRef.current || !onExport) return;

    try {
      setIsLoading(true);
      
      const canvas = chartRef.current.canvas;
      const options = {
        width: canvas.width,
        height: canvas.height,
        backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
      };

      if (format === 'png' || format === 'jpg') {
        const dataUrl = canvas.toDataURL(`image/${format}`);
        const link = document.createElement('a');
        link.download = `${title}.${format}`;
        link.href = dataUrl;
        link.click();
      } else {
        await onExport(format, options);
      }
    } catch (err) {
      setError('Failed to export chart');
      console.error('Export error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [chartRef, onExport, title, theme]);

  // Share functionality
  const handleShare = useCallback(async (shareType: string) => {
    if (!onShare) return;

    try {
      setIsLoading(true);
      await onShare(shareType, {
        title,
        description,
        chartType: config.type,
      });
    } catch (err) {
      setError('Failed to share chart');
      console.error('Share error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [onShare, title, description, config.type]);

  // Annotation visibility toggle
  const toggleAnnotation = useCallback((annotationId: string) => {
    setVisibleAnnotations(prev => 
      prev.includes(annotationId)
        ? prev.filter(id => id !== annotationId)
        : [...prev, annotationId]
    );
  }, []);

  // Fullscreen toggle
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  }, []);

  // Manual refresh
  const handleRefresh = useCallback(async () => {
    if (!onDataUpdate) return;

    try {
      setIsLoading(true);
      const response = await fetch(`/api/admin/charts/${id}/data/`);
      const updatedData = await response.json();
      onDataUpdate(updatedData);
      setLastUpdate(new Date());
    } catch (err) {
      setError('Failed to refresh chart data');
      console.error('Refresh error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [id, onDataUpdate]);

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <div className="text-red-800">
            <h3 className="text-sm font-medium">Chart Error</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`relative bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 ${className}`}
      style={{ height: height, width: width }}
    >
      {/* Custom CSS */}
      {customCss && <style>{customCss}</style>}
      
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>
          {description && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {description}
            </p>
          )}
        </div>
        
        {/* Controls */}
        {showControls && !isEmbedded && (
          <div className="flex items-center space-x-2">
            {isRealTime && (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-400' : 'bg-green-400'}`} />
                <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
              </div>
            )}
            
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              title="Filters"
            >
              <Filter className="w-4 h-4" />
            </button>
            
            {showAnnotations && annotations.length > 0 && (
              <button
                onClick={() => setShowAnnotationPanel(!showAnnotationPanel)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                title="Annotations"
              >
                <Bookmark className="w-4 h-4" />
              </button>
            )}
            
            {showComments && (
              <button
                onClick={() => setShowCommentPanel(!showCommentPanel)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                title="Comments"
              >
                <MessageCircle className="w-4 h-4" />
                {comments.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                    {comments.length}
                  </span>
                )}
              </button>
            )}
            
            <div className="relative">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                title="Export & Share"
              >
                <Download className="w-4 h-4" />
              </button>
              
              {showSettings && (
                <div className="absolute right-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-10">
                  <div className="p-2">
                    <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Export</div>
                    <button
                      onClick={() => handleExport('png')}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    >
                      Export as PNG
                    </button>
                    <button
                      onClick={() => handleExport('pdf')}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    >
                      Export as PDF
                    </button>
                    <button
                      onClick={() => handleExport('csv')}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    >
                      Export Data (CSV)
                    </button>
                    
                    <div className="border-t border-gray-200 dark:border-gray-700 my-2"></div>
                    <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Share</div>
                    <button
                      onClick={() => handleShare('public_link')}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    >
                      Create Public Link
                    </button>
                    <button
                      onClick={() => handleShare('embed_code')}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                    >
                      Get Embed Code
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            <button
              onClick={toggleFullscreen}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              title="Fullscreen"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
      
      {/* Chart Container */}
      <div className="relative flex-1 p-4" style={{ height: height - 80 }}>
        {isLoading && (
          <div className="absolute inset-0 bg-white dark:bg-gray-800 bg-opacity-75 flex items-center justify-center z-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        <ChartComponent
          ref={chartRef}
          data={processedData}
          options={chartConfig}
        />
        
        {/* Annotations Overlay */}
        {showAnnotations && annotations.length > 0 && (
          <div className="absolute inset-0 pointer-events-none">
            {annotations
              .filter(annotation => visibleAnnotations.includes(annotation.id))
              .map(annotation => (
                <div
                  key={annotation.id}
                  className="absolute bg-yellow-100 border border-yellow-300 rounded px-2 py-1 text-xs pointer-events-auto"
                  style={{
                    left: annotation.position.x || 0,
                    top: annotation.position.y || 0,
                  }}
                  title={annotation.content}
                >
                  {annotation.title}
                </div>
              ))}
          </div>
        )}
      </div>
      
      {/* Annotation Panel */}
      {showAnnotationPanel && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-20">
          <div className="p-4">
            <h4 className="font-medium text-gray-900 dark:text-white mb-3">Annotations</h4>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {annotations.map(annotation => (
                <div key={annotation.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded">
                  <div className="flex-1">
                    <div className="text-sm font-medium">{annotation.title}</div>
                    <div className="text-xs text-gray-500">{annotation.content}</div>
                  </div>
                  <button
                    onClick={() => toggleAnnotation(annotation.id)}
                    className="ml-2 p-1 text-gray-400 hover:text-gray-600"
                  >
                    {visibleAnnotations.includes(annotation.id) ? (
                      <Eye className="w-4 h-4" />
                    ) : (
                      <EyeOff className="w-4 h-4" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Comment Panel */}
      {showCommentPanel && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-20">
          <div className="p-4">
            <h4 className="font-medium text-gray-900 dark:text-white mb-3">Comments</h4>
            <div className="space-y-3 max-h-60 overflow-y-auto">
              {comments.map(comment => (
                <div key={comment.id} className="p-3 bg-gray-50 dark:bg-gray-700 rounded">
                  <div className="flex items-start space-x-2">
                    <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs">
                      {comment.author.name.charAt(0)}
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-medium">{comment.author.name}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                        {comment.content}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(comment.createdAt).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Performance Info (Development) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="absolute bottom-2 left-2 text-xs text-gray-400 bg-black bg-opacity-50 px-2 py-1 rounded">
          Load: {performanceMetrics.loadTime.toFixed(0)}ms | 
          Render: {performanceMetrics.renderTime.toFixed(0)}ms | 
          Size: {(performanceMetrics.dataSize / 1024).toFixed(1)}KB
        </div>
      )}
    </div>
  );
};

export default AdvancedChart;