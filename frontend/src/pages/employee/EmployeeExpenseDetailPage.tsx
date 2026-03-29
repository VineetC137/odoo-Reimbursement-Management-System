import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import Layout from '../../components/Layout';
import axios from '../../lib/axios';
import type { Expense } from '../../types';

interface ExpenseFormData {
  description: string;
  category: string;
  paid_by: string;
  expense_date: string;
  currency_original: string;
  amount_original: number;
}

export default function EmployeeExpenseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNewExpense = id === 'new';

  const [expense, setExpense] = useState<Expense | null>(null);
  const [loading, setLoading] = useState(!isNewExpense);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ExpenseFormData>({
    defaultValues: {
      description: '',
      category: '',
      paid_by: '',
      expense_date: new Date().toISOString().split('T')[0],
      currency_original: 'USD',
      amount_original: 0,
    },
  });

  const isDraft = expense?.status === 'DRAFT' || isNewExpense;

  useEffect(() => {
    if (!isNewExpense) {
      fetchExpense();
    }
  }, [id]);

  const fetchExpense = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`/employee/expenses/${id}`);
      const expenseData = response.data;
      setExpense(expenseData);
      
      // Populate form with existing data
      reset({
        description: expenseData.description,
        category: expenseData.category,
        paid_by: expenseData.paid_by,
        expense_date: expenseData.expense_date,
        currency_original: expenseData.currency_original,
        amount_original: expenseData.amount_original,
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load expense');
    } finally {
      setLoading(false);
    }
  };

  const onSave = async (data: ExpenseFormData) => {
    try {
      setSubmitting(true);
      setError(null);

      if (isNewExpense) {
        await axios.post('/employee/expenses', data);
      } else {
        await axios.put(`/employee/expenses/${id}`, data);
      }

      navigate('/employee/expenses');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save expense');
    } finally {
      setSubmitting(false);
    }
  };

  const onSubmitForApproval = async () => {
    try {
      setSubmitting(true);
      setError(null);

      // First save the current form data
      const formData = watch();
      if (isNewExpense) {
        const createResponse = await axios.post('/employee/expenses', formData);
        const newExpenseId = createResponse.data.id;
        await axios.post(`/employee/expenses/${newExpenseId}/submit`);
      } else {
        await axios.put(`/employee/expenses/${id}`, formData);
        await axios.post(`/employee/expenses/${id}/submit`);
      }

      navigate('/employee/expenses');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit expense');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      WAITING_APPROVAL: 'bg-yellow-100 text-yellow-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-800',
      APPROVED: 'bg-green-100 text-green-800',
      REJECTED: 'bg-red-100 text-red-800',
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

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
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            {isNewExpense ? 'Create Expense' : 'Expense Detail'}
          </h1>
          {expense && (
            <div className="flex items-center gap-4">
              {getStatusBadge(expense.status)}
            </div>
          )}
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <form onSubmit={handleSubmit(onSave)}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <input
                  type="text"
                  disabled={!isDraft}
                  {...register('description', { required: 'Description is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                {errors.description && (
                  <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category *
                </label>
                <select
                  disabled={!isDraft}
                  {...register('category', { required: 'Category is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Select category</option>
                  <option value="Travel">Travel</option>
                  <option value="Meals">Meals</option>
                  <option value="Office Supplies">Office Supplies</option>
                  <option value="Software">Software</option>
                  <option value="Other">Other</option>
                </select>
                {errors.category && (
                  <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Paid By *
                </label>
                <select
                  disabled={!isDraft}
                  {...register('paid_by', { required: 'Payment method is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="">Select payment method</option>
                  <option value="Personal Card">Personal Card</option>
                  <option value="Company Card">Company Card</option>
                  <option value="Cash">Cash</option>
                </select>
                {errors.paid_by && (
                  <p className="mt-1 text-sm text-red-600">{errors.paid_by.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Expense Date *
                </label>
                <input
                  type="date"
                  disabled={!isDraft}
                  max={new Date().toISOString().split('T')[0]}
                  {...register('expense_date', { required: 'Expense date is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                {errors.expense_date && (
                  <p className="mt-1 text-sm text-red-600">{errors.expense_date.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Currency *
                </label>
                <select
                  disabled={!isDraft}
                  {...register('currency_original', { required: 'Currency is required' })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="JPY">JPY</option>
                  <option value="CAD">CAD</option>
                  <option value="AUD">AUD</option>
                  <option value="CHF">CHF</option>
                  <option value="CNY">CNY</option>
                  <option value="INR">INR</option>
                </select>
                {errors.currency_original && (
                  <p className="mt-1 text-sm text-red-600">{errors.currency_original.message}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Amount *
                </label>
                <input
                  type="number"
                  step="0.01"
                  disabled={!isDraft}
                  {...register('amount_original', {
                    required: 'Amount is required',
                    min: { value: 0.01, message: 'Amount must be positive' },
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                {errors.amount_original && (
                  <p className="mt-1 text-sm text-red-600">{errors.amount_original.message}</p>
                )}
              </div>
            </div>

            {isDraft && (
              <div className="mt-6 flex gap-3">
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Saving...' : 'Save Draft'}
                </button>
                <button
                  type="button"
                  onClick={onSubmitForApproval}
                  disabled={submitting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {submitting ? 'Submitting...' : 'Submit for Approval'}
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/employee/expenses')}
                  disabled={submitting}
                  className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            )}

            {!isDraft && (
              <div className="mt-6">
                <button
                  type="button"
                  onClick={() => navigate('/employee/expenses')}
                  className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
                >
                  Back to Expenses
                </button>
              </div>
            )}
          </form>
        </div>

        {expense && expense.approval_steps.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Approval Timeline</h2>
            <div className="space-y-4">
              {expense.approval_steps.map((step, index) => (
                <div key={step.id} className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        step.status === 'APPROVED'
                          ? 'bg-green-100 text-green-800'
                          : step.status === 'REJECTED'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {index + 1}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900">{step.approver_name}</span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          step.status === 'APPROVED'
                            ? 'bg-green-100 text-green-800'
                            : step.status === 'REJECTED'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {step.status}
                      </span>
                    </div>
                    {step.comment && (
                      <p className="text-sm text-gray-600 mb-1">{step.comment}</p>
                    )}
                    {step.acted_at && (
                      <p className="text-xs text-gray-500">{formatDate(step.acted_at)}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
