/**
 * API route for handling frontend logs
 * Forwards logs to Django backend
 */

import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const correlationId = request.headers.get('x-correlation-id');
    
    // Forward logs to Django backend
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/logs/frontend-logs/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(correlationId && { 'X-Correlation-ID': correlationId })
      },
      body: JSON.stringify(body)
    });
    
    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }
    
    const result = await response.json();
    
    return NextResponse.json(result, { status: 201 });
    
  } catch (error) {
    console.error('Error forwarding logs to backend:', error);
    
    return NextResponse.json(
      { error: 'Failed to process logs' },
      { status: 500 }
    );
  }
}