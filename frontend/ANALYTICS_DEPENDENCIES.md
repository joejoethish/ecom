# Analytics Dependencies

The sales analytics components require the following additional dependencies to be installed:

## Required Dependencies

```bash
npm install recharts date-fns
```

## Dependencies Used

- **recharts**: For advanced chart visualizations (LineChart, BarChart, AreaChart, etc.)
- **date-fns**: For date manipulation and formatting utilities

## Current Implementation

The current implementation uses placeholder components for charts to avoid dependency issues. To enable full functionality:

1. Install the dependencies listed above
2. Uncomment the chart imports in the analytics components
3. Replace the placeholder chart divs with the actual chart components

## Chart Components Used

- `LineChart` - For trend analysis and time series data
- `BarChart` - For comparative metrics and growth analysis  
- `AreaChart` - For forecast visualization with confidence intervals
- `PieChart` - For distribution and attribution analysis

## Date Utilities Used

- `format()` - For date formatting in charts and displays
- `subDays()`, `addMonths()` - For date range calculations
- `startOfMonth()`, `endOfMonth()` - For period-based analysis

## Alternative Implementation

If you prefer not to add these dependencies, the current implementation provides:

- Simple HTML date inputs for date range selection
- Placeholder chart areas with descriptive text
- All data processing and API integration functionality
- Fully functional dashboard without visual charts

The analytics functionality is complete - only the visual chart rendering requires the additional dependencies.