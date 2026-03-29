import { useNavigate } from 'react-router-dom';
import Layout from '../../components/Layout';

export default function EmployeeDashboard() {
  const navigate = useNavigate();

  return (
    <Layout>
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Employee Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Quick Actions Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/employee/expenses/new')}
                className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-left flex items-center justify-between"
              >
                <span>Create New Expense</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
              <button
                onClick={() => navigate('/employee/expenses')}
                className="w-full px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium text-left"
              >
                View My Expenses
              </button>
            </div>
          </div>

          {/* Getting Started Card */}
          <div className="bg-blue-50 rounded-lg shadow p-6 border border-blue-200">
            <h2 className="text-xl font-semibold text-blue-900 mb-4">Getting Started</h2>
            <div className="space-y-3 text-sm text-blue-800">
              <div className="flex items-start">
                <span className="font-bold mr-2">1.</span>
                <span>Click "Create New Expense" to submit a reimbursement request</span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">2.</span>
                <span>Fill in expense details (description, amount, category, date)</span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">3.</span>
                <span>Save as draft or submit directly for approval</span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">4.</span>
                <span>Track approval status in "My Expenses"</span>
              </div>
            </div>
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">My Expenses</h3>
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-gray-900">View All</p>
            <button
              onClick={() => navigate('/employee/expenses')}
              className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Go to My Expenses →
            </button>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">Draft Expenses</h3>
              <svg className="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-gray-900">Saved</p>
            <button
              onClick={() => navigate('/employee/expenses')}
              className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View Drafts →
            </button>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">Pending Approval</h3>
              <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-gray-900">In Progress</p>
            <button
              onClick={() => navigate('/employee/expenses')}
              className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Check Status →
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
