import { useEffect, useState, type ReactNode } from "react";
import { authAPI, patientsAPI, appointmentsAPI, analysesAPI, documentsAPI, adminAPI } from "./api";
import { setAuthToken, clearAuthToken, getCurrentUser, setCurrentUser } from "./config";

type View =
  | "landing"
  | "clinical-login"
  | "doctor-dashboard"
  | "assistant-dashboard"
  | "patient-search"
  | "patient-chart"
  | "add-info"
  | "processing"
  | "report"
  | "confirmation"
  | "intake"
  | "uploads"
  | "compare"
  | "print-report"
  | "admin-login"
  | "admin-home"
  | "admin-users"
  | "admin-data"
  | "admin-monitoring";

type ButtonProps = {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "quiet" | "danger";
  type?: "button" | "submit";
  className?: string;
  disabled?: boolean;
  "aria-expanded"?: boolean;
  "aria-controls"?: string;
  onKeyDown?: (event: React.KeyboardEvent<HTMLButtonElement>) => void;
};

function Button({
  children,
  onClick,
  variant = "primary",
  type = "button",
  className = "",
  disabled = false,
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`button button--${variant} ${className}`}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}

function LinkButton({
  children,
  onClick,
  className = "",
}: {
  children: ReactNode;
  onClick: () => void;
  className?: string;
}) {
  return (
    <button className={`text-link ${className}`} type="button" onClick={onClick}>
      {children}
    </button>
  );
}

function Field({
  label,
  placeholder,
  type = "text",
  defaultValue,
  value,
  onChange,
  required,
  hint,
  error,
  name,
}: {
  label: string;
  placeholder?: string;
  type?: string;
  defaultValue?: string;
  value?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
  hint?: string;
  error?: string;
  name?: string;
}) {
  const id = name || label.toLowerCase().replace(/\W+/g, "-");
  return (
    <label className="field" htmlFor={id}>
      <span className="field__label">
        {label}
        {required && <span aria-hidden="true"> *</span>}
      </span>
      <input
        id={id}
        name={id}
        type={type}
        placeholder={placeholder}
        defaultValue={defaultValue}
        value={value}
        onChange={onChange}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
      />
      {error && (
        <span className="field__error" id={`${id}-error`} role="alert">
          {error}
        </span>
      )}
      {hint && (
        <span className="field__hint" id={`${id}-hint`}>
          {hint}
        </span>
      )}
    </label>
  );
}

function TextArea({
  label,
  placeholder,
  defaultValue,
  name,
}: {
  label: string;
  placeholder?: string;
  defaultValue?: string;
  name?: string;
}) {
  const id = name || label.toLowerCase().replace(/\W+/g, "-");
  return (
    <label className="field" htmlFor={id}>
      <span className="field__label">{label}</span>
      <textarea id={id} name={id} rows={4} placeholder={placeholder} defaultValue={defaultValue} />
    </label>
  );
}

function SelectField({
  label,
  children,
  name,
}: {
  label: string;
  children: ReactNode;
  name?: string;
}) {
  const id = name || label.toLowerCase().replace(/\W+/g, "-");
  return (
    <label className="field" htmlFor={id}>
      <span className="field__label">{label}</span>
      <select id={id} name={id}>{children}</select>
    </label>
  );
}

function Status({
  tone,
  children,
}: {
  tone: "success" | "caution" | "critical" | "neutral" | "admin";
  children: ReactNode;
}) {
  return <span className={`status status--${tone}`}>{children}</span>;
}

function LoadingSpinner() {
  return (
    <div className="processing-mark" aria-label="Loading">
      <span />
    </div>
  );
}

// Simple context for current patient
const PatientContext = ({ patient }: { patient: any }) => {
  if (!patient) return null;
  
  return (
    <div className="patient-context">
      <div>
        <span className="patient-context__name">{patient.full_name}</span>
        <span>{patient.age} years</span>
        <span>{patient.gender}</span>
      </div>
      <div className="patient-context__ids">
        <span>Patient ID <code>{patient.id}</code></span>
        <span>MRN <code>{patient.mrn}</code></span>
      </div>
    </div>
  );
};

// This is a simplified integration example
// Due to the large size of the original App.tsx, I'm creating key integrated components
// You'll need to merge this with your existing App.tsx

