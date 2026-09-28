# Integration Verification Checklist

Use this to verify your frontend-backend integration is working correctly.

## ✅ Pre-Integration Checks

### 1. Backend is Running
```bash
# Test this URL in browser:
http://localhost:8000

# Should see:
{"message": "ClinIQ API", "version": "1.0.0", ...}
```

### 2. API Documentation Works
```bash
# Open in browser:
http://localhost:8000/docs

# Should see:
Swagger UI with all endpoints listed
```

### 3. Database Has Data
```bash
# In Supabase dashboard:
# Go to: Table Editor → users
# Should see: 5 users including maya.patel@northlake.org
```

### 4. Frontend Environment Configured
```bash
# Check: frontend/.env
VITE_API_BASE_URL=http://localhost:8000

# Should match your backend URL
```

---

## 🧪 Integration Tests

### Test 1: Login Authentication

**What to test:**
1. Open http://localhost:8443
2. Click "Sign in" → "Clinical app sign in"
3. Enter credentials:
   - Email: `maya.patel@northlake.org`
   - Password: `clinical-access`
4. Click "Sign in"

**Expected result:**
- ✅ Redirects to doctor dashboard
- ✅ See "Good morning, Dr. Priya Deshmukh" (or similar)
- ✅ localStorage has `auth_token`
- ✅ localStorage has `user` object

**How to check:**
```javascript
// Open browser console (F12)
localStorage.getItem('auth_token')  // Should see JWT token
localStorage.getItem('user')         // Should see user data
```

**If it fails:**
- Check Network tab → /auth/login
- Status should be 200
- Response should have `access_token`
- Check console for errors

---

### Test 2: Patient Search

**What to test:**
1. Go to "Patient search"
2. Enter: `Sunita`
3. Click "Search patients"

**Expected result:**
- ✅ Shows loading state
- ✅ Displays "Sunita Jadhav" in results
- ✅ Shows patient ID: CLQ-10482
- ✅ Shows age, gender, MRN

**How to check:**
```javascript
// In Network tab:
GET /patients/search?q=Sunita
// Status: 200
// Response: Array with patient object
```

**If it fails:**
- Check auth token is being sent
- Check backend is running
- Check Supabase has the patient data

---

### Test 3: Today's Appointments

**What to test:**
1. Go to doctor dashboard
2. Look for "Today's patient queue"

**Expected result:**
- ✅ Shows list of appointments
- ✅ Shows patient names (Ramesh Bhosale, Sunita Jadhav, etc.)
- ✅ Shows appointment times
- ✅ Shows status badges

**How to check:**
```javascript
// In Network tab:
GET /appointments/today
// Status: 200
// Response: Array of appointments
```

---

### Test 4: Patient Chart

**What to test:**
1. Search for "Sunita"
2. Click on patient result
3. Should show patient chart

**Expected result:**
- ✅ Shows patient name: Sunita Jadhav
- ✅ Shows age: 57
- ✅ Shows medical history
- ✅ Shows current medications
- ✅ Shows timeline of visits

**How to check:**
```javascript
// In Network tab:
GET /patients/CLQ-10482
GET /patients/CLQ-10482/timeline
// Both should return 200
```

---

### Test 5: Clinical Analysis Request

**What to test:**
1. From patient chart, click "Add clinical info"
2. Fill in symptoms: "Chest pain on exertion"
3. Fill in observations: "Patient alert, vital signs stable"
4. Click "Request clinical analysis"

**Expected result:**
- ✅ Shows "Processing" screen
- ✅ Wait 3 seconds
- ✅ Automatically navigates to report
- ✅ Shows diagnoses with confidence scores
- ✅ Shows recommendations

**How to check:**
```javascript
// In Network tab:
POST /analyses
// Status: 201
// Response: analysis object with id

// After 3 seconds:
GET /analyses/{id}
// Status: 200
// Response: analysis with diagnoses array
```

---

### Test 6: Record Clinical Decision

**What to test:**
1. On report page, select "Approve recommendation"
2. Enter notes: "Plan approved, follow-up in 2 weeks"
3. Check attestation box
4. Click "Save decision to record"

**Expected result:**
- ✅ Shows success message
- ✅ Navigates to confirmation page
- ✅ Shows decision was recorded

