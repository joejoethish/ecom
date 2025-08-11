'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Shield } from 'lucide-react';

export default function BackupsList() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Data Backups
            </CardTitle>
            <CardDescription>
              Manage data backups and restore operations
            </CardDescription>
          </div>
          <Button>
            <Shield className="h-4 w-4 mr-2" />
            Create Backup
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-muted-foreground">
          Data backups management interface will be implemented here
        </div>
      </CardContent>
    </Card>
  );
}