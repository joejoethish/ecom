'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle } from 'lucide-react';

export default function QualityRulesList() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5" />
              Data Quality Rules
            </CardTitle>
            <CardDescription>
              Define and manage data quality validation rules
            </CardDescription>
          </div>
          <Button>
            <CheckCircle className="h-4 w-4 mr-2" />
            New Rule
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-center py-8 text-muted-foreground">
          Data quality rules management interface will be implemented here
        </div>
      </CardContent>
    </Card>
  );
}