**How to check:**
```javascript
// In Network tab:
POST /analyses/{id}/decision
// Status: 201
// Body: {decision_type: "approve", clinician_notes: "..."}
```

---

### Test 7: Patient Registration (Assistant)

**What to test:**
1. Logout
2. Login as assistant:
   - Email: `jamie.rivera@northlake.org`
   - Password: `clinical-access`
3. Go to "Register a new patient"
4. Fill in patient details
5. Click "Register patient"

**Expected result:**
- ✅ Shows generated patient ID
- ✅ Shows success message
- ✅ New patient appears in search

**How to check:**
```javascript
// In Network tab:
POST /patients
// Status: 201
// Response: new patient object with id
```

---

### Test 8: Document Upload

**What to test:**
1. Go to "Documents"
2. Enter patient ID: CLQ-10482
3. Click "Verify patient"
4. Choose a file (PDF, image, etc.)
5. Click upload

**Expected result:**
- ✅ File uploads successfully
- ✅ Appears in documents list
- ✅ Shows filename and date

**How to check:**
```javascript
// In Network tab:
POST /documents/upload?patient_id=CLQ-10482&category=lab
// Status: 201
// Response: document object with file_url
```

---

### Test 9: Admin Metrics

**What to test:**
1. Logout
2. Login as admin:
   - Email: `admin@northlake.org`
   - Password: `clinical-access`
3. View admin dashboard

**Expected result:**
- ✅ Shows active users count
- ✅ Shows analyses today count
- ✅ Shows knowledge sources count
- ✅ Shows service availability

**How to check:**
```javascript
// In Network tab:
GET /admin/metrics
// Status: 200
// Response: {active_users: 4, analyses_today: 1, ...}
```

---

### Test 10: User Management

**What to test:**
1. In admin console, go to "User management"
2. Should see list of users

**Expected result:**
- ✅ Shows all users
- ✅ Shows roles (doctor, assistant, admin)
- ✅ Shows status (active/deactivated)

**How to check:**
```javascript
// In Network tab:
GET /admin/users
// Status: 200
// Response: Array of user objects
```

---

## 🔍 Debug Checklist

### If Nothing Works:

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy"}
   ```

2. **Check frontend can reach backend:**
   ```javascript
   // In browser console:
   fetch('http://localhost:8000')
     .then(r => r.json())
     .then(console.log)
   ```

3. **Check CORS is configured:**
   ```bash
   # In backend/.env:
   CORS_ORIGINS=["http://localhost:8443"]
   ```

4. **Check authentication:**
   ```javascript
   // After login, in console:
   localStorage.getItem('auth_token')  // Should have token
   ```

5. **Check API calls have auth header:**
   ```javascript
   // In Network tab → Headers
   // Should see: Authorization: Bearer eyJ...
   ```

---

## 📊 Integration Score

Count how many tests pass:

- [ ] Test 1: Login ✅
- [ ] Test 2: Patient Search ✅
- [ ] Test 3: Appointments ✅
- [ ] Test 4: Patient Chart ✅
- [ ] Test 5: Clinical Analysis ✅
- [ ] Test 6: Record Decision ✅
- [ ] Test 7: Patient Registration ✅
- [ ] Test 8: Document Upload ✅
- [ ] Test 9: Admin Metrics ✅
- [ ] Test 10: User Management ✅

**Score: __ / 10**

---

## 🎯 Success Criteria

Your integration is complete when:
- ✅ All 10 tests pass
- ✅ No console errors
- ✅ No network errors
- ✅ Data loads from backend
- ✅ User can complete full workflow

---

## 🐛 Common Issues

### Issue: "Failed to fetch"
- Backend not running
- Wrong API URL in .env
- CORS not configured

### Issue: "401 Unauthorized"
- Not logged in
- Token expired
- Token not in headers

### Issue: "404 Not Found"
- Wrong endpoint URL
- Resource doesn't exist
- Check API docs

### Issue: Data is undefined
- Wrong property name
- Data structure mismatch
- Check API response format

### Issue: "CORS policy" error
- Add frontend URL to backend CORS_ORIGINS
- Restart backend

---

## 📞 Need Help?

1. Check browser console for errors
2. Check Network tab for failed requests
3. Check backend logs for errors
4. Review `FRONTEND_INTEGRATION_GUIDE.md`
5. Review `INTEGRATION_STEPS.md`

---

**Good luck with testing!** 🎉
