import { Link, useLocation } from 'react-router-dom';
import { getAuthUser } from '../utils/auth';

interface MenuItem {
  path: string;
  label: string;
  roles: string[];
}

const menuItems: MenuItem[] = [
  // Admin menu items
  { path: '/admin/dashboard', label: 'Dashboard', roles: ['ADMIN'] },
  { path: '/admin/users', label: 'Users', roles: ['ADMIN'] },
  { path: '/admin/approval-rules', label: 'Approval Rules', roles: ['ADMIN'] },
  { path: '/admin/expenses', label: 'All Expenses', roles: ['ADMIN'] },
  
  // Manager menu items
  { path: '/manager/dashboard', label: 'Dashboard', roles: ['MANAGER'] },
  { path: '/manager/approvals', label: 'Pending Approvals', roles: ['MANAGER'] },
  
  // Employee menu items
  { path: '/employee/dashboard', label: 'Dashboard', roles: ['EMPLOYEE'] },
  { path: '/employee/expenses', label: 'My Expenses', roles: ['EMPLOYEE'] },
];

export default function Sidebar() {
  const location = useLocation();
  const user = getAuthUser();
  const userRole = user?.role || '';

  const filteredMenuItems = menuItems.filter(item => 
    item.roles.includes(userRole)
  );

  return (
    <aside className="w-64 bg-white border-r border-gray-200 fixed left-0 top-16 h-[calc(100vh-4rem)] overflow-y-auto">
      <nav className="p-4">
        <ul className="space-y-2">
          {filteredMenuItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`block px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-white'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
