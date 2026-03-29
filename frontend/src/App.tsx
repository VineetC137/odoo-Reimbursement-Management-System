import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminApprovalRulesPage from './pages/admin/AdminApprovalRulesPage';
import AdminExpensesPage from './pages/admin/AdminExpensesPage';
import ManagerDashboard from './pages/manager/ManagerDashboard';
import ManagerApprovalsPage from './pages/manager/ManagerApprovalsPage';
import EmployeeDashboard from './pages/employee/EmployeeDashboard';
import EmployeeExpensesPage from './pages/employee/EmployeeExpensesPage';
import EmployeeExpenseDetailPage from './pages/employee/EmployeeExpenseDetailPage';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        
        {/* Admin routes */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminUsersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/approval-rules"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminApprovalRulesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/expenses"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <AdminExpensesPage />
            </ProtectedRoute>
          }
        />
        
        {/* Manager routes */}
        <Route
          path="/manager/dashboard"
          element={
            <ProtectedRoute allowedRoles={['MANAGER']}>
              <ManagerDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/manager/approvals"
          element={
            <ProtectedRoute allowedRoles={['MANAGER']}>
              <ManagerApprovalsPage />
            </ProtectedRoute>
          }
        />
        
        {/* Employee routes */}
        <Route
          path="/employee/dashboard"
          element={
            <ProtectedRoute allowedRoles={['EMPLOYEE']}>
              <EmployeeDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/expenses"
          element={
            <ProtectedRoute allowedRoles={['EMPLOYEE']}>
              <EmployeeExpensesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee/expenses/:id"
          element={
            <ProtectedRoute allowedRoles={['EMPLOYEE']}>
              <EmployeeExpenseDetailPage />
            </ProtectedRoute>
          }
        />
        
        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
