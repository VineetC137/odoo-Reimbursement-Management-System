import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { getAuthToken, getAuthUser, getRoleDashboardPath } from '../utils/auth';

interface ProtectedRouteProps {
  children: ReactNode;
  allowedRoles: string[];
}

export default function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const token = getAuthToken();
  const user = getAuthUser();

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (!allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard based on role
    return <Navigate to={getRoleDashboardPath(user.role)} replace />;
  }

  return <>{children}</>;
}
