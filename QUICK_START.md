# ClinIQ - Quick Start (5 Minutes)

## The Database Error Fix

**✅ FIXED:** The PostgreSQL error about immutable expressions has been resolved. The schema now uses a view and helper functions instead of a generated column for age calculation.

---

## Fastest Way to Get Running

### 1. Supabase Setup (2 minutes)

1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Save your database password!
3. Go to **SQL Editor** → Paste and run `backend/schema.sql` → ✅
4. **New query** → Paste and run `backend/seed_data.sql` → ✅
5. Go to **Storage** → **New bucket** → Name: `patient-documents` → Public ✅
6. Go to **Settings** → **API** → Copy these:
   ```
   Project URL: https://xxx.supabase.co
   anon key: eyJhbG...
   service_role key: eyJhbG...
   ```

### 2. Backend Setup (2 minutes)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Now edit .env and paste your Supabase credentials

# Start server
uvicorn main:app --reload --port 8000
```

**Test it:** Open http://localhost:8000 - you should see API info!

### 3. Test the API (1 minute)

Open http://localhost:8000/docs

Try the login endpoint:
- Click **POST /auth/login** → **Try it out**
- Email: `maya.patel@northlake.org`
- Password: `clinical-access`
- Click **Execute**

You should get a token! 🎉

---

## What You Have Now

✅ **13 Database Tables** with sample Indian patient data  
✅ **30+ API Endpoints** fully functional  
✅ **Mock AI Analysis** that generates realistic diagnostic reports  
✅ **JWT Authentication** with role-based access control  
✅ **File Upload** to Supabase Storage  
✅ **Complete Documentation** in README.md and SETUP_GUIDE.md

---

## Next Steps

### Option A: Test the Backend API
Use the Swagger docs at http://localhost:8000/docs to explore all endpoints

### Option B: Run the Frontend (Original Mock UI)
The frontend in `frontend/` folder still works with its original mock data:
```bash
cd frontend
pnpm install
pnpm dev
# Open http://localhost:8443
```

### Option C: Integrate Frontend with Backend
Replace the hardcoded mock data in `frontend/src/App.tsx` with API calls from `frontend/src/api.ts`

---

## Common Issues & Solutions

### "ModuleNotFoundError" in Backend
```bash
# Make sure venv is activated - you should see (venv) in prompt
source venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused" to Supabase
- Check your `.env` file has correct credentials
- Verify your Supabase project is active (green in dashboard)

### Backend "Port 8000 already in use"
```bash
# Use a different port
uvicorn main:app --reload --port 8001

# Update frontend/.env to match:
VITE_API_BASE_URL=http://localhost:8001
```

### SQL Script Errors
- Make sure you run `schema.sql` FIRST, then `seed_data.sql`
- Check for any error messages in Supabase SQL Editor output

---

## Test Accounts

All passwords: **`clinical-access`**

**Doctor:**
- maya.patel@northlake.org (Dr. Priya Deshmukh)

**Assistant:**
- jamie.rivera@northlake.org (Aditya Kulkarni)

**Admin:**
- admin@northlake.org (Sneha Patil)

---

## Sample Patients (Marathi Names)

- **Sunita Jadhav** (CLQ-10482) - 57F, Dyspnea
- **Ramesh Bhosale** (CLQ-10479) - 66M, Post-op review
- **Manjusha Pawar** (CLQ-10491) - 53F, Medication follow-up
- **Anand Kale** (CLQ-10496) - 59M, Lab review

---

## Key API Endpoints to Try

### Authentication
```bash
POST /auth/login
POST /auth/logout
```

### Patients
```bash
GET /patients/search?q=Sunita
GET /patients/{patient_id}
POST /patients
GET /patients/{patient_id}/timeline
```

### Clinical Analysis
```bash
POST /analyses          # Request AI analysis
GET /analyses/{id}      # Get results
POST /analyses/{id}/decision  # Record decision
```

### Admin
```bash
GET /admin/users
GET /admin/metrics
GET /admin/knowledge-sources
```

---

## What's Special About This Backend?

1. **Production-Ready** - Proper security, validation, error handling
2. **Mock AI** - Generates realistic diagnoses while you build real AI
3. **Indian Context** - Marathi names, Indian phone numbers
4. **Complete Workflow** - Full clinical decision support cycle
5. **Well-Documented** - Every endpoint documented in Swagger
6. **Easy to Extend** - Add your AI model by replacing `services/mock_analysis.py`

---

## Need More Help?

- **Full Setup Guide:** See `SETUP_GUIDE.md`
- **Deployment Guide:** See `DEPLOYMENT.md`
- **Project Overview:** See `PROJECT_SUMMARY.md`
- **API Docs:** http://localhost:8000/docs (when running)

---

**You're all set! Start with the Supabase setup above, then run the backend.** 🚀

The API will be ready to generate mock clinical analyses, manage patients, and support the full clinical workflow!
