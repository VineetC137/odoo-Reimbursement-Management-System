import { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import axios from '../../lib/axios';
import type { User } from '../../types';

interface ApproverForm {
  approver_id: number;
  sequence: number;
  is_required: boolean;
}

interface RuleForm {
  name: string;
  description: string;
  mode: 'PERCENTAGE' | 'SPECIFIC' | 'HYBRID';
  percentage_threshold: number | null;
  special_approver_id: number | null;
  is_manager_approver: boolean;
  approvers: ApproverForm[];
}

export default function AdminApprovalRulesPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  
  const [form, setForm] = useState<RuleForm>({
    name: '',
    description: '',
    mode: 'PERCENTAGE',
    percentage_threshold: 50,
    special_approver_id: null,
    is_manager_approver: false,
    approvers: [],
  });

  useEffect(() => {
    fetchCurrentRule();
    fetchUsers();
  }, []);

  const fetchCurrentRule = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('/admin/approval-rules/current');
      if (response.data) {
        setForm({
          name: response.data.name,
          description: response.data.description || '',
          mode: response.data.mode,
          percentage_threshold: response.data.percentage_threshold,
          special_approver_id: response.data.special_approver_id,
          is_manager_approver: response.data.is_manager_approver,
          approvers: response.data.approvers.map((a: any) => ({
            approver_id: a.approver_id,
            sequence: a.sequence,
            is_required: a.is_required,
          })),
        });
      }
    } catch (err: any) {
      if (err.response?.status !== 404) {
        setError(err.response?.data?.detail || 'Failed to load approval rule');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get('/admin/users');
      setUsers(response.data.users);
    } catch (err) {
      console.error('Failed to load users:', err);
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!form.name.trim()) {
      errors.name = 'Name is required';
    }

    if (form.mode === 'PERCENTAGE' || form.mode === 'HYBRID') {
      if (form.percentage_threshold === null || form.percentage_threshold < 0 || form.percentage_threshold > 100) {
        errors.percentage_threshold = 'Percentage must be between 0 and 100';
      }
    }

    if (form.mode === 'SPECIFIC' || form.mode === 'HYBRID') {
      if (!form.special_approver_id) {
        errors.special_approver_id = 'Special approver is required for SPECIFIC and HYBRID modes';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      await axios.post('/admin/approval-rules', form);
      
      setSuccess('Approval rule saved successfully');
      fetchCurrentRule();
      
      setTimeout(() => setSuccess(null), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save approval rule');
    } finally {
      setSaving(false);
    }
  };

  const addApprover = () => {
    const nextSequence = form.approvers.length > 0 
      ? Math.max(...form.approvers.map(a => a.sequence)) + 1 
      : 1;
    
    setForm({
      ...form,
      approvers: [
        ...form.approvers,
        { approver_id: 0, sequence: nextSequence, is_required: true },
      ],
    });
  };

  const removeApprover = (index: number) => {
    const newApprovers = form.approvers.filter((_, i) => i !== index);
    // Resequence
    const resequenced = newApprovers.map((a, i) => ({ ...a, sequence: i + 1 }));
    setForm({ ...form, approvers: resequenced });
  };

  const updateApprover = (index: number, field: keyof ApproverForm, value: any) => {
    const newApprovers = [...form.approvers];
    newApprovers[index] = { ...newApprovers[index], [field]: value };
    setForm({ ...form, approvers: newApprovers });
  };

  const moveApprover = (index: number, direction: 'up' | 'down') => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === form.approvers.length - 1)
    ) {
      return;
    }

    const newApprovers = [...form.approvers];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    
    [newApprovers[index], newApprovers[targetIndex]] = [newApprovers[targetIndex], newApprovers[index]];
    
    // Update sequences
    const resequenced = newApprovers.map((a, i) => ({ ...a, sequence: i + 1 }));
    setForm({ ...form, approvers: resequenced });
  };

  const availableUsers = users.filter(
    u => !form.approvers.some(a => a.approver_id === u.id)
  );

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Approval Rules Configuration</h1>

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

        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Basic Information</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rule Name *
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                  formErrors.name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="e.g., Standard Approval Workflow"
              />
              {formErrors.name && (
                <p className="mt-1 text-sm text-red-600">{formErrors.name}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                placeholder="Describe the approval workflow..."
              />
            </div>
          </div>

          {/* Approval Mode */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Approval Mode</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mode *
              </label>
              <select
                value={form.mode}
                onChange={(e) => setForm({ ...form, mode: e.target.value as 'PERCENTAGE' | 'SPECIFIC' | 'HYBRID' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="PERCENTAGE">Percentage - Approve when X% of approvers approve</option>
                <option value="SPECIFIC">Specific - Require specific approver</option>
                <option value="HYBRID">Hybrid - Percentage OR specific approver</option>
              </select>
            </div>

            {(form.mode === 'PERCENTAGE' || form.mode === 'HYBRID') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Percentage Threshold: {form.percentage_threshold}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={form.percentage_threshold || 50}
                  onChange={(e) => setForm({ ...form, percentage_threshold: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>0%</span>
                  <span>50%</span>
                  <span>100%</span>
                </div>
                {formErrors.percentage_threshold && (
                  <p className="mt-1 text-sm text-red-600">{formErrors.percentage_threshold}</p>
                )}
              </div>
            )}

            {(form.mode === 'SPECIFIC' || form.mode === 'HYBRID') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Special Approver *
                </label>
                <select
                  value={form.special_approver_id || ''}
                  onChange={(e) => setForm({ ...form, special_approver_id: e.target.value ? parseInt(e.target.value) : null })}
                  className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    formErrors.special_approver_id ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select a user</option>
                  {users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name} ({user.role})
                    </option>
                  ))}
                </select>
                {formErrors.special_approver_id && (
                  <p className="mt-1 text-sm text-red-600">{formErrors.special_approver_id}</p>
                )}
              </div>
            )}
          </div>

          {/* Manager Approver */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Manager Approval</h2>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_manager_approver"
                checked={form.is_manager_approver}
                onChange={(e) => setForm({ ...form, is_manager_approver: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="is_manager_approver" className="ml-2 block text-sm text-gray-700">
                Require employee's manager approval
              </label>
            </div>
            <p className="text-sm text-gray-500">
              When enabled, the employee's direct manager will be automatically added as an approver
            </p>
          </div>

          {/* Approvers List */}
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Approvers</h2>
              <button
                type="button"
                onClick={addApprover}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                disabled={availableUsers.length === 0}
              >
                Add Approver
              </button>
            </div>

            {form.approvers.length === 0 ? (
              <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg">
                No approvers added yet. Click "Add Approver" to add one.
              </div>
            ) : (
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sequence
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Approver
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Required
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {form.approvers.map((approver, index) => (
                      <tr key={index}>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{approver.sequence}</span>
                            <div className="flex flex-col">
                              <button
                                type="button"
                                onClick={() => moveApprover(index, 'up')}
                                disabled={index === 0}
                                className="text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                              >
                                ▲
                              </button>
                              <button
                                type="button"
                                onClick={() => moveApprover(index, 'down')}
                                disabled={index === form.approvers.length - 1}
                                className="text-gray-400 hover:text-gray-600 disabled:opacity-30 disabled:cursor-not-allowed"
                              >
                                ▼
                              </button>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          <select
                            value={approver.approver_id}
                            onChange={(e) => updateApprover(index, 'approver_id', parseInt(e.target.value))}
                            className="px-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          >
                            <option value={0}>Select user...</option>
                            {users
                              .filter(u => u.id === approver.approver_id || !form.approvers.some(a => a.approver_id === u.id))
                              .map((user) => (
                                <option key={user.id} value={user.id}>
                                  {user.name} ({user.role})
                                </option>
                              ))}
                          </select>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          <input
                            type="checkbox"
                            checked={approver.is_required}
                            onChange={(e) => updateApprover(index, 'is_required', e.target.checked)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                          <button
                            type="button"
                            onClick={() => removeApprover(index)}
                            className="text-red-600 hover:text-red-800 font-medium"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Approval Rule'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
