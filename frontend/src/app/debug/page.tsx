/**
 * E2E Debugging Dashboard - Main Page
 * 
 * This page provides a comprehensive debugging interface for the e-commerce platform,
 * including system health monitoring, workflow tracing, and error analysis.
 */

'use client';

import React from 'react';
import { DebuggingDashboard } from '@/components/debugging/DebuggingDashboard';

export default function DebugPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <DebuggingDashboard />
    </div>
  );
}