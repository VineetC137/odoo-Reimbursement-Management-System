import { FormEvent, useEffect, useState } from "react";

import "./styles/tokens.css";
import "./styles/app.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:4000/api/v1";
const SESSION_STORAGE_KEY = "reimbursement-session";

type AuthMode = "signup" | "login";

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

async function requestJson<T>(path: string, init?: RequestInit): Promise<ApiSuccessPayload<T>> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
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
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submissionError, setSubmissionError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [session, setSession] = useState<Session | null>(() => readStoredSession());

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

  const selectedCountry = countries.find((country) => country.countryCode === signupForm.countryCode);

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

  async function handleSignupSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const validationErrors = validateSignupForm();
    setFieldErrors(validationErrors);
    setSubmissionError("");

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await requestJson<Session>("/auth/signup", {
        method: "POST",
        body: JSON.stringify(signupForm)
      });

      setSession(response.data);
      setSignupForm(initialSignupForm);
    } catch (error) {
      setSubmissionError(error instanceof Error ? error.message : "Unable to create account");
      setFieldErrors((error as Error & { fieldErrors?: Record<string, string> }).fieldErrors ?? {});
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLoginSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();

    const validationErrors = validateLoginForm();
    setFieldErrors(validationErrors);
    setSubmissionError("");

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await requestJson<Session>("/auth/login", {
        method: "POST",
        body: JSON.stringify(loginForm)
      });

      setSession(response.data);
      setLoginForm(initialLoginForm);
    } catch (error) {
      setSubmissionError(error instanceof Error ? error.message : "Unable to log in");
      setFieldErrors((error as Error & { fieldErrors?: Record<string, string> }).fieldErrors ?? {});
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleLogout(): void {
    setSession(null);
    setMode("login");
    setSubmissionError("");
    setFieldErrors({});
  }

  if (session) {
    return (
      <div className="dashboard-shell">
        <aside className="dashboard-sidebar">
          <div>
            <p className="eyebrow">Signed In</p>
            <h2>{session.company.name}</h2>
          </div>
          <nav className="dashboard-nav">
            <a href="#overview">Overview</a>
            <a href="#users">Users</a>
            <a href="#expenses">Expenses</a>
            <a href="#approvals">Approvals</a>
            <a href="#rules">Approval Rules</a>
          </nav>
          <button className="ghost-button" type="button" onClick={handleLogout}>
            Sign out
          </button>
        </aside>

        <main className="dashboard-main">
          <header className="welcome-card" id="overview">
            <div>
              <p className="eyebrow">Account Ready</p>
              <h1>{session.user.fullName}</h1>
              <p className="welcome-copy">
                The onboarding flow is live. Your next implementation step is user management,
                expense submission, and rule-driven approvals on top of this company context.
              </p>
            </div>
            <div className="badge-stack">
              <span className="pill">{session.user.roles.join(" / ")}</span>
              <span className="pill pill-soft">
                {session.company.countryCode} · {session.company.baseCurrency}
              </span>
            </div>
          </header>

          <section className="metrics-grid">
            <article className="metric-card">
              <span className="metric-label">Base Currency</span>
              <strong>{session.company.baseCurrency}</strong>
              <p>All submitted expenses will be normalized into this currency for approval review.</p>
            </article>
            <article className="metric-card">
              <span className="metric-label">Current Role</span>
              <strong>{session.user.roles[0] ?? "Admin"}</strong>
              <p>Company onboarding automatically attached the admin role to the first user.</p>
            </article>
            <article className="metric-card">
              <span className="metric-label">Ready Next</span>
              <strong>Users + Expenses</strong>
              <p>The backend now supports auth, so role management and expense APIs can build on it.</p>
            </article>
          </section>

          <section className="next-step-grid">
            <article className="roadmap-card" id="users">
              <h3>What is already working</h3>
              <ul>
                <li>Dynamic country and currency loading through the backend</li>
                <li>Admin company signup with default categories</li>
                <li>Login with JWT-based session creation</li>
                <li>Responsive entry UI with project-aligned styling</li>
              </ul>
            </article>

            <article className="roadmap-card" id="expenses">
              <h3>Next implementation slice</h3>
              <ul>
                <li>Admin user creation and manager mapping</li>
                <li>Employee expense draft and submission APIs</li>
                <li>Manager approval queue and actions</li>
                <li>Rule configuration screens and workflow engine wiring</li>
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
              <li>Default categories ready for expense creation</li>
            </ul>
          </article>

          <article className="hero-card hero-card-accent">
            <span className="hero-card-title">What comes next</span>
            <ul>
              <li>User and manager mapping</li>
              <li>Expense drafts and submission</li>
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
                setFieldErrors({});
                setSubmissionError("");
              }}
            >
              Signup
            </button>
            <button
              className={mode === "login" ? "mode-button is-active" : "mode-button"}
              type="button"
              onClick={() => {
                setMode("login");
                setFieldErrors({});
                setSubmissionError("");
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

        {submissionError ? (
          <div className="alert-box alert-box-danger">
            <strong>Request could not be completed.</strong>
            <p>{submissionError}</p>
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
              {fieldErrors.companyName ? <small>{fieldErrors.companyName}</small> : null}
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
                {fieldErrors.firstName ? <small>{fieldErrors.firstName}</small> : null}
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
                {fieldErrors.lastName ? <small>{fieldErrors.lastName}</small> : null}
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
              {fieldErrors.email ? <small>{fieldErrors.email}</small> : null}
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
                {fieldErrors.countryCode ? <small>{fieldErrors.countryCode}</small> : null}
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
              {fieldErrors.password ? <small>{fieldErrors.password}</small> : null}
            </label>

            <button className="primary-button" type="submit" disabled={isSubmitting || countriesLoading}>
              {isSubmitting ? "Creating workspace..." : "Create workspace"}
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
              {fieldErrors.email ? <small>{fieldErrors.email}</small> : null}
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
              {fieldErrors.password ? <small>{fieldErrors.password}</small> : null}
            </label>

            <button className="primary-button" type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Signing in..." : "Sign in"}
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
