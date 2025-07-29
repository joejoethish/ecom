import React from 'react';
import { SellerLayout } from '../../components/layout/SellerLayout';

export default function Layout({ children }: { children: React.ReactNode }) {
  return <SellerLayout>{children}</SellerLayout>;
}