export default function App() {
  const [view, setView] = useState<View>("landing");
  const [currentPatient, setCurrentPatient] = useState<any>(null);
  
  const navigate = (nextView: View) => {
    setView(nextView);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // This is a starter - you'll integrate more components based on FRONTEND_INTEGRATION_GUIDE.md
  return (
    <div className="app">
      {view === "landing" && <Landing navigate={navigate} />}
      {view === "clinical-login" && <IntegratedLogin navigate={navigate} admin={false} />}
      {view === "admin-login" && <IntegratedLogin navigate={navigate} admin={true} />}
      {view === "doctor-dashboard" && <IntegratedDoctorDashboard navigate={navigate} />}
      {view === "patient-search" && <IntegratedPatientSearch navigate={navigate} setCurrentPatient={setCurrentPatient} />}
      {/* Add more views as needed */}
    </div>
  );
}

// Integrated Login Component
function IntegratedLogin({
  admin = false,
  navigate,
}: {
  admin?: boolean;
  navigate: (view: View) => void;
}) {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState(admin ? "admin@northlake.org" : "maya.patel@northlake.org");
  const [password, setPassword] = useState("clinical-access");
  const [clinicalRole, setClinicalRole] = useState<"doctor" | "assistant">("doctor");

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(false);

    try {
      const response = await authAPI.login(email, password);
      setAuthToken(response.access_token);
      setCurrentUser(response.user);
      
      // Navigate based on role
      if (response.user.role === 'admin') {
        navigate('admin-home');
      } else if (response.user.role === 'assistant') {
        navigate('assistant-dashboard');
      } else {
        navigate('doctor-dashboard');
      }
    } catch (err) {
      setError(true);
      setLoading(false);
    }
  };

  return (
    <div className={`login-page ${admin ? "theme-admin" : ""}`}>
      <header className="login-topbar">
        <button className="wordmark" onClick={() => navigate("landing")}>
          Clin<span>IQ</span>{admin && <em>Admin</em>}
        </button>
        <LinkButton onClick={() => navigate("landing")}>Return to public site</LinkButton>
      </header>
      <main className="login-main">
        <div className="login-context">
          <p>{admin ? "Operations access" : "Hospital workforce access"}</p>
          <h1>{admin ? "Admin console" : "Clinical app"}</h1>
          <p>
            {admin
              ? "Manage users, knowledge sources, and system performance."
              : "Secure access for doctors and clinical assistants."}
          </p>
        </div>
        <form className="login-form" onSubmit={handleLogin}>
          <h2>{admin ? "Admin sign in" : "Sign in to the clinical app"}</h2>
          
          {!admin && (
            <div className="role-select">
              <label htmlFor="clinical-role">
                <span className="field__label">Clinical role</span>
                <span className="select-control">
                  <select
                    id="clinical-role"
                    value={clinicalRole}
                    onChange={(e) => {
                      setClinicalRole(e.target.value as "doctor" | "assistant");
                      setEmail(e.target.value === "doctor" ? "maya.patel@northlake.org" : "jamie.rivera@northlake.org");
                    }}
                  >
                    <option value="doctor">Doctor</option>
                    <option value="assistant">Clinical assistant</option>
                  </select>
                </span>
              </label>
            </div>
          )}
          
          {error && (
            <div className="form-error" role="alert">
              <strong>Login failed.</strong>
              <span>Check your credentials and try again.</span>
            </div>
          )}
          
          <Field
            label="Work email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Field
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            error={error ? "Incorrect password" : undefined}
          />
          <Button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </main>
    </div>
  );
}

// Integrated Doctor Dashboard
function IntegratedDoctorDashboard({ navigate }: { navigate: (view: View) => void }) {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    appointmentsAPI.getToday()
      .then((data: any) => {
        setAppointments(data);
        setLoading(false);
      })
      .catch((err: any) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="page" style={{ textAlign: "center", padding: "100px" }}>
        <LoadingSpinner />
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="form-error">Error loading dashboard: {error}</div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Today's Appointments</h1>
      <div className="data-table">
        {appointments.length === 0 ? (
          <p>No appointments today</p>
        ) : (
          appointments.map((apt: any) => (
            <div key={apt.id} className="data-row">
              <span>{new Date(apt.appointment_time).toLocaleTimeString()}</span>
              <span>{apt.patient_name}</span>
              <span>{apt.reason}</span>
              <Status tone="neutral">{apt.status}</Status>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Integrated Patient Search
function IntegratedPatientSearch({ 
  navigate, 
  setCurrentPatient 
}: { 
  navigate: (view: View) => void;
  setCurrentPatient: (patient: any) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const data = await patientsAPI.search(query);
      setResults(data);
      setSearched(true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePatientClick = (patient: any) => {
    setCurrentPatient(patient);
    navigate("patient-chart");
  };

  return (
    <div className="page">
      <h1>Patient Search</h1>
      
      <section className="search-panel">
        <label className="search-field">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter patient ID, MRN, or name"
            onKeyPress={(e) => e.key === "Enter" && handleSearch()}
          />
        </label>
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? "Searching..." : "Search patients"}
        </Button>
        <Button variant="quiet" onClick={() => { setQuery(""); setResults([]); setSearched(false); }}>
          Clear
        </Button>
      </section>

      {loading && (
        <div style={{ textAlign: "center", padding: "40px" }}>
          <LoadingSpinner />
        </div>
      )}

      {searched && !loading && (
        <section className="data-section">
          <div className="section-title">
            <h2>Search results</h2>
            <p>{results.length} patient(s) found</p>
          </div>
          
          {results.length === 0 ? (
            <div className="empty-state">
              <strong>No patients found</strong>
              <p>Try a different search term</p>
            </div>
          ) : (
            <div className="data-table search-results">
              <div className="data-row data-row--head">
                <span>Patient</span>
                <span>Patient ID</span>
                <span>MRN</span>
                <span>Date of birth</span>
                <span />
              </div>
              {results.map((patient: any) => (
                <button className="data-row" key={patient.id} onClick={() => handlePatientClick(patient)}>
                  <span data-label="Patient">
                    <strong>{patient.full_name}</strong>
                    <small>{patient.gender} · {patient.age} years</small>
                  </span>
                  <span data-label="Patient ID" className="mono">{patient.id}</span>
                  <span data-label="MRN" className="mono">{patient.mrn}</span>
                  <span data-label="Date of birth">{patient.date_of_birth}</span>
                  <span className="row-action">Open chart</span>
                </button>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

// Placeholder Landing component (use your original)
function Landing({ navigate }: { navigate: (view: View) => void }) {
  return (
    <div className="landing">
      <header className="public-header">
        <button className="wordmark" onClick={() => navigate("landing")}>
          Clin<span>IQ</span>
        </button>
        <div className="signin-wrap">
          <Button variant="quiet" onClick={() => navigate("clinical-login")}>
            Sign in
          </Button>
        </div>
      </header>
      <main>
        <section className="hero">
          <div className="hero__copy">
            <h1>Clinical decision support with real-time AI</h1>
            <p className="hero__lead">
              ClinIQ connects to your backend API for real patient data and AI analysis.
            </p>
            <div className="hero__actions">
              <Button onClick={() => navigate("clinical-login")}>Sign in</Button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
