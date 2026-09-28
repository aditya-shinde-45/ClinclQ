# Step-by-Step Frontend Integration

I've created `frontend/src/App-integrated.tsx` with integrated versions of key components. Here's how to complete the full integration:

## ✅ What's Already Integrated in App-integrated.tsx

1. **Login Component** - Real API authentication
2. **Doctor Dashboard** - Loads real appointments
3. **Patient Search** - Real search functionality

## 🔄 How to Complete Integration

### Option 1: Gradual Migration (Recommended)

Slowly replace components in your existing `App.tsx`:

#### Step 1: Update Imports
Add these imports at the top of `frontend/src/App.tsx`:

```typescript
import { authAPI, patientsAPI, appointmentsAPI, analysesAPI, documentsAPI, adminAPI } from "./api";
import { setAuthToken, clearAuthToken, getCurrentUser, setCurrentUser } from "./config";
```

#### Step 2: Add State for Current Patient
After the `view` state, add:

```typescript
const [currentPatient, setCurrentPatient] = useState<any>(null);
const [currentAnalysis, setCurrentAnalysis] = useState<any>(null);
```

#### Step 3: Replace Login Component
Find the `Login` component (around line 520) and replace the form submission with:

```typescript
const handleSubmit = async (event: React.FormEvent) => {
  event.preventDefault();
  setLoading(true);
  setError(false);

  try {
    const response = await authAPI.login(email, password);
    setAuthToken(response.access_token);
    setCurrentUser(response.user);
    
    if (response.user.role === 'admin') {
      navigate('admin-home');
    } else if (response.user.role === 'assistant') {
      navigate('assistant-dashboard');
    } else {
      navigate('doctor-dashboard');
    }
  } catch (err) {
    setError(true);
  } finally {
    setLoading(false);
  }
};
```

#### Step 4: Replace DoctorDashboard Queue
Find `DoctorDashboard` component and replace the hardcoded `queue` array:

```typescript
const [appointments, setAppointments] = useState<any[]>([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  appointmentsAPI.getToday()
    .then(setAppointments)
    .catch(console.error)
    .finally(() => setLoading(false));
}, []);

// In JSX:
{loading ? <div>Loading...</div> : appointments.map((apt) => (
  <div key={apt.id}>
    {/* Format the appointment data */}
  </div>
))}
```

#### Step 5: Replace PatientSearch
Find `PatientSearch` component and add:

```typescript
const [query, setQuery] = useState("");
const [results, setResults] = useState<any[]>([]);
const [loading, setLoading] = useState(false);

const handleSearch = async () => {
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
```

#### Step 6: Replace Patient Data
Find `PatientContext` and `PatientChart` components, replace hardcoded `patient`:

```typescript
const [patient, setPatient] = useState<any>(null);
const patientId = "CLQ-10482"; // or from props/state

useEffect(() => {
  patientsAPI.getById(patientId)
    .then(setPatient)
    .catch(console.error);
}, [patientId]);
```

#### Step 7: Replace Timeline
In `PatientChart`, replace hardcoded `timeline`:

```typescript
const [timeline, setTimeline] = useState<any[]>([]);

useEffect(() => {
  patientsAPI.getTimeline(patientId)
    .then((data) => {
      const formatted = data.map((visit: any) => ({
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

#### Step 8: Integrate Clinical Analysis
In `AddInfo` component, replace navigation with API call:

```typescript
const handleSubmit = async (event: React.FormEvent) => {
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
    
    setCurrentAnalysis(analysis);
    localStorage.setItem('currentAnalysisId', analysis.id.toString());
    navigate("processing");
  } catch (err) {
    alert('Failed to request analysis: ' + (err as Error).message);
  }
};
```

#### Step 9: Processing Component
Add polling logic:

```typescript
useEffect(() => {
  const analysisId = localStorage.getItem('currentAnalysisId');
  if (!analysisId) return;
  
  const checkStatus = async () => {
    try {
      const analysis = await analysesAPI.getById(parseInt(analysisId));
      
      if (analysis.status === 'awaiting_review') {
        setCurrentAnalysis(analysis);
        navigate("report");
      } else if (analysis.status === 'processing') {
        setTimeout(checkStatus, 2000); // Poll every 2 seconds
      }
    } catch (err) {
      console.error(err);
    }
  };
  
  setTimeout(checkStatus, 3000); // Wait 3 seconds then start polling
}, [navigate]);
```

#### Step 10: Report Component
Load real analysis data:

```typescript
const [analysisData, setAnalysisData] = useState<any>(null);

