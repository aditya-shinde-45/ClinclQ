# Frontend-Backend Integration Guide

## ✅ Complete Integration Checklist

This document provides the exact changes needed to connect the frontend mock data to the real backend API.

---

## Current State

- ✅ Backend API running with 30+ endpoints
- ✅ API client functions in `frontend/src/api.ts`
- ❌ Frontend still using hardcoded mock data
- ❌ No loading states
- ❌ No error handling

---

## Integration Steps

### Step 1: Add Loading & Error States

Create a new file `frontend/src/hooks/useApi.ts`:

```typescript
import { useState, useEffect } from 'react';

export function useApi<T>(apiCall: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    
    apiCall()
      .then(result => {
        if (mounted) {
          setData(result);
          setError(null);
        }
      })
      .catch(err => {
        if (mounted) {
          setError(err.message || 'An error occurred');
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => { mounted = false; };
  }, deps);

  return { data, loading, error, setData };
}
```

### Step 2: Authentication Integration

**Login Component** - Replace mock login:

```typescript
// Before (mock):
if (password !== "clinical-access") {
  setError(true);
  return;
}
navigate(admin ? "admin-home" : clinicalRole === "assistant" ? "assistant-dashboard" : "doctor-dashboard");

// After (real API):
import { authAPI } from './api';
import { setAuthToken } from './config';

try {
  const response = await authAPI.login(email, password);
  setAuthToken(response.access_token);
  
  // Store user info
  localStorage.setItem('user', JSON.stringify(response.user));
  
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
}
```

### Step 3: Patient Data Integration

**PatientContext Component** - Replace hardcoded patient:

```typescript
// Before:
const patient = {
  name: "Elena Marquez",
  age: 57,
  gender: "Female",
  id: "CLQ-10482",
  mrn: "MRN-883104",
};

// After:
const [patient, setPatient] = useState(null);
const patientId = "CLQ-10482"; // Get from route params

useEffect(() => {
  patientsAPI.getById(patientId)
    .then(setPatient)
    .catch(console.error);
}, [patientId]);

if (!patient) return null; // Or loading spinner
```

### Step 4: Appointments Queue Integration

**DoctorDashboard Component** - Replace hardcoded queue:

```typescript
// Before:
const queue = [
  ["08:30", "Noah Williams", "CLQ-10479", "Post-operative review", "Checked in"],
  // ... more hardcoded data
];

// After:
import { appointmentsAPI } from './api';

const [appointments, setAppointments] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  appointmentsAPI.getToday()
    .then(data => {
      // Transform to match UI format
      const formatted = data.map(apt => [
        new Date(apt.appointment_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        apt.patient_name,
        apt.patient_id,
        apt.reason,
        apt.status
      ]);
      setAppointments(formatted);
    })
    .catch(console.error)
    .finally(() => setLoading(false));
}, []);

// In JSX:
{loading ? <div>Loading...</div> : appointments.map(...)}
```

### Step 5: Patient Search Integration

**PatientSearch Component** - Wire up real search:

```typescript
// Before:
const [searched, setSearched] = useState(true);

// After:
import { patientsAPI } from './api';

const [query, setQuery] = useState("");
const [results, setResults] = useState([]);
const [loading, setLoading] = useState(false);

const handleSearch = async () => {
  if (!query.trim()) return;
  
  setLoading(true);
  try {
    const data = await patientsAPI.search(query);
    setResults(data);
  } catch (err) {
    console.error(err);
  } finally {
    setLoading(false);
  }
};

// In JSX:
<input value={query} onChange={(e) => setQuery(e.target.value)} />
<Button onClick={handleSearch}>Search patients</Button>
{loading ? <div>Searching...</div> : results.map(...)}
```

### Step 6: Timeline Integration

**PatientChart Component** - Replace hardcoded timeline:

```typescript
// Before:
const timeline = [
  {
    date: "Today, 09:12",
    title: "Current visit opened",
    body: "Persistent dyspnea...",
    type: "Clinical note",
  },
  // ... more hardcoded
];

// After:
import { patientsAPI } from './api';

const [timeline, setTimeline] = useState([]);

useEffect(() => {
  patientsAPI.getTimeline(patientId)
    .then(data => {
      // Transform dates for display
      const formatted = data.map(visit => ({
        date: new Date(visit.visit_date).toLocaleString(),
        title: visit.title,
        body: visit.body,
        type: visit.type
      }));
      setTimeline(formatted);
    })
    .catch(console.error);
}, [patientId]);
```

### Step 7: Clinical Analysis Integration

**AddInfo Component** - Request real analysis:

```typescript
// Before:
navigate("processing");

// After:
import { analysesAPI } from './api';

const handleSubmit = async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  
  try {
    const analysis = await analysesAPI.request({
      patient_id: patientId,
      new_symptoms: formData.get('new-symptoms') as string,
      observations: formData.get('current-observations') as string,
      test_results: formData.get('new-test-results') as string,
      clinical_notes: formData.get('additional-clinical-notes') as string
    });
    
    // Store analysis ID for later retrieval
    localStorage.setItem('currentAnalysisId', analysis.id.toString());
    navigate("processing");
  } catch (err) {
    alert('Failed to request analysis: ' + err.message);
  }
};
```

### Step 8: Processing & Results

**Processing Component** - Poll for completion:

