export interface User {
  id: number;
  company_id: number;
  name: string;
  email: string;
  role: 'ADMIN' | 'MANAGER' | 'EMPLOYEE';
  manager_id: number | null;
  created_at: string;
}

export interface Company {
  id: number;
  name: string;
  country: string;
  base_currency: string;
  created_at: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface SignupResponse {
  token: string;
  user: User;
  company: Company;
}

export interface Expense {
  id: number;
  company_id: number;
  employee_id: number;
  employee_name: string;
  category: string;
  description: string;
  expense_date: string;
  paid_by: string;
  currency_original: string;
  amount_original: number;
  amount_company_currency: number;
  status: 'DRAFT' | 'WAITING_APPROVAL' | 'IN_PROGRESS' | 'APPROVED' | 'REJECTED';
  created_at: string;
  approval_steps: ApprovalStep[];
  receipts: Receipt[];
}

export interface ApprovalStep {
  id: number;
  expense_id: number;
  approver_id: number;
  approver_name: string;
  sequence: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  comment: string | null;
  acted_at: string | null;
}

export interface Receipt {
  id: number;
  expense_id: number;
  file_path: string;
  original_filename: string;
  uploaded_at: string;
}

export interface ApprovalRule {
  id: number;
  company_id: number;
  name: string;
  description: string | null;
  mode: 'PERCENTAGE' | 'SPECIFIC' | 'HYBRID';
  percentage_threshold: number | null;
  special_approver_id: number | null;
  is_manager_approver: boolean;
  approvers: Approver[];
  created_at: string;
}

export interface Approver {
  approver_id: number;
  approver_name: string;
  sequence: number;
  is_required: boolean;
}

export interface ParsedReceipt {
  raw_text: string;
  amount: number | null;
  currency_guess: string | null;
  date: string | null;
  merchant: string | null;
}
