'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Sync } from 'lucide-react';

export default function SyncJobsList() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Sync className="h-5 w-5" />
              Sync Jobs
            </CardTitle>
            <CardDescription>
              Manage scheduled data synchronization jobs
            </CardDescription>
          </div>
          <Button>
            <Sync className="h-4 w-4 mr-2" />
            New Sync Job
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-muted-foreground">
          Sync jobs management interface will be implemented here
        </div>
      </CardContent>
    </Card>
  );
}