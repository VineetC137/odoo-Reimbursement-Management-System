import { FormEvent, useEffect, useState } from "react";

import "./styles/tokens.css";
import "./styles/app.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000/api/v1";
const SESSION_STORAGE_KEY = "reimbursement-session";

type AuthMode = "signup" | "login";
type AssignableRole = "EMPLOYEE" | "MANAGER";

type CountryOption = {
  countryCode: string;
  countryName: string;
  currencyCode: string;
  currencyName: string | null;
  currencySymbol: string | null;
};

type Session = {
  accessToken: string;
  refreshToken: string;
  user: {
    id: string;
    firstName: string;
    lastName: string;
    fullName: string;
    email: string;
    roles: string[];
  };
  company: {
    id: string;
    name: string;
    countryCode: string;
    baseCurrency: string;
  };
};

type UserSummary = {
  id: string;
  firstName: string;
  lastName: string;
  fullName: string;
  email: string;
  role: string;
  status: string;
  createdAt: string;
  manager: {
    id: string;
    fullName: string;
    email: string;
  } | null;
};

type ApiErrorPayload = {
  success?: boolean;
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, string>;
  };
  message?: string;
};

type ApiSuccessPayload<T> = {
  success: true;
  message?: string;
  data: T;
};

type SignupFormState = {
  companyName: string;
  countryCode: string;
  firstName: string;
  lastName: string;
  email: string;
  password: string;
};

type LoginFormState = {
  email: string;
  password: string;
};

type CreateUserFormState = {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  role: AssignableRole;
};

type RequestJsonOptions = RequestInit & {
  token?: string;
};

const initialSignupForm: SignupFormState = {
  companyName: "",
  countryCode: "",
  firstName: "",
  lastName: "",
  email: "",
  password: ""
};

const initialLoginForm: LoginFormState = {
  email: "",
  password: ""
};

const initialCreateUserForm: CreateUserFormState = {
  firstName: "",
  lastName: "",
  email: "",
  password: "",
  role: "EMPLOYEE"
};

function readStoredSession(): Session | null {
  try {
    const storedValue = window.localStorage.getItem(SESSION_STORAGE_KEY);

    if (!storedValue) {
      return null;
    }

    return JSON.parse(storedValue) as Session;
  } catch {
    return null;
  }
}

function extractErrorMessage(payload: ApiErrorPayload | null, fallbackMessage: string): string {
  return payload?.error?.message ?? payload?.message ?? fallbackMessage;
}

function extractFieldErrors(payload: ApiErrorPayload | null): Record<string, string> {
  return payload?.error?.details ?? {};
}

function formatDate(isoValue: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(isoValue));
}

async function requestJson<T>(path: string, options: RequestJsonOptions = {}): Promise<ApiSuccessPayload<T>> {
  const { token, headers, ...init } = options;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers ?? {})
    },
    ...init
  });

  const rawBody = (await response.json().catch(() => null)) as ApiSuccessPayload<T> | ApiErrorPayload | null;

  if (!response.ok) {
    const error = new Error(extractErrorMessage(rawBody as ApiErrorPayload | null, "Request failed"));
    (error as Error & { fieldErrors?: Record<string, string> }).fieldErrors = extractFieldErrors(rawBody as ApiErrorPayload | null);
    throw error;
  }

  return rawBody as ApiSuccessPayload<T>;
}

