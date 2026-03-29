import { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import axios from '../../lib/axios';
import type { Expense } from '../../types';

interface PendingApproval {
  step_id: number;
  expense: Expense;
  sequence: number;
}

export default function ManagerApprovalsPage() {
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [selectedStepId, setSelectedStepId] = useState<number | null>(null);
  const [rejectComment, setRejectComment] = useState('');
  const [rejectError, setRejectError] = useState<string | null>(null);

  useEffect(() => {
    fetchApprovals();
  }, []);

  const fetchApprovals = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('/manager/approvals/pending');
      setApprovals(response.data.approvals);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load pending approvals');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (stepId: number) => {
    try {
      setActionLoading(stepId);
      setError(null);
      setSuccess(null);
      await axios.post(`/manager/approvals/${stepId}/approve`);
      setSuccess('Expense approved successfully');
      fetchApprovals();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to approve expense');
    } finally {
      setActionLoading(null);
    }
  };

  const openRejectModal = (stepId: number) => {
    setSelectedStepId(stepId);
    setRejectComment('');
    setRejectError(null);
    setRejectModalOpen(true);
  };

  const closeRejectModal = () => {
    setRejectModalOpen(false);
    setSelectedStepId(null);
    setRejectComment('');
    setRejectError(null);
  };

  const handleReject = async () => {
    if (!rejectComment.trim()) {
      setRejectError('Comment is required');
      return;
    }

    if (!selectedStepId) return;

    try {
      setActionLoading(selectedStepId);
      setError(null);
      setSuccess(null);
      setRejectError(null);
      await axios.post(`/manager/approvals/${selectedStepId}/reject`, {
        comment: rejectComment,
      });
      setSuccess('Expense rejected successfully');
      closeRejectModal();
      fetchApprovals();
    } catch (err: any) {
      setRejectError(err.response?.data?.detail || 'Failed to reject expense');
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatAmount = (amount: number, currency: string) => {
    return `${currency} ${amount.toFixed(2)}`;
  };

  return (
    <Layout>
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Pending Approvals</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg">
            {success}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Employee
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {approvals.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                      No pending approvals
                    </td>
                  </tr>
                ) : (
                  approvals.map((approval) => (
                    <tr key={approval.step_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {approval.expense.employee_name}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {approval.expense.description}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatAmount(
                          approval.expense.amount_original,
                          approval.expense.currency_original
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(approval.expense.expense_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleApprove(approval.step_id)}
                            disabled={actionLoading === approval.step_id}
                            className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {actionLoading === approval.step_id ? 'Processing...' : 'Approve'}
                          </button>
                          <button
                            onClick={() => openRejectModal(approval.step_id)}
                            disabled={actionLoading === approval.step_id}
                            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            Reject
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Reject Modal */}
        {rejectModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Reject Expense</h2>
              
              {rejectError && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
                  {rejectError}
                </div>
              )}

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rejection Comment <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={rejectComment}
                  onChange={(e) => setRejectComment(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Please provide a reason for rejection..."
                />
              </div>

              <div className="flex gap-3 justify-end">
                <button
                  onClick={closeRejectModal}
                  disabled={actionLoading !== null}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReject}
                  disabled={actionLoading !== null}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading !== null ? 'Processing...' : 'Reject Expense'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
