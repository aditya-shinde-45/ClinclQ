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
  | "schedule-appointment"
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
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`button button--${variant} ${className}`}
      onClick={onClick}
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
  value,
  defaultValue,
  onChange,
  required,
  hint,
  error,
}: {
  label: string;
  placeholder?: string;
  type?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
  hint?: string;
  error?: string;
}) {
  const id = label.toLowerCase().replace(/\W+/g, "-");
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
        value={value}
        defaultValue={defaultValue}
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
  value,
  defaultValue,
  onChange,
}: {
  label: string;
  placeholder?: string;
  value?: string;
  defaultValue?: string;
  onChange?: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}) {
  const id = label.toLowerCase().replace(/\W+/g, "-");
  return (
    <label className="field" htmlFor={id}>
      <span className="field__label">{label}</span>
      <textarea id={id} rows={4} placeholder={placeholder} value={value} defaultValue={defaultValue} onChange={onChange} />
    </label>
  );
}

function SelectField({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  const id = label.toLowerCase().replace(/\W+/g, "-");
  return (
    <label className="field" htmlFor={id}>
      <span className="field__label">{label}</span>
      <select id={id}>{children}</select>
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

// Patient data now comes from API - see PatientContext component

function Timeline({ compact = false, patientId }: { compact?: boolean; patientId?: string }) {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    
    setLoading(true);
    patientsAPI.getTimeline(patientId)
      .then(data => {
        setTimeline(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load timeline:', err);
        setLoading(false);
      });
  }, [patientId]);

  if (loading) {
    return <div className="timeline"><p>Loading timeline...</p></div>;
  }

  if (timeline.length === 0) {
    return <div className="timeline"><p>No timeline events yet</p></div>;
  }

  return (
    <div className={`timeline ${compact ? "timeline--compact" : ""}`}>
      {timeline.map((item, idx) => (
        <div className="timeline__item" key={`${item.visit_date}-${idx}`}>
          <div className="timeline__marker" aria-hidden="true" />
          <div className="timeline__date">{new Date(item.visit_date).toLocaleDateString()}</div>
          <div className="timeline__content">
            <div className="timeline__topline">
              <strong>{item.title}</strong>
              <Status tone="neutral">{item.type}</Status>
            </div>
            <p>{item.body}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function PatientContext({ patient }: { patient: any }) {
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
}

function ClinicalShell({
  view,
  navigate,
  children,
  currentPatient,
  role = "Doctor",
}: {
  view: View;
  navigate: (view: View) => void;
  children: ReactNode;
  currentPatient?: any;
  role?: "Doctor" | "Assistant";
}) {
  const [accountMenu, setAccountMenu] = useState(false);
  const [timeoutWarning, setTimeoutWarning] = useState(false);
  const user = getCurrentUser();
  
  useEffect(() => {
    if (!timeoutWarning) return;
    const autoLogout = window.setTimeout(() => {
      clearAuthToken();
      navigate("clinical-login");
    }, 120_000);
    return () => window.clearTimeout(autoLogout);
  }, [timeoutWarning, navigate]);
  
  const tabs =
    role === "Doctor"
      ? [
          ["doctor-dashboard", "Today"],
          ["patient-search", "Patient search"],
          ["patient-chart", "Patient chart"],
          ["report", "Clinical report"],
        ]
      : [
          ["assistant-dashboard", "Workspace"],
          ["intake", "Register patient"],
          ["schedule-appointment", "Schedule"],
          ["uploads", "Documents"],
          ["patient-search", "Patient search"],
        ];
  return (
    <div className="app-shell">
      <header className="utility-bar">
        <button className="wordmark" onClick={() => navigate(role === "Doctor" ? "doctor-dashboard" : "assistant-dashboard")}>
          Clin<span>IQ</span>
        </button>
        <div className="utility-bar__right">
          <span className="facility">Northlake Medical Center</span>
          <span className="role-badge">{role}</span>
          <button className="user-menu" type="button" aria-label="Open user menu" aria-expanded={accountMenu} onClick={() => setAccountMenu(!accountMenu)}>
            {user?.full_name || (role === "Doctor" ? "Dr. Maya Patel" : "Jamie Rivera")}
            <span aria-hidden="true">⌄</span>
          </button>
          {accountMenu && (
            <div className="account-menu">
              <span>Signed in securely</span>
              <button onClick={() => { setAccountMenu(false); setTimeoutWarning(true); }}>View session timeout</button>
              <button onClick={() => { clearAuthToken(); navigate("clinical-login"); }}>Log out</button>
            </div>
          )}
        </div>
      </header>
      {currentPatient && <PatientContext patient={currentPatient} />}
      <nav className="task-tabs" aria-label="Clinical tasks">
        <div className="task-tabs__inner">
          {tabs.map(([target, label]) => (
            <button
              className={view === target ? "is-active" : ""}
              key={target}
              onClick={() => navigate(target as View)}
            >
              {label}
            </button>
          ))}
        </div>
      </nav>
      {children}
      {timeoutWarning && (
        <div className="modal-backdrop" role="presentation">
          <div className="timeout-dialog" role="alertdialog" aria-modal="true" aria-labelledby="timeout-title" aria-describedby="timeout-description">
            <span>Session security</span>
            <h2 id="timeout-title">Your session will end in 2 minutes</h2>
            <p id="timeout-description">For patient privacy, ClinIQ signs you out after a period of inactivity. Unsaved changes may be lost.</p>
            <div>
              <Button variant="secondary" onClick={() => { clearAuthToken(); navigate("clinical-login"); }}>Sign out now</Button>
              <Button onClick={() => setTimeoutWarning(false)}>Stay signed in</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <p className="breadcrumb">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}

function Landing({ navigate }: { navigate: (view: View) => void }) {
  const [chooser, setChooser] = useState(false);
  return (
    <div className="landing">
      <header className="public-header">
        <button className="wordmark" onClick={() => navigate("landing")}>
          Clin<span>IQ</span>
        </button>
        <nav aria-label="Public navigation">
          <a href="#how">How it works</a>
          <a href="#trust">Trust & safety</a>
          <a href="#contact">Contact</a>
        </nav>
        <div className="signin-wrap">
          <Button variant="quiet" onClick={() => setChooser(!chooser)} aria-expanded={chooser}>
            Sign in
          </Button>
          {chooser && (
            <div className="signin-chooser">
              <strong>Choose your workspace</strong>
              <p>Clinical and administrative access are managed separately.</p>
              <Button onClick={() => navigate("clinical-login")}>Clinical app sign in</Button>
              <Button variant="secondary" onClick={() => navigate("admin-login")}>
                Admin console sign in
              </Button>
            </div>
          )}
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero__copy">
            <p className="hero__kicker">Clinical decision support, with clinicians in control</p>
            <h1>Evidence-based recommendations for the decisions clinicians make every day.</h1>
            <p className="hero__lead">
              ClinIQ reviews patient context, retrieves relevant evidence, and presents a
              citation-backed recommendation. The clinician makes the final decision.
            </p>
            <div className="hero__actions">
              <Button onClick={() => navigate("clinical-login")}>View the clinical app</Button>
              <a className="text-link text-link--anchor" href="#how">
                See how it works
              </a>
            </div>
            <div className="trust-line">
              <span>Human reviewed</span>
              <span>Citation backed</span>
              <span>Audit ready</span>
            </div>
          </div>
          <ReportPreview />
        </section>

        <section className="process-section" id="how">
          <div className="section-heading">
            <p>Designed around the clinical workflow</p>
            <h2>From patient context to a recorded decision</h2>
          </div>
          <ol className="process-list">
            {[
              ["01", "Capture context", "Bring symptoms, observations, medications, and recent results together."],
              ["02", "Analyze evidence", "Cross-check patient factors against current clinical knowledge."],
              ["03", "Review recommendation", "Inspect reasoning, confidence, warnings, and source citations."],
              ["04", "Record the decision", "Approve, modify, or reject—with the clinician’s rationale preserved."],
            ].map(([number, title, text]) => (
              <li key={number}>
                <span>{number}</span>
                <strong>{title}</strong>
                <p>{text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="trust-section" id="trust">
          <div className="trust-section__statement">
            <p>Trust and safety</p>
            <h2>Clinical judgment remains the final authority.</h2>
          </div>
          <div className="trust-principles">
            <div>
              <strong>Human in the loop</strong>
              <p>Every recommendation requires an explicit clinician decision before it enters the record.</p>
            </div>
            <div>
              <strong>Evidence in view</strong>
              <p>Reasoning links directly to guidelines and source evidence for inspection at the point of care.</p>
            </div>
            <div>
              <strong>Privacy by design</strong>
              <p>Access controls, audit trails, and hospital-managed identity protect patient information.</p>
            </div>
          </div>
        </section>
      </main>
      <footer className="public-footer" id="contact">
        <div>
          <button className="wordmark" onClick={() => navigate("landing")}>Clin<span>IQ</span></button>
          <p>Clinical decision support for hospital care teams.</p>
        </div>
        <div>
          <strong>Access</strong>
          <LinkButton onClick={() => navigate("clinical-login")}>Clinical app sign in</LinkButton>
          <LinkButton onClick={() => navigate("admin-login")}>Admin console sign in</LinkButton>
        </div>
        <div>
          <strong>Contact</strong>
          <p>clinicalsystems@cliniq.health</p>
          <p>Security and procurement inquiries</p>
        </div>
      </footer>
    </div>
  );
}

function ReportPreview() {
  return (
    <div className="report-preview" aria-label="Clinical report preview">
      <div className="report-preview__bar">
        <div>
          <span>Clinical analysis</span>
          <strong>CDS report 2025-0618</strong>
        </div>
        <Status tone="caution">Needs review</Status>
      </div>
      <div className="report-preview__patient">
        <span>Patient context</span>
        <strong>57F · Dyspnea · Chest pressure</strong>
      </div>
      <div className="preview-heading">
        <span>Rank</span>
        <span>Potential diagnosis</span>
        <span>Confidence</span>
      </div>
      <div className="preview-row">
        <span>01</span>
        <div><strong>Stable angina</strong><small>4 supporting findings</small></div>
        <strong>78%</strong>
      </div>
      <div className="preview-row">
        <span>02</span>
        <div><strong>Heart failure exacerbation</strong><small>3 supporting findings</small></div>
        <strong>64%</strong>
      </div>
      <div className="preview-evidence">
        <span>Evidence trail</span>
        <p>2024 ACC/AHA guideline · Patient medication history · ECG 18 Jun</p>
      </div>
      <div className="preview-decision">
        <span>Clinician decision required</span>
        <div><i /><i /><i /></div>
      </div>
    </div>
  );
}

function Login({
  admin = false,
  navigate,
}: {
  admin?: boolean;
  navigate: (view: View) => void;
}) {
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const [recoveryHelp, setRecoveryHelp] = useState(false);
  const [clinicalRole, setClinicalRole] = useState<"doctor" | "assistant">("doctor");
  const [email, setEmail] = useState(admin ? "admin@northlake.org" : "maya.patel@northlake.org");
  const [password, setPassword] = useState("clinical-access");

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
          {!admin && (
            <div className="access-note">
              <strong>Authorized clinical staff only</strong>
              <p>Patient information is monitored and access is recorded in the audit log.</p>
            </div>
          )}
        </div>
        <form className="login-form" onSubmit={handleLogin}>
          <h2>{admin ? "Admin sign in" : "Sign in to the clinical app"}</h2>
          <p>{admin ? "Use your administrator credentials." : "Access is based on your assigned hospital role."}</p>
          {!admin && (
            <div className="role-select">
              <label htmlFor="clinical-role">
                <span className="field__label">Clinical role</span>
                <span className="select-control">
                  <select
                    id="clinical-role"
                    name="clinical-role"
                    value={clinicalRole}
                    onChange={(event) => {
                      const newRole = event.target.value as "doctor" | "assistant";
                      setClinicalRole(newRole);
                      setEmail(newRole === "doctor" ? "maya.patel@northlake.org" : "jamie.rivera@northlake.org");
                      setError(false);
                    }}
                  >
                    <option value="doctor">Doctor</option>
                    <option value="assistant">Clinical assistant</option>
                  </select>
                  <span aria-hidden="true">⌄</span>
                </span>
              </label>
              <div className="role-context" aria-live="polite">
                <strong>{clinicalRole === "doctor" ? "Doctor workspace" : "Clinical assistant workspace"}</strong>
                <span>
                  {clinicalRole === "doctor"
                    ? "Review patient charts, request clinical analysis, and record final decisions."
                    : "Register patients, prepare records, and attach clinical documents."}
                </span>
              </div>
            </div>
          )}
          {error && (
            <div className="form-error" role="alert">
              <strong>We couldn't verify those credentials.</strong>
              <span>Check your details or contact your hospital administrator.</span>
            </div>
          )}
          {!admin && <div className="credential-heading"><strong>Hospital credentials</strong></div>}
          <Field
            key={admin ? "admin" : clinicalRole}
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
            error={error ? "The password is incorrect. Try again or contact your hospital administrator." : undefined}
          />
          <Button type="submit" disabled={loading}>
            {loading ? "Signing in..." : admin ? "Sign in to admin console" : `Continue to ${clinicalRole === "doctor" ? "doctor workspace" : "assistant workspace"}`}
          </Button>
          <LinkButton onClick={() => setRecoveryHelp(!recoveryHelp)}>Forgot your password?</LinkButton>
          {recoveryHelp && (
            <p className="login-help" role="status">
              Password recovery is handled by your hospital identity system. Open your hospital identity portal or contact your administrator if access is blocked.
            </p>
          )}
        </form>
      </main>
    </div>
  );
}


function DoctorDashboard({ navigate, setCurrentPatient }: { navigate: (view: View) => void; setCurrentPatient: (p: any) => void }) {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [apptLoading, setApptLoading] = useState(true);
  const [patients, setPatients] = useState<any[]>([]);
  const [patientsLoading, setPatientsLoading] = useState(true);
  const user = getCurrentUser();

  useEffect(() => {
    appointmentsAPI.getToday()
      .then(data => setAppointments(data as any[]))
      .catch(err => console.error("Failed to load appointments:", err))
      .finally(() => setApptLoading(false));

    patientsAPI.search("")
      .then(data => setPatients(data as any[]))
      .catch(err => console.error("Failed to load patients:", err))
      .finally(() => setPatientsLoading(false));
  }, []);

  const handleOpenChart = async (appt: any) => {
    try {
      const patient = await patientsAPI.getById(appt.patient_id);
      setCurrentPatient(patient);
      navigate("patient-chart");
    } catch (err) {
      console.error("Failed to load patient:", err);
    }
  };

  const handlePatientClick = (patient: any) => {
    setCurrentPatient(patient);
    navigate("patient-chart");
  };

  const apptTone = (s: string): "success" | "caution" | "neutral" | "critical" | "admin" =>
    s === "completed" ? "success" : s === "in_progress" ? "caution" : "neutral";

  return (
    <ClinicalShell view="doctor-dashboard" navigate={navigate}>
      <main className="page">
        <PageHeader
          eyebrow={new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          title={"Good morning, " + (user?.full_name || "Doctor")}
          description={"You have " + appointments.length + " appointments today."}
          actions={<Button variant="secondary" onClick={() => navigate("patient-search")}>Find a patient</Button>}
        />
        <div className="summary-strip">
          <div><strong>{appointments.length}</strong><span>Appointments today</span></div>
          <div><strong>{appointments.filter(a => a.status === "scheduled" || a.status === "checked_in").length}</strong><span>Waiting</span></div>
          <div><strong>{appointments.filter(a => a.status === "in_progress").length}</strong><span>In progress</span></div>
          <div><strong>{appointments.filter(a => a.status === "completed").length}</strong><span>Completed</span></div>
        </div>
        <section className="data-section">
          <div className="section-title">
            <div><h2>Today's patient queue</h2><p>Appointments assigned to you</p></div>
          </div>
          <div className="data-table queue-table">
            <div className="data-row data-row--head">
              <span>Time</span><span>Patient</span><span>Patient ID</span><span>Reason</span><span>Status</span><span />
            </div>
            {apptLoading ? (
              <div className="empty-state"><strong>Loading appointments...</strong></div>
            ) : appointments.length === 0 ? (
              <div className="empty-state"><strong>No appointments today</strong></div>
            ) : appointments.map(appt => (
              <button className="data-row" key={appt.id} onClick={() => handleOpenChart(appt)}>
                <span data-label="Time">{appt.appointment_time ? new Date(appt.appointment_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "--"}</span>
                <span data-label="Patient"><strong>{appt.patient_name}</strong></span>
                <span data-label="Patient ID" className="mono">{appt.patient_id}</span>
                <span data-label="Reason">{appt.reason || "--"}</span>
                <span data-label="Status"><Status tone={apptTone(appt.status)}>{appt.status}</Status></span>
                <span className="row-action">Open chart</span>
              </button>
            ))}
          </div>
        </section>
        <section className="data-section">
          <div className="section-title">
            <div><h2>All patients</h2><p>{patients.length} patient(s) in the system</p></div>
            <Button variant="secondary" onClick={() => navigate("patient-search")}>Advanced search</Button>
          </div>
          <div className="data-table search-results">
            <div className="data-row data-row--head"><span>Patient</span><span>Patient ID</span><span>MRN</span><span>Date of birth</span><span>Last activity</span><span /></div>
            {patientsLoading ? (
              <div className="empty-state"><strong>Loading patients...</strong></div>
            ) : patients.length === 0 ? (
              <div className="empty-state"><strong>No patients found</strong></div>
            ) : patients.slice(0, 10).map((patient: any) => (
              <button className="data-row" key={patient.id} onClick={() => handlePatientClick(patient)}>
                <span data-label="Patient"><strong>{patient.full_name}</strong><small>{patient.gender} · {patient.age} years</small></span>
                <span data-label="Patient ID" className="mono">{patient.id}</span>
                <span data-label="MRN" className="mono">{patient.mrn}</span>
                <span data-label="Date of birth">{patient.date_of_birth}</span>
                <span data-label="Last activity">{patient.last_visit || 'No visits'}</span>
                <span className="row-action">Open chart</span>
              </button>
            ))}
          </div>
          {patients.length > 10 && (
            <div style={{ textAlign: "center", padding: "20px" }}>
              <Button variant="secondary" onClick={() => navigate("patient-search")}>View all {patients.length} patients</Button>
            </div>
          )}
        </section>
      </main>
    </ClinicalShell>
  );
}

function PatientSearch({ navigate, setCurrentPatient, role = "Doctor" }: { navigate: (view: View) => void; setCurrentPatient: (patient: any) => void; role?: "Doctor" | "Assistant" }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    loadAllPatients();
  }, []);

  const loadAllPatients = async () => {
    setLoading(true);
    try {
      const data = await patientsAPI.search("");
      setResults(data);
      setSearched(true);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
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
    <ClinicalShell view="patient-search" navigate={navigate} role={role}>
      <main className="page">
        <PageHeader title="Patient search" description="Search by patient ID, MRN, or full name." />
        <section className="search-panel">
          <label className="search-field">
            <span className="sr-only">Patient ID, MRN, or name</span>
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
          <Button variant="quiet" onClick={() => { setQuery(""); loadAllPatients(); }}>Clear</Button>
        </section>
        {loading && (
          <div style={{ textAlign: "center", padding: "40px" }}>
            <div className="processing-mark" aria-label="Loading"><span /></div>
          </div>
        )}
        {searched && !loading && (
          <section className="data-section">
            <div className="section-title"><div><h2>{query ? "Search results" : "All patients"}</h2><p>{results.length} patient(s) found</p></div></div>
            {results.length === 0 ? (
              <div className="empty-state">
                <strong>No patients found</strong>
                <p>Try a different search term</p>
              </div>
            ) : (
              <div className="data-table search-results">
                <div className="data-row data-row--head"><span>Patient</span><span>Patient ID</span><span>MRN</span><span>Date of birth</span><span>Last activity</span><span /></div>
                {results.map((patient: any) => (
                  <button className="data-row" key={patient.id} onClick={() => handlePatientClick(patient)}>
                    <span data-label="Patient"><strong>{patient.full_name}</strong><small>{patient.gender} · {patient.age} years</small></span>
                    <span data-label="Patient ID" className="mono">{patient.id}</span>
                    <span data-label="MRN" className="mono">{patient.mrn}</span>
                    <span data-label="Date of birth">{patient.date_of_birth}</span>
                    <span data-label="Last activity">{patient.last_visit || 'No visits'}</span>
                    <span className="row-action">Open chart</span>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}
        {!searched && !loading && (
          <div className="empty-state">
            <strong>Loading patients...</strong>
          </div>
        )}
      </main>
    </ClinicalShell>
  );
}

function PatientChart({ navigate, currentPatient, role = "Doctor" }: { navigate: (view: View) => void; currentPatient: any; role?: "Doctor" | "Assistant" }) {
  const [timeline, setTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!currentPatient) return;

    patientsAPI.getTimeline(currentPatient.id)
      .then(data => {
        setTimeline(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load timeline:', err);
        setLoading(false);
      });
  }, [currentPatient]);

  if (!currentPatient) {
    return (
      <ClinicalShell view="patient-chart" navigate={navigate} role={role}>
        <main className="page">
          <div className="empty-state">
            <strong>No patient selected</strong>
            <p>Please search for a patient first</p>
          </div>
        </main>
      </ClinicalShell>
    );
  }

  return (
    <ClinicalShell view="patient-chart" navigate={navigate} currentPatient={currentPatient} role={role}>
      <main className="page">
        <PageHeader
          eyebrow="Patient chart"
          title={currentPatient.full_name}
          description={`Current visit opened ${currentPatient.last_visit || 'today'}`}
          actions={role === "Doctor" ? (
            <>
              <Button variant="secondary" onClick={() => navigate("compare")}>Compare reports</Button>
              <Button variant="secondary" onClick={() => navigate("add-info")}>Re-run analysis</Button>
              <Button onClick={() => navigate("add-info")}>Add clinical info</Button>
            </>
          ) : <Status tone="neutral">Read-only access</Status>}
        />
        {currentPatient.allergies && (
          <div className="alert-line">
            <strong>Allergy recorded:</strong>
            <span>{currentPatient.allergies}</span>
            <span>Verified {currentPatient.last_visit}</span>
          </div>
        )}
        <div className="chart-layout">
          <div className="chart-summary">
            <section>
              <h2>Medical history</h2>
              <dl className="fact-list">
                <div><dt>Active conditions</dt><dd>{currentPatient.medical_history || 'No active conditions recorded'}</dd></div>
                <div><dt>Current medications</dt><dd>{currentPatient.current_medications || 'No medications recorded'}</dd></div>
                <div><dt>Past diagnoses</dt><dd>{currentPatient.past_diagnosis || 'None'}</dd></div>
                <div><dt>Past treatments</dt><dd>{currentPatient.past_treatments || 'None'}</dd></div>
              </dl>
            </section>
            <section>
              <h2>Clinical overview</h2>
              <dl className="metric-list">
                <div><dt>Blood pressure</dt><dd>-- <small>mmHg</small></dd></div>
                <div><dt>Heart rate</dt><dd>-- <small>bpm</small></dd></div>
                <div><dt>O₂ saturation</dt><dd>--<small>%</small></dd></div>
              </dl>
            </section>
          </div>
          <section className="history-section">
            <div className="section-title">
              <div><h2>Previous records</h2><p>Chronological clinical history</p></div>
              <select aria-label="Filter record type"><option>All record types</option><option>Lab results</option><option>AI analyses</option></select>
            </div>
            <Timeline patientId={currentPatient.id} />
            <Button variant="secondary">Load earlier records</Button>
          </section>
        </div>
      </main>
    </ClinicalShell>
  );
}

function AddInfo({
  navigate,
  currentPatient,
  setCurrentAnalysis,
}: {
  navigate: (view: View) => void;
  currentPatient: any;
  setCurrentAnalysis: (a: any) => void;
}) {
  const patient = currentPatient || {
    id: "CLQ-10482",
    full_name: "Sunita Jadhav",
    age: 58,
    gender: "Female",
  };
  const [symptoms, setSymptoms] = useState(patient.reason_for_visit || "");
  const [observations, setObservations] = useState("");
  const [impression, setImpression] = useState("");
  const [testResults, setTestResults] = useState("");
  const [allergies, setAllergies] = useState("");
  const [testsToPerform, setTestsToPerform] = useState("");
  const [notes, setNotes] = useState(
    [
      patient.current_medications
        ? `Current medications: ${patient.current_medications}`
        : "",
      patient.past_treatments ? `Past treatments: ${patient.past_treatments}` : "",
      patient.allergies ? `Known allergies: ${patient.allergies}` : "",
    ]
      .filter(Boolean)
      .join("\n")
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setSymptoms(patient.reason_for_visit || "");
    setObservations("");
    setImpression("");
    setNotes(
      [
        patient.current_medications
          ? `Current medications: ${patient.current_medications}`
          : "",
        patient.past_treatments ? `Past treatments: ${patient.past_treatments}` : "",
        patient.allergies ? `Known allergies: ${patient.allergies}` : "",
      ]
        .filter(Boolean)
        .join("\n")
    );
  }, [patient.id]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        patient_id: patient.id,
        new_symptoms: symptoms,
        observations: observations,
        test_results: testResults,
        clinical_notes: [impression, notes, allergies ? `New allergy: ${allergies}` : "", `Tests to perform: ${testsToPerform}`].filter(Boolean).join(" | "),
      };
      const res = await analysesAPI.request(payload);
      setCurrentAnalysis(res);
      navigate("processing");
    } catch (err: any) {
      console.error("Failed to request analysis:", err);
      setError(err.message || "Failed to initiate clinical analysis.");
      setSubmitting(false);
    }
  };

  return (
    <ClinicalShell view="patient-chart" navigate={navigate} currentPatient={patient}>
      <main className="page page--form">
        <PageHeader
          eyebrow="Current visit"
          title="Add clinical information"
          description="Document changes since the previous encounter. Existing chart data and AWS Bedrock AI models will be utilized."
        />
        {error && (
          <div className="form-error" role="alert" style={{ marginBottom: "1.5rem" }}>
            <strong>{error}</strong>
          </div>
        )}
        <form className="clinical-form" onSubmit={handleSubmit}>
          <section>
            <div className="form-section-heading">
              <span>1</span>
              <div>
                <h2>Symptoms and observations</h2>
                <p>Capture the patient’s current presentation.</p>
              </div>
            </div>
            <div className="form-grid">
              <TextArea
                label="New symptoms"
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
              />
              <TextArea
                label="Current observations"
                value={observations}
                onChange={(e) => setObservations(e.target.value)}
              />
            </div>
          </section>
          <section>
            <div className="form-section-heading">
              <span>2</span>
              <div>
                <h2>Clinical findings</h2>
                <p>Add the current impression and recent results.</p>
              </div>
            </div>
            <div className="form-grid">
              <TextArea
                label="Current diagnosis or impression"
                placeholder="Enter working diagnosis or differential"
                value={impression}
                onChange={(e) => setImpression(e.target.value)}
              />
              <TextArea
                label="New test results"
                value={testResults}
                onChange={(e) => setTestResults(e.target.value)}
              />
              <TextArea
                label="New allergies"
                placeholder="Enter new allergy and reaction, or leave blank"
                value={allergies}
                onChange={(e) => setAllergies(e.target.value)}
              />
              <TextArea
                label="Tests to perform"
                value={testsToPerform}
                onChange={(e) => setTestsToPerform(e.target.value)}
              />
            </div>
          </section>
          <section>
            <div className="form-section-heading">
              <span>3</span>
              <div>
                <h2>Visit notes</h2>
                <p>Include context relevant to the AI analysis.</p>
              </div>
            </div>
            <TextArea
              label="Additional clinical notes"
              placeholder="Add relevant history, concerns, or context"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </section>
          <div className="form-actions">
            <p>
              <strong>Before requesting analysis</strong>
              <span>Review the information above for accuracy. ClinIQ will query AWS Bedrock clinical intelligence.</span>
            </p>
            <div>
              <Button variant="quiet" onClick={() => navigate("patient-chart")}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Initiating analysis..." : "Request clinical analysis"}
              </Button>
            </div>
          </div>
        </form>
      </main>
    </ClinicalShell>
  );
}

function Processing({
  navigate,
  currentAnalysis,
  setCurrentAnalysis,
  currentPatient,
}: {
  navigate: (view: View) => void;
  currentAnalysis: any;
  setCurrentAnalysis: (a: any) => void;
  currentPatient: any;
}) {
  const [stage, setStage] = useState(0);
  const stages = [
    "Reviewing patient history & chart context",
    "Invoking AWS Bedrock clinical intelligence",
    "Cross-checking drug interactions & medical guidelines",
    "Calibrating differential confidence intervals",
  ];

  useEffect(() => {
    const stageInterval = window.setInterval(() => {
      setStage((value) => Math.min(value + 1, stages.length - 1));
    }, 1100);

    let isMounted = true;
    let pollInterval: any = null;

    if (currentAnalysis?.id) {
      let attempts = 0;
      pollInterval = setInterval(async () => {
        attempts++;
        try {
          const updated = await analysesAPI.getById(currentAnalysis.id);
          if (
            updated.status === "awaiting_review" ||
            updated.status === "failed" ||
            (updated.diagnoses && updated.diagnoses.length > 0) ||
            attempts >= 25
          ) {
            if (isMounted) {
              setCurrentAnalysis(
                (attempts >= 25 || updated.status === "failed") && (!updated.diagnoses || updated.diagnoses.length === 0)
                  ? { ...updated, status: "failed", error: updated.clinical_notes || "AWS Bedrock did not return a report before the request timed out." }
                  : updated
              );
              clearInterval(pollInterval);
              navigate("report");
            }
          }
        } catch (e) {
          console.error("Error polling Bedrock analysis:", e);
          if (attempts >= 20 && isMounted) {
            clearInterval(pollInterval);
            setCurrentAnalysis({
              ...currentAnalysis,
              status: "failed",
              error: "Unable to retrieve the AWS Bedrock report. Check the backend logs and try again.",
            });
            navigate("report");
          }
        }
      }, 1500);
    } else {
      const timer = window.setTimeout(() => {
        if (isMounted) navigate("report");
      }, 4500);
      return () => {
        clearInterval(stageInterval);
        clearTimeout(timer);
      };
    }

    return () => {
      isMounted = false;
      clearInterval(stageInterval);
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [currentAnalysis?.id, navigate, setCurrentAnalysis, stages.length]);

  return (
    <ClinicalShell view="report" navigate={navigate} currentPatient={currentPatient}>
      <main className="processing-page" aria-live="polite">
        <div className="processing-mark" aria-hidden="true">
          <span />
        </div>
        <p>AWS Bedrock Clinical Decision Support in Progress</p>
        <h1>{stages[stage]}</h1>
        <p>
          ClinIQ is querying AWS Bedrock foundation model and synthesizing guideline recommendations.
        </p>
        <ol className="stage-list">
          {stages.map((item, index) => (
            <li
              className={
                index < stage ? "is-complete" : index === stage ? "is-active" : ""
              }
              key={item}
            >
              <span>
                {index < stage ? "Complete" : index === stage ? "In progress" : "Waiting"}
              </span>
              <strong>{item}</strong>
            </li>
          ))}
        </ol>
        <p className="processing-note">
          Analysis generated via AWS Bedrock (Mumbai ap-south-1). Results will link directly to this patient chart.
        </p>
      </main>
    </ClinicalShell>
  );
}

function Report({
  navigate,
  currentPatient,
  currentAnalysis,
  setLastDecision,
  print = false,
}: {
  navigate: (view: View) => void;
  currentPatient: any;
  currentAnalysis: any;
  setLastDecision: (d: any) => void;
  print?: boolean;
}) {
  const patient = currentPatient || {
    id: "CLQ-10482",
    full_name: "Sunita Jadhav",
    age: 58,
    gender: "Female",
  };
  const [expanded, setExpanded] = useState<number[]>([0]);
  const [decision, setDecision] = useState("approve");
  const [clinicianNotes, setClinicianNotes] = useState("");
  const [attestation, setAttestation] = useState(true);
  const [savingDecision, setSavingDecision] = useState(false);

  if (
    !currentAnalysis?.id ||
    currentAnalysis.status === "failed" ||
    !currentAnalysis.diagnoses?.length
  ) {
    return (
      <ClinicalShell view="report" navigate={navigate} currentPatient={patient}>
        <main className="page">
          <div className="empty-state">
            <strong>No AI-generated report is available</strong>
            <p>
              {currentAnalysis?.error ||
                "Request a new clinical analysis and wait for AWS Bedrock processing to complete."}
            </p>
            <Button onClick={() => navigate("add-info")}>Request clinical analysis</Button>
          </div>
        </main>
      </ClinicalShell>
    );
  }

  const toggle = (index: number) =>
    setExpanded((current) =>
      current.includes(index) ? current.filter((item) => item !== index) : [...current, index]
    );

  const handleRowKey = (
    event: React.KeyboardEvent<HTMLButtonElement>,
    index: number
  ) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const rows = Array.from(
        document.querySelectorAll<HTMLButtonElement>(".diagnosis-toggle")
      );
      rows[
        (index + (event.key === "ArrowDown" ? 1 : -1) + rows.length) % rows.length
      ]?.focus();
    }
  };

  const handleSaveDecision = async () => {
    setSavingDecision(true);
    const decisionObj = {
      decision_type: decision,
      clinician_notes: clinicianNotes,
      attestation_confirmed: attestation,
      decided_at: new Date().toISOString(),
      report_id: currentAnalysis?.report_id || "CDS-2026-0618",
    };
    if (currentAnalysis?.id) {
      try {
        const res = await analysesAPI.recordDecision(currentAnalysis.id, {
          analysis_id: currentAnalysis.id,
          decision_type: decision,
          clinician_notes: clinicianNotes,
          attestation_confirmed: attestation,
        });
        setLastDecision({ ...decisionObj, ...res });
      } catch (e) {
        console.warn("Could not save decision to backend, using local record:", e);
        setLastDecision(decisionObj);
      }
    } else {
      setLastDecision(decisionObj);
    }
    setSavingDecision(false);
    navigate("confirmation");
  };

  const displayDiagnoses = (currentAnalysis.diagnoses || []).map((d: any) => ({
    name: d.name,
    confidence: `${Math.round(d.confidence_percentage)}% confidence`,
    tone:
      d.confidence_label === "high" || d.confidence_percentage >= 70
        ? ("success" as const)
        : ("caution" as const),
    label: d.confidence_label === "high" ? "High confidence" : "Needs review",
    summary: d.summary,
    evidence: Array.isArray(d.evidence) ? d.evidence : [d.evidence],
  }));
  const displayRecommendations = currentAnalysis.recommendations || [];
  const displayInteractions = currentAnalysis.drug_interactions || [];
  const displayRiskFactors = currentAnalysis.risk_factors || [];
  const displayEvidence = currentAnalysis.retrieved_evidence || [];

  const reportId = currentAnalysis?.report_id || "CDS-2026-0618";
  const formattedDate = currentAnalysis?.generated_at
    ? new Date(currentAnalysis.generated_at).toLocaleString()
    : new Date().toLocaleString();

  const content = (
    <main className={`page report-page ${print ? "report-page--print" : ""}`}>
      <PageHeader
        eyebrow={
          print
            ? "Read-only clinical document"
            : `Analysis complete · ${reportId} · ${formattedDate}`
        }
        title="Clinical decision support report"
        description="AWS Bedrock differential diagnoses, recommended next steps, and risk factors synthesized for physician review."
        actions={
          !print && (
            <>
              <Button variant="secondary" onClick={() => navigate("print-report")}>
                Print view
              </Button>
              <Status tone="caution">Clinician review required</Status>
            </>
          )
        }
      />
      {print && (
        <div className="print-meta">
          <span>{patient.full_name}</span>
          <code>{patient.id}</code>
          <span>Report {reportId} · {formattedDate}</span>
        </div>
      )}
      <div className="report-layout">
        <div className="report-main">
          <section className="report-section">
            <div className="section-title">
              <div>
                <h2>Ranked differential</h2>
                <p>
                  Generated by AWS Bedrock AI. Confidence reflects fit with available patient evidence.
                </p>
              </div>
            </div>
            <div className="diagnosis-list">
              {displayDiagnoses.map((diagnosis: any, index: number) => (
                <div
                  className={`diagnosis-row ${
                    expanded.includes(index) || print ? "is-expanded" : ""
                  }`}
                  key={diagnosis.name}
                >
                  <button
                    className="diagnosis-toggle"
                    onClick={() => toggle(index)}
                    onKeyDown={(event) => handleRowKey(event, index)}
                    aria-expanded={expanded.includes(index) || print}
                    aria-controls={`diagnosis-${index}`}
                  >
                    <span className="rank">0{index + 1}</span>
                    <span className="diagnosis-name">
                      <strong>{diagnosis.name}</strong>
                      <small>{diagnosis.summary}</small>
                    </span>
                    <span className="confidence">
                      <strong>{diagnosis.confidence}</strong>
                      <Status tone={diagnosis.tone}>{diagnosis.label}</Status>
                    </span>
                    {!print && (
                      <span className="expand-label">
                        {expanded.includes(index) ? "Hide evidence" : "View evidence"}
                      </span>
                    )}
                  </button>
                  {(expanded.includes(index) || print) && (
                    <div className="diagnosis-evidence" id={`diagnosis-${index}`}>
                      <strong>Supporting patient evidence</strong>
                      <ul>
                        {diagnosis.evidence.map((item: string, i: number) => (
                          <li key={i}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
          <section className="report-section recommendation">
            <div className="section-title">
              <div>
                <h2>Recommended next steps</h2>
                <p>Based on current findings and the leading differential.</p>
              </div>
            </div>
            <ol>
              {displayRecommendations.map((rec: any, idx: number) => (
                <li key={idx}>
                  <span>{rec.step_number || idx + 1}</span>
                  <div>
                    <strong>{rec.title}</strong>
                    <p>{rec.description}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
          {displayInteractions.map((interaction: any, idx: number) => (
            <section className="risk-warning" key={idx}>
              <div>
                <Status tone="critical">Drug interaction risk</Status>
                <strong>{interaction.title}</strong>
              </div>
              <p>{interaction.description}</p>
            </section>
          ))}
          <section className="report-section">
            <div className="section-title">
              <div>
                <h2>Patient-specific risk factors</h2>
              </div>
            </div>
            <div className="risk-list">
              {displayRiskFactors.map((factor: string, idx: number) => (
                <span key={idx}>{factor}</span>
              ))}
            </div>
          </section>
          <section className="report-section evidence-trail" id="citations">
            <div className="section-title">
              <div>
                <h2>Retrieved patient evidence (RAG Knowledge Source)</h2>
                <p>
                  Patient-specific records dynamically retrieved via Amazon Bedrock Titan Text Embeddings and pgvector.
                </p>
              </div>
              <Status tone="success">
                {displayEvidence.length} {displayEvidence.length === 1 ? "Chunk Retrieved" : "Chunks Retrieved"}
              </Status>
            </div>
            {displayEvidence.length > 0 ? (
              <div className="retrieved-evidence-grid" style={{ display: "flex", flexDirection: "column", gap: "1rem", marginTop: "1rem" }}>
                {displayEvidence.map((ev: any, idx: number) => {
                  const simPct = Math.round((ev.similarity || 0) * 100);
                  const sourceTitle = ev.metadata?.source_title || ev.metadata?.filename || ev.source_type.replace("_", " ").toUpperCase();
                  return (
                    <div
                      key={ev.chunk_id || idx}
                      className="evidence-card"
                      style={{
                        padding: "1rem",
                        borderRadius: "8px",
                        border: "1px solid var(--border, #e2e8f0)",
                        background: "var(--surface-subtle, #f8fafc)",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                          <span style={{ fontWeight: 600, fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "#0284c7" }}>
                            [Evidence #{idx + 1}] {sourceTitle}
                          </span>
                          {ev.source_id && (
                            <code style={{ fontSize: "0.75rem", background: "#e0f2fe", color: "#0369a1", padding: "0.15rem 0.4rem", borderRadius: "4px" }}>
                              Ref: {ev.source_id}
                            </code>
                          )}
                        </div>
                        <Status tone={simPct >= 75 ? "success" : "caution"}>
                          {simPct}% match
                        </Status>
                      </div>
                      <p style={{ margin: "0.25rem 0", fontSize: "0.9rem", lineHeight: "1.4", color: "var(--text, #1e293b)" }}>
                        {ev.content}
                      </p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="report-disclaimer">
                No prior patient record chunks met the vector similarity threshold for this query. The synthesis relied exclusively on current clinical encounter presentation.
              </p>
            )}
            <div style={{ marginTop: "1.5rem" }}>
              <h3 style={{ fontSize: "1rem", fontWeight: 600, marginBottom: "0.5rem" }}>Patient chart timeline context</h3>
              <Timeline compact patientId={patient.id} />
            </div>
          </section>
          <section className="report-section explanation">
            <h2>Explanation for the patient</h2>
            <p>
              {currentAnalysis.patient_explanation ||
                "A patient explanation was not returned by AWS Bedrock. Your clinician should review the findings and explain the plan before treatment."}
            </p>
          </section>
        </div>
        {!print && (
          <aside className="decision-panel">
            <div className="decision-panel__heading">
              <span>Required step</span>
              <h2>Record your decision</h2>
              <p>The recommendation will not enter the patient record until you complete this review.</p>
            </div>
            <div className="decision-options">
              {[
                ["approve", "Approve recommendation", "Accept the proposed next steps."],
                ["modify", "Modify recommendation", "Record a revised clinical plan."],
                ["reject", "Reject recommendation", "Do not use this recommendation."],
              ].map(([value, label, hint]) => (
                <label className={decision === value ? "is-selected" : ""} key={value}>
                  <input
                    type="radio"
                    name="decision"
                    value={value}
                    checked={decision === value}
                    onChange={() => setDecision(value)}
                  />
                  <span>
                    <strong>{label}</strong>
                    <small>{hint}</small>
                  </span>
                </label>
              ))}
            </div>
            <TextArea
              label="Clinical notes"
              placeholder="Document your rationale, modifications, or follow-up plan"
              value={clinicianNotes}
              onChange={(e) => setClinicianNotes(e.target.value)}
            />
            <div className="attestation">
              <input
                id="attest"
                type="checkbox"
                checked={attestation}
                onChange={(e) => setAttestation(e.target.checked)}
              />
              <label htmlFor="attest">
                I reviewed the supporting evidence, warnings, and patient context.
              </label>
            </div>
            <Button onClick={handleSaveDecision} disabled={savingDecision}>
              {savingDecision ? "Saving decision..." : "Save decision to record"}
            </Button>
            <p className="audit-note">
              Your name, decision, and timestamp will be recorded in the audit trail.
            </p>
          </aside>
        )}
      </div>
      {print && (
        <div className="print-actions">
          <Button variant="secondary" onClick={() => navigate("report")}>
            Return to interactive report
          </Button>
          <Button onClick={() => window.print()}>Print report</Button>
        </div>
      )}
    </main>
  );

  return print ? (
    <div className="print-shell">
      <header>
        <span className="wordmark">
          Clin<span>IQ</span>
        </span>
        <p>Clinical decision support document</p>
      </header>
      {content}
    </div>
  ) : (
    <ClinicalShell view="report" navigate={navigate} currentPatient={patient}>
      {content}
    </ClinicalShell>
  );
}

function Confirmation({
  navigate,
  currentPatient,
  currentAnalysis,
  lastDecision,
}: {
  navigate: (view: View) => void;
  currentPatient: any;
  currentAnalysis: any;
  lastDecision: any;
}) {
  const patient = currentPatient || {
    id: "CLQ-10482",
    full_name: "Sunita Jadhav",
    age: 58,
  };
  const user = getCurrentUser();
  const decisionLabel =
    lastDecision?.decision_type === "approve"
      ? "Recommendation approved"
      : lastDecision?.decision_type === "modify"
      ? "Recommendation modified"
      : lastDecision?.decision_type === "reject"
      ? "Recommendation rejected"
      : "Recommendation approved";

  const decisionTimestamp = lastDecision?.decided_at
    ? new Date(lastDecision.decided_at).toLocaleString()
    : new Date().toLocaleString();

  return (
    <ClinicalShell view="report" navigate={navigate} currentPatient={patient}>
      <main className="confirmation-page">
        <div className="confirmation-symbol" aria-hidden="true">✓</div>
        <Status tone="success">Saved to patient record</Status>
        <h1>Clinical decision recorded</h1>
        <p>Your approval and notes are now part of {patient.full_name}’s clinical record.</p>
        <dl className="confirmation-details">
          <div><dt>Decision</dt><dd>{decisionLabel}</dd></div>
          <div><dt>Saved by</dt><dd>{user?.full_name || "Dr. Priya Deshmukh"} · {user?.department || "Cardiology"}</dd></div>
          <div><dt>Timestamp</dt><dd>{decisionTimestamp}</dd></div>
          <div><dt>Report ID</dt><dd>{currentAnalysis?.report_id || lastDecision?.report_id || "CDS-2026-0618"}</dd></div>
          <div><dt>Record includes</dt><dd>AWS Bedrock AI analysis, evidence citations, warnings, and clinician notes</dd></div>
          {lastDecision?.clinician_notes && (
            <div><dt>Physician Notes</dt><dd>{lastDecision.clinician_notes}</dd></div>
          )}
        </dl>
        <div>
          <Button onClick={() => navigate("patient-chart")}>Return to updated patient chart</Button>
          <Button variant="secondary" onClick={() => navigate("print-report")}>Open saved report</Button>
        </div>
      </main>
    </ClinicalShell>
  );
}

function AssistantDashboard({ navigate, setCurrentPatient }: { navigate: (view: View) => void; setCurrentPatient: (p: any) => void }) {
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const user = getCurrentUser();

  useEffect(() => {
    patientsAPI.search("")
      .then(data => setPatients(data as any[]))
      .catch(err => console.error("Failed to load patients:", err))
      .finally(() => setLoading(false));
  }, []);

  const handlePatientClick = (patient: any) => {
    setCurrentPatient(patient);
    navigate("patient-chart");
  };

  return (
    <ClinicalShell view="assistant-dashboard" navigate={navigate} role="Assistant">
      <main className="page">
        <PageHeader eyebrow="Clinical intake workspace" title={"Good morning, " + (user?.full_name || "Assistant")} description="Register new patients and prepare records for the care team." actions={<Button onClick={() => navigate("intake")}>Register a new patient</Button>} />
        <div className="assistant-actions">
          <button onClick={() => navigate("intake")}><strong>Register a new patient</strong><span>Create a patient record and assign a doctor.</span><em>Start intake →</em></button>
          <button onClick={() => navigate("schedule-appointment")}><strong>Schedule appointment</strong><span>Book appointments for patients with doctors.</span><em>Schedule now →</em></button>
          <button onClick={() => navigate("uploads")}><strong>Upload patient documents</strong><span>Attach labs, imaging, or external reports by patient ID.</span><em>Add documents →</em></button>
          <button onClick={() => navigate("patient-search")}><strong>Find an existing patient</strong><span>Open a read-only chart to confirm details.</span><em>Search patients →</em></button>
        </div>
        <section className="data-section">
          <div className="section-title">
            <div><h2>Recent patients</h2><p>{patients.length} patient(s) in the system</p></div>
            <Button variant="secondary" onClick={() => navigate("patient-search")}>View all patients</Button>
          </div>
          <div className="data-table search-results">
            <div className="data-row data-row--head"><span>Patient</span><span>Patient ID</span><span>MRN</span><span>Date of birth</span><span>Last activity</span><span /></div>
            {loading ? (
              <div className="empty-state"><strong>Loading patients...</strong></div>
            ) : patients.length === 0 ? (
              <div className="empty-state"><strong>No patients found</strong><p>Register a new patient to get started</p></div>
            ) : patients.slice(0, 10).map((patient: any) => (
              <button className="data-row" key={patient.id} onClick={() => handlePatientClick(patient)}>
                <span data-label="Patient"><strong>{patient.full_name}</strong><small>{patient.gender} · {patient.age} years</small></span>
                <span data-label="Patient ID" className="mono">{patient.id}</span>
                <span data-label="MRN" className="mono">{patient.mrn}</span>
                <span data-label="Date of birth">{patient.date_of_birth}</span>
                <span data-label="Last activity">{patient.last_visit || 'No visits'}</span>
                <span className="row-action">View chart</span>
              </button>
            ))}
          </div>
        </section>
      </main>
    </ClinicalShell>
  );
}

function Intake({ navigate }: { navigate: (view: View) => void }) {
  const [registered, setRegistered] = useState(false);
  const [newPatient, setNewPatient] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [doctors, setDoctors] = useState<any[]>([]);
  const [form, setForm] = useState({
    full_name: "", date_of_birth: "", gender: "Female", contact_number: "",
    mrn: "", reason_for_visit: "", medical_history: "", allergies: "",
    current_medications: "", past_treatments: "", assigned_doctor_id: ""
  });

  useEffect(() => {
    patientsAPI.getDoctors()
      .then((data: any) => setDoctors(data))
      .catch(() => {});
  }, []);

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const payload: any = { ...form };
      if (payload.assigned_doctor_id) payload.assigned_doctor_id = parseInt(payload.assigned_doctor_id);
      else delete payload.assigned_doctor_id;
      const patient = await patientsAPI.create(payload);
      setNewPatient(patient);
      setRegistered(true);
    } catch (err: any) {
      setError(err.message || "Failed to register patient");
    } finally {
      setSubmitting(false);
    }
  };

  if (registered) return (
    <ClinicalShell view="intake" navigate={navigate} role="Assistant">
      <main className="confirmation-page">
        <Status tone="success">Patient registered</Status>
        <h1>Patient ID created</h1>
        <p>Use this identifier for all documents and future visits.</p>
        <div className="generated-id"><span>Patient ID</span><strong>{newPatient?.id || "--"}</strong><small>MRN: {newPatient?.mrn || "--"}</small></div>
        <div><Button onClick={() => navigate("uploads")}>Upload patient documents</Button><Button variant="secondary" onClick={() => navigate("assistant-dashboard")}>Return to workspace</Button></div>
      </main>
    </ClinicalShell>
  );
  return (
    <ClinicalShell view="intake" navigate={navigate} role="Assistant">
      <main className="page page--form">
        <PageHeader eyebrow="Patient intake" title="Register a new patient" description="Create the patient record before attaching documents or beginning a clinical visit." />
        <form className="clinical-form" onSubmit={handleSubmit}>
          {error && <div className="form-error" role="alert"><strong>{error}</strong></div>}
          <section>
            <div className="form-section-heading"><span>1</span><div><h2>Patient details</h2><p>Enter details exactly as they appear in the hospital record.</p></div></div>
            <div className="form-grid form-grid--three">
              <label className="field"><span className="field__label">Full legal name <span aria-hidden="true"> *</span></span><input required value={form.full_name} onChange={set("full_name")} /></label>
              <label className="field"><span className="field__label">Date of birth <span aria-hidden="true"> *</span></span><input type="date" required value={form.date_of_birth} onChange={set("date_of_birth")} /></label>
              <label className="field"><span className="field__label">Gender</span><select value={form.gender} onChange={set("gender")}><option>Female</option><option>Male</option><option>Non-binary</option><option>Not specified</option></select></label>
              <label className="field"><span className="field__label">Contact number</span><input type="tel" value={form.contact_number} onChange={set("contact_number")} /></label>
              <label className="field"><span className="field__label">MRN <span aria-hidden="true"> *</span></span><input required value={form.mrn} onChange={set("mrn")} placeholder="e.g. MRN-123456" /></label>
              <label className="field"><span className="field__label">Reason for visit</span><input value={form.reason_for_visit} onChange={set("reason_for_visit")} /></label>
            </div>
          </section>
          <section>
            <div className="form-section-heading"><span>2</span><div><h2>Clinical history</h2><p>Add known information. Clinicians can review and update this later.</p></div></div>
            <div className="form-grid">
              <label className="field"><span className="field__label">Medical history and conditions</span><textarea rows={4} value={form.medical_history} onChange={set("medical_history")} /></label>
              <label className="field"><span className="field__label">Allergies and reactions</span><textarea rows={4} value={form.allergies} onChange={set("allergies")} /></label>
              <label className="field"><span className="field__label">Current medications</span><textarea rows={4} value={form.current_medications} onChange={set("current_medications")} /></label>
              <label className="field"><span className="field__label">Past treatments</span><textarea rows={4} value={form.past_treatments} onChange={set("past_treatments")} /></label>
            </div>
          </section>
          <section>
            <div className="form-section-heading"><span>3</span><div><h2>Care assignment</h2><p>Route the patient to the appropriate care team.</p></div></div>
            <label className="field"><span className="field__label">Assigned doctor</span>
              <select value={form.assigned_doctor_id} onChange={set("assigned_doctor_id")}>
                <option value="">Select a doctor</option>
                {doctors.map((d: any) => <option key={d.id} value={d.id}>{d.full_name} — {d.department || "General"}</option>)}
              </select>
            </label>
          </section>
          <div className="form-actions"><p><strong>Patient identity check</strong><span>Confirm the name, date of birth, and MRN before creating the record.</span></p><div><Button variant="quiet" onClick={() => navigate("assistant-dashboard")}>Cancel</Button><Button type="submit" disabled={submitting}>{submitting ? "Registering..." : "Register patient"}</Button></div></div>
        </form>
      </main>
    </ClinicalShell>
  );
}

function Uploads({ navigate }: { navigate: (view: View) => void }) {
  const [patientIdInput, setPatientIdInput] = useState("");
  const [verifiedPatient, setVerifiedPatient] = useState<any>(null);
  const [verifyError, setVerifyError] = useState("");
  const [documents, setDocuments] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");

  const handleVerify = async () => {
    setVerifyError("");
    setUploadError("");
    setUploadSuccess("");
    try {
      const p = await patientsAPI.getById(patientIdInput.trim());
      setVerifiedPatient(p);
      const docs = await documentsAPI.getByPatient(p.id);
      setDocuments(docs as any[]);
    } catch {
      setVerifyError("Patient not found. Check the ID or MRN.");
      setVerifiedPatient(null);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!verifiedPatient || !e.target.files?.length) return;
    setUploading(true);
    setUploadError("");
    setUploadSuccess("");
    try {
      for (const file of Array.from(e.target.files)) {
        await documentsAPI.upload(verifiedPatient.id, "general", file);
      }
      setUploadSuccess("Documents uploaded securely to AWS S3!");
      const docs = await documentsAPI.getByPatient(verifiedPatient.id);
      setDocuments(docs as any[]);
    } catch (err: any) {
      console.error("Upload failed:", err);
      setUploadError(err.message || "Failed to upload document to AWS S3.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <ClinicalShell view="uploads" navigate={navigate} role="Assistant">
      <main className="page">
        <PageHeader title="Upload patient documents" description="Attach files to the correct patient record. Files are stored securely with AWS S3 AES-256 encryption." />
        <section className="patient-lookup" aria-label="Patient record lookup">
          <label className="field">
            <span className="field__label">Patient ID or MRN</span>
            <input value={patientIdInput} onChange={e => setPatientIdInput(e.target.value)} placeholder="e.g. CLQ-10482" />
          </label>
          <Button onClick={handleVerify}>Verify patient</Button>
          {verifiedPatient && <Status tone="success">Record verified: {verifiedPatient.full_name}</Status>}
          {verifyError && <span className="field__error">{verifyError}</span>}
        </section>
        {verifiedPatient && (
          <div className="upload-layout">
            <section className="upload-zone">
              <span>Patient ID verified</span><strong>{verifiedPatient.id} · {verifiedPatient.full_name}</strong>
              <label className="file-control"><input type="file" multiple onChange={handleUpload} /><span>{uploading ? "Uploading to AWS S3..." : "Choose files to upload"}</span></label>
              {uploadSuccess && <div style={{ color: "var(--color-success, #10b981)", marginTop: "8px", fontWeight: 500 }}>{uploadSuccess}</div>}
              {uploadError && <div style={{ color: "var(--color-critical, #ef4444)", marginTop: "8px" }}>{uploadError}</div>}
              <p>Lab results, MRI, CT, X-ray, prescriptions, and external reports · AWS S3 encrypted</p>
            </section>
            <section className="data-section">
              <div className="section-title"><div><h2>Uploaded files</h2><p>{documents.length} documents attached to this patient</p></div></div>
              <div className="file-list">
                {documents.length === 0 ? (
                  <div className="empty-state"><strong>No documents yet</strong></div>
                ) : documents.map((doc: any) => (
                  <div key={doc.id}>
                    <div>
                      <strong>{doc.filename || doc.file_name}</strong>
                      <span>{doc.category}</span>
                    </div>
                    <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                    <Button variant="quiet" onClick={() => window.open(doc.file_url, "_blank")}>View</Button>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </main>
    </ClinicalShell>
  );
}

function ScheduleAppointment({ navigate }: { navigate: (view: View) => void }) {
  const [patients, setPatients] = useState<any[]>([]);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [dataError, setDataError] = useState("");
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    patient_id: "",
    doctor_id: "",
    appointment_date: "",
    appointment_time: "",
    reason: ""
  });

  useEffect(() => {
    const loadData = async () => {
      setDataLoading(true);
      try {
        const [patientsData, doctorsData] = await Promise.all([
          patientsAPI.search(""),
          patientsAPI.getDoctors()
        ]);
        setPatients(patientsData as any[]);
        setDoctors(doctorsData as any[]);
      } catch (err: any) {
        setDataError(err.message || "Failed to load data. Please ensure you are logged in and the backend is running.");
        console.error("Failed to load data:", err);
      } finally {
        setDataLoading(false);
      }
    };
    loadData();
  }, []);

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(f => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const appointmentDateTime = `${form.appointment_date}T${form.appointment_time}:00`;
      
      await appointmentsAPI.createAppointment({
        patient_id: form.patient_id,
        doctor_id: parseInt(form.doctor_id),
        appointment_time: appointmentDateTime,
        reason: form.reason
      });

      setSuccess(true);
    } catch (err: any) {
      setError(err.message || "Failed to schedule appointment");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <ClinicalShell view="schedule-appointment" navigate={navigate} role="Assistant">
        <main className="confirmation-page">
          <Status tone="success">Appointment scheduled</Status>
          <h1>Appointment confirmed</h1>
          <p>The appointment has been added to the doctor&apos;s schedule.</p>
          <div>
            <Button onClick={() => navigate("assistant-dashboard")}>Return to workspace</Button>
            <Button variant="secondary" onClick={() => { setSuccess(false); setForm({ patient_id: "", doctor_id: "", appointment_date: "", appointment_time: "", reason: "" }); }}>Schedule another</Button>
          </div>
        </main>
      </ClinicalShell>
    );
  }

  return (
    <ClinicalShell view="schedule-appointment" navigate={navigate} role="Assistant">
      <main className="page page--form">
        <PageHeader
          eyebrow="Appointment scheduling"
          title="Schedule appointment"
          description="Book a patient appointment with a doctor."
        />
        {dataError && (
          <div className="form-error" role="alert">
            <strong>Unable to load scheduling data</strong>
            <span>{dataError}</span>
            <Button variant="secondary" onClick={() => navigate("assistant-dashboard")}>Return to workspace</Button>
          </div>
        )}
        {dataLoading && (
          <div style={{ textAlign: "center", padding: "40px" }}>
            <div className="processing-mark" aria-label="Loading"><span /></div>
            <p>Loading patients and doctors...</p>
          </div>
        )}
        {!dataLoading && !dataError && (
          <form className="clinical-form" onSubmit={handleSubmit}>
            {error && <div className="form-error" role="alert"><strong>{error}</strong></div>}
          <section>
            <div className="form-section-heading">
              <span>1</span>
              <div><h2>Patient selection</h2><p>Select the patient for this appointment.</p></div>
            </div>
            <label className="field">
              <span className="field__label">Patient <span aria-hidden="true"> *</span></span>
              <select required value={form.patient_id} onChange={set("patient_id")}>
                <option value="">Select a patient</option>
                {patients.map((p: any) => (
                  <option key={p.id} value={p.id}>{p.full_name} - {p.id}</option>
                ))}
              </select>
            </label>
          </section>
          <section>
            <div className="form-section-heading">
              <span>2</span>
              <div><h2>Doctor and schedule</h2><p>Choose doctor, date, and time.</p></div>
            </div>
            <div className="form-grid">
              <label className="field">
                <span className="field__label">Doctor <span aria-hidden="true"> *</span></span>
                <select required value={form.doctor_id} onChange={set("doctor_id")}>
                  <option value="">Select a doctor</option>
                  {doctors.map((d: any) => (
                    <option key={d.id} value={d.id}>{d.full_name} — {d.department || "General"}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span className="field__label">Appointment date <span aria-hidden="true"> *</span></span>
                <input type="date" required value={form.appointment_date} onChange={set("appointment_date")} />
              </label>
              <label className="field">
                <span className="field__label">Appointment time <span aria-hidden="true"> *</span></span>
                <input type="time" required value={form.appointment_time} onChange={set("appointment_time")} />
              </label>
            </div>
          </section>
          <section>
            <div className="form-section-heading">
              <span>3</span>
              <div><h2>Appointment details</h2><p>Enter the reason for visit.</p></div>
            </div>
            <label className="field">
              <span className="field__label">Reason for visit <span aria-hidden="true"> *</span></span>
              <textarea rows={4} required value={form.reason} onChange={set("reason")} placeholder="Enter chief complaint or reason for appointment" />
            </label>
          </section>
          <div className="form-actions">
            <p><strong>Confirm appointment details</strong><span>Verify patient, doctor, date, and time before scheduling.</span></p>
            <div>
              <Button variant="quiet" onClick={() => navigate("assistant-dashboard")}>Cancel</Button>
              <Button type="submit" disabled={loading}>{loading ? "Scheduling..." : "Schedule appointment"}</Button>
            </div>
          </div>
        </form>
        )}
      </main>
    </ClinicalShell>
  );
}

function Compare({ navigate }: { navigate: (view: View) => void }) {
  const reports = [
    { date: "18 June 2025", outcome: "Awaiting decision", diagnosis: "Stable angina", confidence: "78%", plan: "Serial troponin, BNP, chest X-ray; review antianginal therapy." },
    { date: "18 November 2024", outcome: "Approved", diagnosis: "Chronic coronary syndrome", confidence: "71%", plan: "Continue aspirin and statin; complete cardiac rehabilitation." },
  ];
  return (
    <ClinicalShell view="patient-chart" navigate={navigate} patientOpen>
      <main className="page">
        <PageHeader eyebrow="Patient chart" title="Compare previous reports" description="Review how clinical evidence, confidence, and recorded decisions changed over time." actions={<Button variant="secondary" onClick={() => navigate("patient-chart")}>Return to chart</Button>} />
        <div className="compare-toolbar"><span>Comparing 2 reports</span><SelectField label="Newer report"><option>18 June 2025</option></SelectField><SelectField label="Earlier report"><option>18 November 2024</option></SelectField></div>
        <div className="comparison">
          {reports.map((report, index) => <section key={report.date}><div className="comparison__header"><span>{index === 0 ? "Current report" : "Previous report"}</span><h2>{report.date}</h2><Status tone={index === 0 ? "caution" : "success"}>{report.outcome}</Status></div><dl><div><dt>Leading diagnosis</dt><dd><strong>{report.diagnosis}</strong><span>{report.confidence} confidence</span></dd></div><div><dt>Recommended plan</dt><dd>{report.plan}</dd></div><div><dt>Patient factors</dt><dd>Coronary artery disease · Hypertension · Hyperlipidemia</dd></div><div><dt>Clinician outcome</dt><dd>{index === 0 ? "Not yet recorded" : "Approved by Dr. Maya Patel with no modifications"}</dd></div></dl><Button variant="quiet" onClick={() => navigate(index === 0 ? "report" : "print-report")}>Open full report</Button></section>)}
        </div>
      </main>
    </ClinicalShell>
  );
}

function AdminShell({ view, navigate, children }: { view: View; navigate: (view: View) => void; children: ReactNode }) {
  return (
    <div className="admin-shell theme-admin">
      <header className="admin-topbar"><button className="wordmark" onClick={() => navigate("admin-home")}>Clin<span>IQ</span><em>Admin</em></button><div><span>Northlake Medical Center</span><button>Alex Morgan <span aria-hidden="true">⌄</span></button></div></header>
      <nav className="admin-nav" aria-label="Admin console">
        {[["admin-home", "System overview"], ["admin-users", "User management"], ["admin-data", "Datasets & knowledge"], ["admin-monitoring", "System monitoring"]].map(([target, label]) => <button className={view === target ? "is-active" : ""} onClick={() => navigate(target as View)} key={target}>{label}</button>)}
      </nav>
      {children}
    </div>
  );
}

function AdminPage({ view, navigate }: { view: View; navigate: (view: View) => void }) {
  const [userPanel, setUserPanel] = useState<"add" | "edit" | null>(null);
  const content: Record<string, { title: string; description: string }> = {
    "admin-home": { title: "System overview", description: "Operational status across the ClinIQ environment." },
    "admin-users": { title: "User management", description: "Manage clinical access, roles, departments, and account status." },
    "admin-data": { title: "Datasets & knowledge base", description: "Review connected clinical sources, versions, and update status." },
    "admin-monitoring": { title: "System monitoring", description: "Inspect recent system activity and service performance." },
  };
  return (
    <AdminShell view={view} navigate={navigate}>
      <main className="page admin-page">
        <PageHeader title={content[view].title} description={content[view].description} actions={view === "admin-users" ? <Button onClick={() => setUserPanel("add")}>Add user</Button> : undefined} />
        {view === "admin-home" && <AdminHome navigate={navigate} />}
        {view === "admin-users" && <AdminUsers userPanel={userPanel} setUserPanel={setUserPanel} />}
        {view === "admin-data" && <AdminData />}
        {view === "admin-monitoring" && <AdminMonitoring />}
      </main>
    </AdminShell>
  );
}

function AdminHome({ navigate }: { navigate: (view: View) => void }) {
  return <><div className="system-status"><div><Status tone="success">All systems operational</Status><strong>Last health check: 09:24</strong></div><p>No active incidents or degraded services.</p></div><div className="admin-metrics"><div><span>Active users</span><strong>146</strong><small>112 doctors · 34 assistants</small></div><div><span>Analyses today</span><strong>382</strong><small>Median completion: 24 sec</small></div><div><span>Knowledge sources</span><strong>18</strong><small>17 current · 1 update pending</small></div><div><span>Service availability</span><strong>99.98%</strong><small>Past 30 days</small></div></div><section className="admin-links"><button onClick={() => navigate("admin-users")}><strong>User management</strong><span>Manage clinical accounts, roles, and access status.</span><em>Open user management →</em></button><button onClick={() => navigate("admin-data")}><strong>Datasets & knowledge base</strong><span>Review sources, update versions, and validation status.</span><em>Open knowledge sources →</em></button><button onClick={() => navigate("admin-monitoring")}><strong>System monitoring</strong><span>Inspect service activity, latency, and recent events.</span><em>Open monitoring →</em></button></section></>;
}

function AdminUsers({ userPanel, setUserPanel }: { userPanel: "add" | "edit" | null; setUserPanel: (value: "add" | "edit" | null) => void }) {
  const [users, setUsers] = useState<any[]>([]);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const adding = userPanel === "add";

  useEffect(() => {
    adminAPI.getUsers()
      .then(data => setUsers(data as any[]))
      .catch(err => console.error("Failed to load users:", err));
  }, []);

  const handleEdit = (user: any) => { setSelectedUser(user); setUserPanel("edit"); };

  return (
    <div className="admin-content-layout">
      <section className="data-section">
        <div className="admin-filter">
          <input aria-label="Search users" placeholder="Search name or email" />
          <select aria-label="Filter by role"><option>All roles</option><option>Doctor</option><option>Assistant</option></select>
          <select aria-label="Filter by status"><option>All statuses</option><option>Active</option><option>Deactivated</option></select>
        </div>
        <div className="data-table users-table">
          <div className="data-row data-row--head"><span>User</span><span>Role</span><span>Department</span><span>Email</span><span>Status</span><span /></div>
          {users.length === 0 ? (
            <div className="empty-state"><strong>Loading users...</strong></div>
          ) : users.map((user: any) => (
            <button className="data-row" key={user.id} onClick={() => handleEdit(user)}>
              <span data-label="User"><strong>{user.full_name}</strong></span>
              <span data-label="Role">{user.role}</span>
              <span data-label="Department">{user.department || "--"}</span>
              <span data-label="Email">{user.email}</span>
              <span data-label="Status"><Status tone={user.status === "active" ? "success" : "neutral"}>{user.status}</Status></span>
              <span className="row-action">Edit</span>
            </button>
          ))}
        </div>
      </section>
      {userPanel && (
        <aside className="edit-panel">
          <div><h2>{adding ? "Add user" : "Edit user"}</h2><Button variant="quiet" onClick={() => setUserPanel(null)}>Close</Button></div>
          <Field label="Full name" defaultValue={adding ? "" : selectedUser?.full_name} required />
          <Field label="Email" type="email" defaultValue={adding ? "" : selectedUser?.email} required />
          <SelectField label="Role"><option>Doctor</option><option>Assistant</option></SelectField>
          <SelectField label="Department"><option>Cardiology</option><option>Internal medicine</option><option>Radiology</option></SelectField>
          <SelectField label="Account status"><option>Active</option><option>Deactivated</option></SelectField>
          <Button onClick={() => setUserPanel(null)}>{adding ? "Add user account" : "Save user changes"}</Button>
        </aside>
      )}
    </div>
  );
}

function AdminData() {
  const sources = [["ACC/AHA Clinical Guidelines", "Guideline library", "2025.06", "Current", "18 Jun, 06:00"], ["Northlake Formulary", "Local medication data", "v42.8", "Current", "18 Jun, 04:20"], ["DrugBank Clinical", "Drug interaction data", "2025-Q2", "Current", "16 Jun, 22:10"], ["NICE Guidance", "Guideline library", "2025.05", "Update pending", "01 Jun, 02:00"]];
  return <section className="data-section"><div className="section-title"><div><h2>Connected sources</h2><p>18 total knowledge sources · Last validation completed today at 06:12</p></div><Button variant="secondary">Validate all sources</Button></div><div className="data-table dataset-table"><div className="data-row data-row--head"><span>Source</span><span>Type</span><span>Version</span><span>Status</span><span>Last synchronized</span><span /></div>{sources.map((source) => <button className="data-row" key={source[0]}><span data-label="Source"><strong>{source[0]}</strong></span><span data-label="Type">{source[1]}</span><span data-label="Version" className="mono">{source[2]}</span><span data-label="Status"><Status tone={source[3] === "Current" ? "success" : "caution"}>{source[3]}</Status></span><span data-label="Last synchronized">{source[4]}</span><span className="row-action">View details</span></button>)}</div></section>;
}

function AdminMonitoring() {
  return <><div className="admin-metrics monitoring"><div><span>Requests, past hour</span><strong>1,284</strong><small>21.4 average per minute</small></div><div><span>Median response time</span><strong>312 ms</strong><small>Within 500 ms target</small></div><div><span>Analysis completion</span><strong>24 sec</strong><small>Median, past hour</small></div><div><span>Error rate</span><strong>0.06%</strong><small>3 recoverable errors</small></div></div><section className="data-section"><div className="section-title"><div><h2>Recent system activity</h2><p>Operational events from all services</p></div><span>Auto-refresh: 30 seconds</span></div><div className="activity-log"><div className="activity-row activity-row--head"><span>Time</span><span>Service</span><span>Event</span><span>Status</span><span>Duration</span></div>{[["09:24:18", "Clinical analysis", "Analysis CLQ-A20481 completed", "Completed", "22.8 sec"], ["09:23:52", "Knowledge service", "Guideline retrieval completed", "Completed", "418 ms"], ["09:22:06", "Audit service", "Decision record written", "Completed", "92 ms"], ["09:19:41", "Identity service", "Hospital directory synchronized", "Completed", "1.2 sec"]].map((item) => <div className="activity-row" key={item[0]}>{item.map((value, index) => <span data-label={["Time", "Service", "Event", "Status", "Duration"][index]} className={index === 0 || index === 4 ? "mono" : ""} key={value}>{index === 3 ? <Status tone="success">{value}</Status> : value}</span>)}</div>)}</div></section></>;
}

export default function App() {
  const [currentPatient, setCurrentPatient] = useState<any>(null);
  const [currentAnalysis, setCurrentAnalysis] = useState<any>(null);
  const [lastDecision, setLastDecision] = useState<any>(null);

  useEffect(() => {
    if (!currentPatient) {
      patientsAPI.getById("CLQ-10482").then(p => setCurrentPatient(p)).catch(() => {});
    }
  }, []);

  const routes: Record<View, string> = {
    landing: "/",
    "clinical-login": "/clinical/login",
    "doctor-dashboard": "/clinical/doctor/today",
    "assistant-dashboard": "/clinical/assistant/workspace",
    "patient-search": "/clinical/patients/search",
    "patient-chart": "/clinical/patients/CLQ-10482",
    "add-info": "/clinical/patients/CLQ-10482/current-visit",
    processing: "/clinical/patients/CLQ-10482/analysis/processing",
    report: "/clinical/patients/CLQ-10482/report/current",
    confirmation: "/clinical/patients/CLQ-10482/report/saved",
    intake: "/clinical/assistant/patients/new",
    uploads: "/clinical/assistant/documents",
    "schedule-appointment": "/clinical/assistant/schedule",
    compare: "/clinical/patients/CLQ-10482/reports/compare",
    "print-report": "/clinical/patients/CLQ-10482/report/print",
    "admin-login": "/admin/login",
    "admin-home": "/admin",
    "admin-users": "/admin/users",
    "admin-data": "/admin/knowledge",
    "admin-monitoring": "/admin/monitoring",
  };
  const routeViews = Object.fromEntries(Object.entries(routes).map(([key, value]) => [value, key])) as Record<string, View>;
  const viewFromLocation = () => routeViews[window.location.hash.replace(/^#/, "") || "/"] ?? "landing";
  const [view, setView] = useState<View>(viewFromLocation);
  const [role, setRole] = useState<"Doctor" | "Assistant">(
    window.location.hash.includes("/assistant") ? "Assistant" : "Doctor",
  );
  const navigate = (next: View) => {
    if (next === "assistant-dashboard" || next === "intake" || next === "uploads") setRole("Assistant");
    if (next === "doctor-dashboard") setRole("Doctor");
    window.location.hash = routes[next];
    setView(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  useEffect(() => {
    const handleRouteChange = () => {
      const nextView = viewFromLocation();
      if (window.location.hash.includes("/assistant")) setRole("Assistant");
      if (window.location.hash.includes("/doctor")) setRole("Doctor");
      setView(nextView);
    };
    window.addEventListener("hashchange", handleRouteChange);
    return () => window.removeEventListener("hashchange", handleRouteChange);
  }, []);
  if (view === "landing") return <Landing navigate={navigate} />;
  if (view === "clinical-login") return <Login navigate={navigate} />;
  if (view === "admin-login") return <Login admin navigate={navigate} />;
  if (view === "doctor-dashboard") return <DoctorDashboard navigate={navigate} setCurrentPatient={setCurrentPatient} />;
  if (view === "assistant-dashboard") return <AssistantDashboard navigate={navigate} setCurrentPatient={setCurrentPatient} />;
  if (view === "patient-search") return <PatientSearch navigate={navigate} setCurrentPatient={setCurrentPatient} role={role} />;
  if (view === "patient-chart") return <PatientChart navigate={navigate} currentPatient={currentPatient} role={role} />;
  if (view === "add-info") return <AddInfo navigate={navigate} currentPatient={currentPatient} setCurrentAnalysis={setCurrentAnalysis} />;
  if (view === "processing") return <Processing navigate={navigate} currentAnalysis={currentAnalysis} setCurrentAnalysis={setCurrentAnalysis} currentPatient={currentPatient} />;
  if (view === "report") return <Report navigate={navigate} currentPatient={currentPatient} currentAnalysis={currentAnalysis} setLastDecision={setLastDecision} />;
  if (view === "confirmation") return <Confirmation navigate={navigate} currentPatient={currentPatient} currentAnalysis={currentAnalysis} lastDecision={lastDecision} />;
  if (view === "intake") return <Intake navigate={navigate} />;
  if (view === "uploads") return <Uploads navigate={navigate} />;
  if (view === "schedule-appointment") return <ScheduleAppointment navigate={navigate} />;
  if (view === "compare") return <Compare navigate={navigate} currentPatient={currentPatient} />;
  if (view === "print-report") return <Report print navigate={navigate} currentPatient={currentPatient} currentAnalysis={currentAnalysis} setLastDecision={setLastDecision} />;
  return <AdminPage view={view} navigate={navigate} />;
}