export default function App() {
  const [mode, setMode] = useState<AuthMode>("signup");
  const [countries, setCountries] = useState<CountryOption[]>([]);
  const [countriesLoading, setCountriesLoading] = useState(true);
  const [countriesError, setCountriesError] = useState("");
  const [signupForm, setSignupForm] = useState<SignupFormState>(initialSignupForm);
  const [loginForm, setLoginForm] = useState<LoginFormState>(initialLoginForm);
  const [authFieldErrors, setAuthFieldErrors] = useState<Record<string, string>>({});
  const [authError, setAuthError] = useState("");
  const [isSubmittingAuth, setIsSubmittingAuth] = useState(false);
  const [session, setSession] = useState<Session | null>(() => readStoredSession());
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState("");
  const [userActionMessage, setUserActionMessage] = useState("");
  const [userActionError, setUserActionError] = useState("");
  const [createUserForm, setCreateUserForm] = useState<CreateUserFormState>(initialCreateUserForm);
  const [createUserErrors, setCreateUserErrors] = useState<Record<string, string>>({});
  const [isCreatingUser, setIsCreatingUser] = useState(false);
  const [roleDrafts, setRoleDrafts] = useState<Record<string, AssignableRole>>({});
  const [managerDrafts, setManagerDrafts] = useState<Record<string, string>>({});
  const [roleUpdatePendingUserId, setRoleUpdatePendingUserId] = useState("");
  const [managerUpdatePendingUserId, setManagerUpdatePendingUserId] = useState("");

  useEffect(() => {
    void loadCountries();
  }, []);

  useEffect(() => {
    if (session) {
      window.localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
      return;
    }

    window.localStorage.removeItem(SESSION_STORAGE_KEY);
  }, [session]);

  useEffect(() => {
    if (!session || !session.user.roles.includes("ADMIN")) {
      return;
    }

    void loadUsers(session.accessToken);
  }, [session]);

  const selectedCountry = countries.find((country) => country.countryCode === signupForm.countryCode);
  const isAdmin = session?.user.roles.includes("ADMIN") ?? false;
  const managerCandidates = users.filter((user) => user.role === "MANAGER");
  const employeeCount = users.filter((user) => user.role === "EMPLOYEE").length;
  const managerCount = managerCandidates.length;

  function syncUserDrafts(nextUsers: UserSummary[]): void {
    setRoleDrafts(
      nextUsers.reduce<Record<string, AssignableRole>>((accumulator, user) => {
        if (user.role === "EMPLOYEE" || user.role === "MANAGER") {
          accumulator[user.id] = user.role;
        }

        return accumulator;
      }, {})
    );

    setManagerDrafts(
      nextUsers.reduce<Record<string, string>>((accumulator, user) => {
        accumulator[user.id] = user.manager?.id ?? "";
        return accumulator;
      }, {})
    );
  }

  async function loadCountries(refresh = false): Promise<void> {
    setCountriesLoading(true);
    setCountriesError("");

    try {
      const response = await requestJson<CountryOption[]>(
        `/metadata/countries${refresh ? "?refresh=true" : ""}`
      );

      setCountries(response.data);
    } catch (error) {
      setCountriesError(error instanceof Error ? error.message : "Unable to load countries");
    } finally {
      setCountriesLoading(false);
    }
  }

  async function loadUsers(token: string): Promise<void> {
    setUsersLoading(true);
    setUsersError("");

    try {
      const response = await requestJson<UserSummary[]>("/users", { token });
      setUsers(response.data);
      syncUserDrafts(response.data);
    } catch (error) {
      setUsersError(error instanceof Error ? error.message : "Unable to load users");
    } finally {
      setUsersLoading(false);
    }
  }

  function validateSignupForm(): Record<string, string> {
    const errors: Record<string, string> = {};

    if (signupForm.companyName.trim().length < 3) {
      errors.companyName = "Company name should be at least 3 characters";
    }

    if (!signupForm.countryCode) {
      errors.countryCode = "Select a country";
    }

    if (signupForm.firstName.trim().length < 2) {
      errors.firstName = "First name should be at least 2 characters";
    }

    if (signupForm.lastName.trim().length < 2) {
      errors.lastName = "Last name should be at least 2 characters";
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signupForm.email)) {
      errors.email = "Enter a valid email address";
    }

    if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,64}$/.test(signupForm.password)) {
      errors.password = "Use 8+ characters with uppercase, lowercase, and a number";
    }

    return errors;
  }

  function validateLoginForm(): Record<string, string> {
    const errors: Record<string, string> = {};

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(loginForm.email)) {
      errors.email = "Enter a valid email address";
    }

    if (!loginForm.password.trim()) {
      errors.password = "Enter your password";
    }

    return errors;
  }

  function validateCreateUserForm(): Record<string, string> {
    const errors: Record<string, string> = {};

    if (createUserForm.firstName.trim().length < 2) {
      errors.firstName = "First name should be at least 2 characters";
    }

    if (createUserForm.lastName.trim().length < 2) {
      errors.lastName = "Last name should be at least 2 characters";
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(createUserForm.email)) {
      errors.email = "Enter a valid email address";
    }

    if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,64}$/.test(createUserForm.password)) {
      errors.password = "Use 8+ characters with uppercase, lowercase, and a number";
    }

    return errors;
  }

  async function handleSignupSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const validationErrors = validateSignupForm();
    setAuthFieldErrors(validationErrors);
    setAuthError("");

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmittingAuth(true);

    try {
      const response = await requestJson<Session>("/auth/signup", {
        method: "POST",
        body: JSON.stringify(signupForm)
      });

      setSession(response.data);
      setSignupForm(initialSignupForm);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Unable to create account");
      setAuthFieldErrors((error as Error & { fieldErrors?: Record<string, string> }).fieldErrors ?? {});
    } finally {
      setIsSubmittingAuth(false);
    }
  }

  async function handleLoginSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const validationErrors = validateLoginForm();
    setAuthFieldErrors(validationErrors);
    setAuthError("");

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmittingAuth(true);

    try {
      const response = await requestJson<Session>("/auth/login", {
        method: "POST",
        body: JSON.stringify(loginForm)
      });

      setSession(response.data);
      setLoginForm(initialLoginForm);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Unable to log in");
      setAuthFieldErrors((error as Error & { fieldErrors?: Record<string, string> }).fieldErrors ?? {});
    } finally {
      setIsSubmittingAuth(false);
    }
  }

  async function handleCreateUserSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    if (!session) {
      return;
    }

    const validationErrors = validateCreateUserForm();
    setCreateUserErrors(validationErrors);
    setUserActionError("");
    setUserActionMessage("");

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsCreatingUser(true);

    try {
      await requestJson<UserSummary>("/users", {
        method: "POST",
        token: session.accessToken,
        body: JSON.stringify(createUserForm)
      });

      setCreateUserForm(initialCreateUserForm);
      setCreateUserErrors({});
      setUserActionMessage("User created successfully.");
      await loadUsers(session.accessToken);
    } catch (error) {
      setUserActionError(error instanceof Error ? error.message : "Unable to create user");
      setCreateUserErrors((error as Error & { fieldErrors?: Record<string, string> }).fieldErrors ?? {});
    } finally {
      setIsCreatingUser(false);
    }
  }

  async function handleRoleUpdate(userId: string): Promise<void> {
    if (!session) {
      return;
    }

    const nextRole = roleDrafts[userId];

    if (!nextRole) {
      return;
    }

    setRoleUpdatePendingUserId(userId);
    setUserActionError("");
    setUserActionMessage("");

    try {
      await requestJson<UserSummary>(`/users/${userId}/role`, {
        method: "PATCH",
        token: session.accessToken,
        body: JSON.stringify({ role: nextRole })
      });

      setUserActionMessage("Role updated successfully.");
      await loadUsers(session.accessToken);
    } catch (error) {
      setUserActionError(error instanceof Error ? error.message : "Unable to update role");
    } finally {
      setRoleUpdatePendingUserId("");
    }
  }

  async function handleManagerAssignment(userId: string): Promise<void> {
    if (!session) {
      return;
    }

    const selectedManagerId = managerDrafts[userId];

    if (!selectedManagerId) {
      setUserActionError("Select a manager before saving.");
      setUserActionMessage("");
      return;
    }

    setManagerUpdatePendingUserId(userId);
    setUserActionError("");
    setUserActionMessage("");

    try {
      await requestJson<UserSummary>(`/users/${userId}/manager`, {
        method: "POST",
        token: session.accessToken,
        body: JSON.stringify({ managerUserId: selectedManagerId })
      });

      setUserActionMessage("Manager updated successfully.");
      await loadUsers(session.accessToken);
    } catch (error) {
      setUserActionError(error instanceof Error ? error.message : "Unable to assign manager");
    } finally {
      setManagerUpdatePendingUserId("");
    }
  }

  function handleLogout(): void {
    setSession(null);
    setMode("login");
    setAuthError("");
    setAuthFieldErrors({});
    setUsers([]);
    setUsersError("");
    setUserActionError("");
    setUserActionMessage("");
  }

  if (session) {
    return (
      <div className="dashboard-shell">
        <aside className="dashboard-sidebar">
          <div>
            <p className="eyebrow">Signed In</p>
            <h2>{session.company.name}</h2>
            <p className="sidebar-copy">
              {session.user.fullName}
              <br />
              {session.user.roles.join(" / ")}
            </p>
          </div>
          <nav className="dashboard-nav">
            <a href="#overview">Overview</a>
            {isAdmin ? <a href="#user-management">User Management</a> : null}
            <a href="#next-build">Next Build</a>
          </nav>
          <button className="ghost-button" type="button" onClick={handleLogout}>
            Sign out
          </button>
        </aside>

        <main className="dashboard-main">
          <header className="welcome-card" id="overview">
            <div>
              <p className="eyebrow">Workspace Active</p>
              <h1>{session.user.fullName}</h1>
              <p className="welcome-copy">
                The project now supports company onboarding, login, admin user creation, role
                updates, and reporting-manager assignment. This gives the reimbursement flow a real
                organization structure to build on.
              </p>
            </div>
            <div className="badge-stack">
              <span className="pill">{session.user.roles.join(" / ")}</span>
              <span className="pill pill-soft">
                {session.company.countryCode} | {session.company.baseCurrency}
              </span>
            </div>
          </header>

          <section className="metrics-grid">
            <article className="metric-card">
              <span className="metric-label">Base Currency</span>
              <strong>{session.company.baseCurrency}</strong>
              <p>Expense normalization and approval review will use this as the company-wide reference.</p>
            </article>
            <article className="metric-card">
              <span className="metric-label">Managers</span>
              <strong>{managerCount}</strong>
              <p>Managers created here can be attached as approvers and reporting heads in later modules.</p>
            </article>
            <article className="metric-card">
              <span className="metric-label">Employees</span>
              <strong>{employeeCount}</strong>
              <p>Employees created under the company are ready for expense submission in the next slice.</p>
            </article>
          </section>

          {isAdmin ? (
            <section className="management-grid" id="user-management">
              <article className="management-card">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Admin</p>
                    <h3>Create team member</h3>
                  </div>
                  <span className="mini-chip">Role + password setup</span>
                </div>

                {userActionMessage ? <div className="inline-banner inline-banner-success">{userActionMessage}</div> : null}
                {userActionError ? <div className="inline-banner inline-banner-danger">{userActionError}</div> : null}

                <form className="auth-form" onSubmit={(event) => void handleCreateUserSubmit(event)}>
                  <div className="field-row">
                    <label className="field">
                      <span>First name</span>
                      <input
                        value={createUserForm.firstName}
                        onChange={(event) =>
                          setCreateUserForm((current) => ({ ...current, firstName: event.target.value }))
                        }
                        placeholder="Shraddha"
                      />
                      {createUserErrors.firstName ? <small>{createUserErrors.firstName}</small> : null}
                    </label>

                    <label className="field">
                      <span>Last name</span>
                      <input
                        value={createUserForm.lastName}
                        onChange={(event) =>
                          setCreateUserForm((current) => ({ ...current, lastName: event.target.value }))
                        }
                        placeholder="Bhadane"
                      />
                      {createUserErrors.lastName ? <small>{createUserErrors.lastName}</small> : null}
                    </label>
                  </div>

                  <label className="field">
                    <span>Email</span>
                    <input
                      type="email"
                      value={createUserForm.email}
                      onChange={(event) =>
                        setCreateUserForm((current) => ({ ...current, email: event.target.value }))
                      }
                      placeholder="teammate@company.com"
                    />
                    {createUserErrors.email ? <small>{createUserErrors.email}</small> : null}
                  </label>

                  <div className="field-row">
                    <label className="field">
                      <span>Temporary password</span>
                      <input
                        type="password"
                        value={createUserForm.password}
                        onChange={(event) =>
                          setCreateUserForm((current) => ({ ...current, password: event.target.value }))
                        }
                        placeholder="Password with uppercase, lowercase, and number"
                      />
                      {createUserErrors.password ? <small>{createUserErrors.password}</small> : null}
                    </label>

                    <label className="field">
                      <span>Role</span>
                      <select
                        value={createUserForm.role}
                        onChange={(event) =>
                          setCreateUserForm((current) => ({
                            ...current,
                            role: event.target.value as AssignableRole
                          }))
                        }
                      >
                        <option value="EMPLOYEE">Employee</option>
                        <option value="MANAGER">Manager</option>
                      </select>
                    </label>
                  </div>

                  <button className="primary-button" type="submit" disabled={isCreatingUser}>
                    {isCreatingUser ? "Creating user..." : "Create user"}
                  </button>
                </form>
              </article>

              <article className="management-card management-card-wide">
                <div className="section-heading">
                  <div>
                    <p className="eyebrow">Admin</p>
                    <h3>Company users</h3>
                  </div>
                  <button className="ghost-button" type="button" onClick={() => void loadUsers(session.accessToken)}>
                    Refresh
                  </button>
                </div>

                {usersError ? <div className="inline-banner inline-banner-danger">{usersError}</div> : null}

                {usersLoading ? (
                  <div className="loading-panel">Loading users...</div>
                ) : (
                  <div className="user-card-list">
                    {users.map((user) => {
                      const isAdminRow = user.role === "ADMIN";
                      const availableManagers = managerCandidates.filter((manager) => manager.id !== user.id);

                      return (
                        <article className="user-card" key={user.id}>
                          <div className="user-card-header">
                            <div>
                              <h4>{user.fullName}</h4>
                              <p>{user.email}</p>
                            </div>
                            <span className={`status-pill status-pill-${user.role.toLowerCase()}`}>{user.role}</span>
                          </div>

                          <div className="user-meta-grid">
                            <div>
                              <span className="meta-label">Created</span>
                              <strong>{formatDate(user.createdAt)}</strong>
                            </div>
                            <div>
                              <span className="meta-label">Status</span>
                              <strong>{user.status}</strong>
                            </div>
                            <div>
                              <span className="meta-label">Manager</span>
                              <strong>{user.manager?.fullName ?? "Not assigned"}</strong>
                            </div>
                          </div>

                          {isAdminRow ? (
                            <p className="admin-note">
                              The company owner account stays protected here so the workspace does not lose admin access.
                            </p>
                          ) : (
                            <div className="user-actions-grid">
                              <label className="field">
                                <span>Role</span>
                                <select
                                  value={roleDrafts[user.id] ?? "EMPLOYEE"}
                                  onChange={(event) =>
                                    setRoleDrafts((current) => ({
                                      ...current,
                                      [user.id]: event.target.value as AssignableRole
                                    }))
                                  }
                                >
                                  <option value="EMPLOYEE">Employee</option>
                                  <option value="MANAGER">Manager</option>
                                </select>
                              </label>

                              <label className="field">
                                <span>Reporting manager</span>
                                <select
                                  value={managerDrafts[user.id] ?? ""}
                                  onChange={(event) =>
                                    setManagerDrafts((current) => ({
                                      ...current,
                                      [user.id]: event.target.value
                                    }))
                                  }
                                  disabled={availableManagers.length === 0}
                                >
                                  <option value="">
                                    {availableManagers.length === 0 ? "No manager available" : "Select manager"}
                                  </option>
                                  {availableManagers.map((manager) => (
                                    <option key={manager.id} value={manager.id}>
                                      {manager.fullName}
                                    </option>
                                  ))}
                                </select>
                              </label>

                              <div className="action-button-row">
                                <button
                                  className="ghost-button"
                                  type="button"
                                  disabled={roleUpdatePendingUserId === user.id}
                                  onClick={() => void handleRoleUpdate(user.id)}
                                >
                                  {roleUpdatePendingUserId === user.id ? "Saving role..." : "Save role"}
                                </button>

                                <button
                                  className="primary-button"
                                  type="button"
                                  disabled={managerUpdatePendingUserId === user.id || availableManagers.length === 0}
                                  onClick={() => void handleManagerAssignment(user.id)}
                                >
                                  {managerUpdatePendingUserId === user.id ? "Saving manager..." : "Save manager"}
                                </button>
                              </div>
                            </div>
                          )}
                        </article>
                      );
                    })}
                  </div>
                )}
              </article>
            </section>
          ) : null}

          <section className="next-step-grid" id="next-build">
            <article className="roadmap-card">
              <h3>What is already working</h3>
              <ul>
                <li>Company onboarding with dynamic country and currency lookup</li>
                <li>JWT login and protected backend routes</li>
                <li>Admin user creation with role assignment</li>
                <li>Reporting-manager mapping with audit-friendly behavior</li>
              </ul>
            </article>

            <article className="roadmap-card">
              <h3>Next implementation slice</h3>
              <ul>
                <li>Expense draft creation and submission APIs</li>
                <li>Employee expense history screens</li>
                <li>Currency normalization during claim submission</li>
                <li>Approval queue setup for managers</li>
              </ul>
            </article>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <section className="hero-panel">
        <p className="eyebrow">Reimbursement Management</p>
        <h1>Build the reimbursement flow from the company level, not from a loose set of forms.</h1>
        <p className="hero-copy">
          This starter experience already uses live country and currency data, creates the first
          admin account, and keeps the UI aligned with the clean white, sky-blue, and red visual
          direction planned for the full product.
        </p>

        <div className="hero-grid">
          <article className="hero-card">
            <span className="hero-card-title">What this unlocks</span>
            <ul>
              <li>Company-aware onboarding with base currency selection</li>
              <li>JWT session foundation for protected screens</li>
              <li>Role-aware user management inside the same workspace</li>
            </ul>
          </article>

          <article className="hero-card hero-card-accent">
            <span className="hero-card-title">What comes next</span>
            <ul>
              <li>Expense drafts and submission</li>
              <li>Manager approval queues</li>
              <li>Sequential and hybrid approval workflows</li>
            </ul>
          </article>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-panel-header">
          <div>
            <p className="eyebrow">Get Started</p>
            <h2>{mode === "signup" ? "Create company workspace" : "Sign in to continue"}</h2>
          </div>
          <div className="mode-switch">
            <button
              className={mode === "signup" ? "mode-button is-active" : "mode-button"}
              type="button"
              onClick={() => {
                setMode("signup");
                setAuthFieldErrors({});
                setAuthError("");
              }}
            >
              Signup
            </button>
            <button
              className={mode === "login" ? "mode-button is-active" : "mode-button"}
              type="button"
              onClick={() => {
                setMode("login");
                setAuthFieldErrors({});
                setAuthError("");
              }}
            >
              Login
            </button>
          </div>
        </div>

        {countriesError ? (
          <div className="alert-box">
            <strong>Country data is unavailable right now.</strong>
            <p>{countriesError}</p>
            <button className="ghost-button" type="button" onClick={() => void loadCountries(true)}>
              Retry
            </button>
          </div>
        ) : null}

        {authError ? (
          <div className="alert-box alert-box-danger">
            <strong>Request could not be completed.</strong>
            <p>{authError}</p>
          </div>
        ) : null}

        {mode === "signup" ? (
          <form className="auth-form" onSubmit={(event) => void handleSignupSubmit(event)}>
            <label className="field">
              <span>Company name</span>
              <input
                value={signupForm.companyName}
                onChange={(event) =>
                  setSignupForm((current) => ({ ...current, companyName: event.target.value }))
                }
                placeholder="Acme Labs"
              />
              {authFieldErrors.companyName ? <small>{authFieldErrors.companyName}</small> : null}
            </label>

            <div className="field-row">
              <label className="field">
                <span>First name</span>
                <input
                  value={signupForm.firstName}
                  onChange={(event) =>
                    setSignupForm((current) => ({ ...current, firstName: event.target.value }))
                  }
                  placeholder="Vineet"
                />
                {authFieldErrors.firstName ? <small>{authFieldErrors.firstName}</small> : null}
              </label>

              <label className="field">
                <span>Last name</span>
                <input
                  value={signupForm.lastName}
                  onChange={(event) =>
                    setSignupForm((current) => ({ ...current, lastName: event.target.value }))
                  }
                  placeholder="Unde"
                />
                {authFieldErrors.lastName ? <small>{authFieldErrors.lastName}</small> : null}
              </label>
            </div>

            <label className="field">
              <span>Email</span>
              <input
                type="email"
                value={signupForm.email}
                onChange={(event) =>
                  setSignupForm((current) => ({ ...current, email: event.target.value }))
                }
                placeholder="admin@acmelabs.com"
              />
              {authFieldErrors.email ? <small>{authFieldErrors.email}</small> : null}
            </label>

            <div className="field-row field-row-country">
              <label className="field">
                <span>Country</span>
                <select
                  value={signupForm.countryCode}
                  onChange={(event) =>
                    setSignupForm((current) => ({ ...current, countryCode: event.target.value }))
                  }
                  disabled={countriesLoading}
                >
                  <option value="">{countriesLoading ? "Loading countries..." : "Select country"}</option>
                  {countries.map((country) => (
                    <option key={country.countryCode} value={country.countryCode}>
                      {country.countryName} ({country.currencyCode})
                    </option>
                  ))}
                </select>
                {authFieldErrors.countryCode ? <small>{authFieldErrors.countryCode}</small> : null}
              </label>

              <div className="currency-preview">
                <span className="currency-label">Base currency</span>
                <strong>{selectedCountry ? selectedCountry.currencyCode : "Waiting for selection"}</strong>
                <p>
                  {selectedCountry
                    ? `${selectedCountry.currencyName ?? "Currency"}${selectedCountry.currencySymbol ? ` · ${selectedCountry.currencySymbol}` : ""}`
                    : "The selected country sets your company currency."}
                </p>
              </div>
            </div>

            <label className="field">
              <span>Password</span>
              <input
                type="password"
                value={signupForm.password}
                onChange={(event) =>
                  setSignupForm((current) => ({ ...current, password: event.target.value }))
                }
                placeholder="Use uppercase, lowercase, and a number"
              />
              {authFieldErrors.password ? <small>{authFieldErrors.password}</small> : null}
            </label>

            <button className="primary-button" type="submit" disabled={isSubmittingAuth || countriesLoading}>
              {isSubmittingAuth ? "Creating workspace..." : "Create workspace"}
            </button>
          </form>
        ) : (
          <form className="auth-form" onSubmit={(event) => void handleLoginSubmit(event)}>
            <label className="field">
              <span>Email</span>
              <input
                type="email"
                value={loginForm.email}
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, email: event.target.value }))
                }
                placeholder="admin@acmelabs.com"
              />
              {authFieldErrors.email ? <small>{authFieldErrors.email}</small> : null}
            </label>

            <label className="field">
              <span>Password</span>
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) =>
                  setLoginForm((current) => ({ ...current, password: event.target.value }))
                }
                placeholder="Enter your password"
              />
              {authFieldErrors.password ? <small>{authFieldErrors.password}</small> : null}
            </label>

            <button className="primary-button" type="submit" disabled={isSubmittingAuth}>
              {isSubmittingAuth ? "Signing in..." : "Sign in"}
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
