import type { ReactNode } from 'react';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-neutral">
      <Navbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8 ml-64">
          {children}
        </main>
      </div>
    </div>
  );
}
