'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database } from 'lucide-react';

export default function DataMappingsList() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Data Mappings
            </CardTitle>
            <CardDescription>
              Configure field mappings for data transformations
            </CardDescription>
          </div>
          <Button>
            <Database className="h-4 w-4 mr-2" />
            New Mapping
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-muted-foreground">
          Data mappings management interface will be implemented here
        </div>
      </CardContent>
    </Card>
  );
}