```typescript
// After submitting, poll for analysis completion
import { analysesAPI } from './api';

useEffect(() => {
  const analysisId = localStorage.getItem('currentAnalysisId');
  if (!analysisId) return;
  
  const checkStatus = async () => {
    try {
      const analysis = await analysesAPI.getById(parseInt(analysisId));
      
      if (analysis.status === 'awaiting_review') {
        // Store full analysis data
        localStorage.setItem('currentAnalysis', JSON.stringify(analysis));
        navigate("report");
      } else if (analysis.status === 'processing') {
        // Keep polling
        setTimeout(checkStatus, 2000);
      }
    } catch (err) {
      console.error('Failed to check analysis status:', err);
    }
  };
  
  // Start polling after component mounts
  setTimeout(checkStatus, 3000);
}, [navigate]);
```

**Report Component** - Load real analysis:

```typescript
// Before:
const diagnoses = [
  {
    name: "Stable angina",
    confidence: "78% confidence",
    // ... hardcoded
  }
];

// After:
const [analysisData, setAnalysisData] = useState(null);

useEffect(() => {
  // Try to load from localStorage first (from processing)
  const stored = localStorage.getItem('currentAnalysis');
  if (stored) {
    setAnalysisData(JSON.parse(stored));
    return;
  }
  
  // Otherwise fetch by ID
  const analysisId = localStorage.getItem('currentAnalysisId');
  if (analysisId) {
    analysesAPI.getById(parseInt(analysisId))
      .then(setAnalysisData)
      .catch(console.error);
  }
}, []);

if (!analysisData) return <div>Loading report...</div>;

// Use real data:
const diagnoses = analysisData.diagnoses;
const recommendations = analysisData.recommendations;
const drugInteractions = analysisData.drug_interactions;
```

### Step 9: Clinical Decision Recording

**Report Component** - Record decision:

```typescript
const handleDecisionSubmit = async () => {
  const analysisId = localStorage.getItem('currentAnalysisId');
  
  try {
    await analysesAPI.recordDecision(parseInt(analysisId), {
      decision_type: decision, // 'approve', 'modify', 'reject'
      clinician_notes: clinicianNotes,
      attestation_confirmed: attestationChecked
    });
    
    navigate("confirmation");
  } catch (err) {
    alert('Failed to record decision: ' + err.message);
  }
};
```

### Step 10: Patient Registration (Intake)

**Intake Component** - Create real patient:

```typescript
import { patientsAPI } from './api';

const handleSubmit = async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  
  try {
    const newPatient = await patientsAPI.create({
      full_name: formData.get('full-legal-name') as string,
      date_of_birth: formData.get('date-of-birth') as string,
      gender: formData.get('gender') as string,
      contact_number: formData.get('contact-number') as string,
      mrn: formData.get('ehr-mrn') as string,
      reason_for_visit: formData.get('reason-for-visit') as string,
      medical_history: formData.get('medical-history-and-conditions') as string,
      allergies: formData.get('allergies-and-reactions') as string,
      current_medications: formData.get('current-medications') as string,
      past_treatments: formData.get('past-treatments') as string,
      assigned_doctor_id: 1 // Get from form
    });
    
    // Show generated ID
    setGeneratedPatientId(newPatient.id);
    setRegistered(true);
  } catch (err) {
    alert('Failed to register patient: ' + err.message);
  }
};
```

### Step 11: Document Upload

**Uploads Component** - Real file upload:

```typescript
import { documentsAPI } from './api';

const handleFileUpload = async (event) => {
  const files = event.target.files;
  if (!files) return;
  
  const patientId = "CLQ-10482"; // Get from context
  
  for (const file of files) {
    try {
      await documentsAPI.upload(patientId, 'lab', file);
      // Refresh document list
      refreshDocuments();
    } catch (err) {
      alert(`Failed to upload ${file.name}: ` + err.message);
    }
  }
};

const [documents, setDocuments] = useState([]);

const refreshDocuments = async () => {
  try {
    const docs = await documentsAPI.getByPatient(patientId);
    setDocuments(docs);
  } catch (err) {
    console.error(err);
  }
};

useEffect(() => {
  refreshDocuments();
}, [patientId]);
```

### Step 12: Admin Functions

**AdminUsers Component** - Real user management:

```typescript
import { adminAPI } from './api';

const [users, setUsers] = useState([]);

useEffect(() => {
  adminAPI.getUsers()
    .then(setUsers)
    .catch(console.error);
}, []);

**AdminMetrics Component** - Real metrics:

```typescript
const [metrics, setMetrics] = useState(null);

useEffect(() => {
  adminAPI.getMetrics()
    .then(setMetrics)
    .catch(console.error);
}, []);
```

---

## Common Patterns

### Loading State
```typescript
{loading && <div className="spinner">Loading...</div>}
{error && <div className="error">Error: {error}</div>}
{data && <YourComponent data={data} />}
```

### Error Handling
```typescript
try {
  const result = await apiCall();
  // success
} catch (err) {
  setError(err.message);
  console.error(err);
}
```

### Authentication Guard
```typescript
useEffect(() => {
  const token = getAuthToken();
  if (!token) {
    navigate('clinical-login');
  }
}, []);
```

---

## Testing Integration

1. Start backend: `cd backend && ./venv/bin/uvicorn main:app --reload --port 8000`
2. Ensure `.env` files are configured
3. Test each feature:
   - ✅ Login with real credentials
   - ✅ Search patients
   - ✅ View patient chart
   - ✅ Request analysis
   - ✅ Record decision
   - ✅ Upload documents

---

## Next Steps

1. Replace hardcoded data section by section
2. Add loading spinners
3. Add error messages
4. Test each integrated feature
5. Add authentication guards
6. Handle token expiration
7. Add retry logic for failed requests

This integration will make your frontend fully functional with the real backend API!