useEffect(() => {
  const analysisId = localStorage.getItem('currentAnalysisId');
  if (analysisId) {
    analysesAPI.getById(parseInt(analysisId))
      .then(setAnalysisData)
      .catch(console.error);
  }
}, []);

// Use real data:
const diagnoses = analysisData?.diagnoses || [];
const recommendations = analysisData?.recommendations || [];
```

#### Step 11: Record Decision
In Report component's decision handler:

```typescript
const handleDecisionSubmit = async () => {
  const analysisId = localStorage.getItem('currentAnalysisId');
  
  try {
    await analysesAPI.recordDecision(parseInt(analysisId!), {
      decision_type: decision,
      clinician_notes: clinicianNotes,
      attestation_confirmed: true
    });
    
    navigate("confirmation");
  } catch (err) {
    alert('Failed to record decision: ' + (err as Error).message);
  }
};
```

---

### Option 2: Use App-integrated.tsx (Quick Start)

1. **Backup your current App.tsx:**
   ```bash
   cp frontend/src/App.tsx frontend/src/App-original.tsx
   ```

2. **Copy the integrated version:**
   ```bash
   cp frontend/src/App-integrated.tsx frontend/src/App.tsx
   ```

3. **Add missing components from App-original.tsx:**
   - Copy all the component definitions you need
   - Merge the routing logic
   - Keep all the CSS and styling as-is

4. **Test each feature:**
   - Login
   - Patient search
   - Dashboard

---

## 🧪 Testing After Integration

### 1. Test Login
```typescript
// Open browser console
// Try login
// Check: localStorage.getItem('auth_token')
// Should see JWT token
```

### 2. Test API Calls
```typescript
// Check Network tab in DevTools
// Should see requests to http://localhost:8000
// Check response status (200 = success)
```

### 3. Test Data Loading
```typescript
// Open patient search
// Search for "Sunita"
// Should see real patient from database
```

---

## 🐛 Common Issues

### Issue: "Network Error"
**Solution:** Backend not running. Start it:
```bash
cd backend
./venv/bin/uvicorn main:app --reload --port 8000
```

### Issue: "401 Unauthorized"
**Solution:** Token not sent. Check:
1. Login first
2. Token stored in localStorage
3. `getAuthHeaders()` called in API client

### Issue: "CORS Error"
**Solution:** Check backend `.env`:
```env
CORS_ORIGINS=["http://localhost:8443"]
```

### Issue: Data doesn't display
**Solution:** Check data transformation:
```typescript
console.log('API response:', data);
// See what format the data is in
// Transform to match UI expectations
```

---

## 📝 Quick Reference

### State Management
```typescript
const [data, setData] = useState<any>(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
```

### API Call Pattern
```typescript
useEffect(() => {
  setLoading(true);
  apiCall()
    .then(setData)
    .catch((err) => setError(err.message))
    .finally(() => setLoading(false));
}, [dependencies]);
```

### Loading UI
```typescript
if (loading) return <LoadingSpinner />;
if (error) return <div>Error: {error}</div>;
if (!data) return null;
```

---

## ✅ Integration Checklist

- [ ] Added API imports
- [ ] Replaced Login with real auth
- [ ] Loaded real appointments in dashboard
- [ ] Implemented patient search
- [ ] Loaded patient details
- [ ] Loaded patient timeline
- [ ] Implemented analysis request
- [ ] Added processing polling
- [ ] Loaded analysis results
- [ ] Implemented decision recording
- [ ] Added loading states
- [ ] Added error handling
- [ ] Tested all features

---

## 🎯 Next Steps

1. Start with Login integration (easiest)
2. Test it works
3. Move to Patient Search
4. Test it works
5. Continue with other components
6. Test end-to-end workflow

**Take it one component at a time!** Don't try to integrate everything at once.

**Need help?** Check the detailed code examples in `FRONTEND_INTEGRATION_GUIDE.md`
