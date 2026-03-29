import { useNavigate } from 'react-router-dom';
import Layout from '../../components/Layout';

export default function ManagerDashboard() {
  const navigate = useNavigate();

  return (
    <Layout>
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Manager Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Quick Actions Card */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button
                onClick={() => navigate('/manager/approvals')}
                className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium text-left flex items-center justify-between"
              >
                <span>Review Pending Approvals</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
            </div>
          </div>

          {/* Manager Guide Card */}
          <div className="bg-green-50 rounded-lg shadow p-6 border border-green-200">
            <h2 className="text-xl font-semibold text-green-900 mb-4">Manager Responsibilities</h2>
            <div className="space-y-3 text-sm text-green-800">
              <div className="flex items-start">
                <span className="font-bold mr-2">•</span>
                <span>Review expense requests from your team members</span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">•</span>
                <span>Approve valid expenses that meet company policy</span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">•</span>
                <span>Reject expenses with clear feedback comments</span>
              </div>
              <div className="flex items-start">
                <span className="font-bold mr-2">•</span>
                <span>Ensure timely processing of reimbursements</span>
              </div>
            </div>
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">Pending Approvals</h3>
              <svg className="w-8 h-8 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-gray-900">Review</p>
            <p className="text-sm text-gray-600 mt-1">Expenses awaiting your approval</p>
            <button
              onClick={() => navigate('/manager/approvals')}
              className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              View Pending →
            </button>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">Approve</h3>
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-gray-900">Quick</p>
            <p className="text-sm text-gray-600 mt-1">One-click approval process</p>
            <button
              onClick={() => navigate('/manager/approvals')}
              className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Start Approving →
            </button>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-500">Reject</h3>
              <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-gray-900">Feedback</p>
            <p className="text-sm text-gray-600 mt-1">Provide rejection comments</p>
            <button
              onClick={() => navigate('/manager/approvals')}
              className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Manage Requests →
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
}
