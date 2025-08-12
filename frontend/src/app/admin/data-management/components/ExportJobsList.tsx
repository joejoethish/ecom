'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Download } from 'lucide-react';

export default function ExportJobsList() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Download className="h-5 w-5" />
              Export Jobs
            </CardTitle>
            <CardDescription>
              Manage data export operations and download files
            </CardDescription>
          </div>
          <Button>
            <Download className="h-4 w-4 mr-2" />
            New Export
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-muted-foreground">
          Export jobs management interface will be implemented here
        </div>
      </CardContent>
    </Card>
  );
}