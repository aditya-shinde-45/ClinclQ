# ClinIQ - Complete Setup Guide

Follow these steps to get the full-stack application running.

## 📋 Prerequisites Checklist

- [ ] Node.js 18+ installed
- [ ] pnpm installed (`npm install -g pnpm`)
- [ ] Python 3.9+ installed
- [ ] Supabase account created

## 🗄️ Step 1: Supabase Setup (15 minutes)

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click **"New Project"**
3. Choose organization and set:
   - **Project Name:** `cliniq` (or your choice)
   - **Database Password:** Save this securely!
   - **Region:** Choose closest to you
4. Click **"Create new project"** and wait ~2 minutes

### 1.2 Run Database Schema

1. In your Supabase dashboard, go to **SQL Editor** (left sidebar)
2. Click **"New query"**
3. Open `backend/schema.sql` in your code editor
4. Copy the entire contents
5. Paste into Supabase SQL Editor
6. Click **"Run"** (or press Ctrl/Cmd + Enter)
7. You should see: "Success. No rows returned"

### 1.3 Load Seed Data

1. Still in **SQL Editor**, click **"New query"** again
2. Open `backend/seed_data.sql`
3. Copy entire contents
4. Paste into SQL Editor
5. Click **"Run"**
6. You should see success messages

### 1.4 Create Storage Bucket

1. Go to **Storage** in left sidebar
2. Click **"Create a new bucket"**
3. Set:
   - **Name:** `patient-documents`
   - **Public bucket:** ✅ (checked)
4. Click **"Create bucket"**

### 1.5 Get Your Credentials

1. Go to **Project Settings** (gear icon in left sidebar)
2. Click **API** in settings menu
3. Copy these values (you'll need them soon):
   ```
   Project URL: https://xxxxx.supabase.co
   anon/public key: eyJhbG...
   service_role key: eyJhbG... (keep secret!)
   ```

## 🐍 Step 2: Backend Setup (10 minutes)

### 2.1 Navigate to Backend

```bash
cd backend
```

### 2.2 Create Python Virtual Environment

**On Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This will install FastAPI, Supabase, JWT libraries, etc. (takes ~2 minutes)

### 2.4 Configure Environment Variables

```bash
cp .env.example .env
```

Now edit `.env` file with your Supabase credentials:

```env
# Paste your Supabase credentials here
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbG... (your anon key)
SUPABASE_SERVICE_KEY=eyJhbG... (your service_role key)

# Generate a random secret (or use this one for testing)
JWT_SECRET_KEY=your_super_secret_key_must_be_at_least_32_characters_long

# These can stay as-is for local development
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:8443","http://localhost:3000"]
```

### 2.5 Start Backend Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

✅ **Test it:** Open http://localhost:8000 in your browser
You should see: `{"message": "ClinIQ API", "version": "1.0.0", ...}`

✅ **View API docs:** Open http://localhost:8000/docs
You should see interactive Swagger documentation!

**Keep this terminal running!**

## ⚛️ Step 3: Frontend Setup (5 minutes)

### 3.1 Open New Terminal

Open a new terminal window/tab (keep backend running in the first one)

### 3.2 Navigate to Frontend

```bash
cd frontend
```

### 3.3 Install Dependencies

```bash
pnpm install
```

This installs React, Vite, Tailwind, etc. (takes ~2 minutes)

### 3.4 Configure Environment

```bash
cp .env.example .env
```

Edit `.env` if needed (default should work):
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3.5 Start Frontend Dev Server

```bash
pnpm dev
```

You should see:
```
VITE v8.x.x ready in xxx ms

➜  Local:   http://localhost:8443/
```

✅ **Test it:** Open http://localhost:8443 in your browser
You should see the ClinIQ landing page!

## 🔐 Step 4: Test the Application (5 minutes)

### 4.1 Test Login

1. Open http://localhost:8443
2. Click **"Sign in"** → **"Clinical app sign in"**
3. Login credentials:
   - **Email:** `maya.patel@northlake.org`
   - **Password:** `clinical-access`
4. Click **"Continue to doctor workspace"**

You should now see the doctor dashboard!

### 4.2 Test Patient Search

1. Click **"Patient search"** in the navigation
2. Search for: `Sunita`
3. Click on **"Sunita Jadhav"** result
4. You should see her complete patient chart!

### 4.3 Test Clinical Analysis

1. From Sunita's chart, click **"Add clinical info"**
2. Fill in symptoms and observations (or use defaults)
3. Click **"Request clinical analysis"**
4. Wait for ~3 seconds (mock processing)
5. You should see AI-generated diagnoses and recommendations!

### 4.4 Test Admin Console

1. Logout (click user menu → "Log out")
2. Go back to login page
3. Click **"Sign in"** → **"Admin console sign in"**
4. Login credentials:
   - **Email:** `admin@northlake.org`
   - **Password:** `clinical-access`
5. You should see the admin dashboard with system metrics!

## ✅ Verification Checklist

- [ ] Backend running on http://localhost:8000
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Frontend running on http://localhost:8443
- [ ] Can login as doctor
- [ ] Can search and view patients
- [ ] Can request clinical analysis
- [ ] Can login as admin
- [ ] Can view system metrics

## 🐛 Troubleshooting

### Backend Issues

**Error: "ModuleNotFoundError"**
- Make sure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Error: "Connection refused" or Supabase errors**
- Check your `.env` file has correct Supabase credentials
- Verify Supabase project is active (green status in dashboard)
- Make sure you ran both `schema.sql` AND `seed_data.sql`

**Error: "Port 8000 already in use"**
- Another process is using port 8000
- Stop it or use different port: `uvicorn main:app --reload --port 8001`
- Update frontend `.env` to match: `VITE_API_BASE_URL=http://localhost:8001`

### Frontend Issues

**Error: "Failed to fetch"**
- Backend must be running first!
- Check `VITE_API_BASE_URL` in frontend `.env`
- Verify CORS settings in backend `.env` include your frontend URL

**Error: "Cannot find module"**
- Delete `node_modules` and `pnpm-lock.yaml`
- Run `pnpm install` again

**Port 8443 already in use**
- Vite will automatically use next available port
- Check terminal output for actual port number

### Database Issues

**No patients showing up**
- Make sure you ran `seed_data.sql` in Supabase
- Check Supabase Table Editor to verify data exists
- Check browser console for API errors

**Authentication fails**
- Password in seed data is: `clinical-access`
- Check users exist in Supabase users table
- Verify JWT_SECRET_KEY is set in backend `.env`

## 🎯 Next Steps

1. **Explore the API:** Visit http://localhost:8000/docs and try endpoints
2. **Check the database:** Open Supabase Table Editor to see real-time data
3. **Modify seed data:** Edit `seed_data.sql` with your own test data
4. **Integrate API calls:** Replace mock data in `frontend/src/App.tsx` with API calls from `api.ts`
5. **Customize styling:** Edit `frontend/src/index.css` for theme changes

## 📞 Getting Help

If you're still stuck:

1. Check backend logs in terminal for error messages
2. Check browser console (F12) for frontend errors
3. Verify all environment variables are set correctly
4. Review Supabase logs in dashboard → Logs section
5. Make sure both SQL scripts ran successfully

---

**Happy coding! 🚀**
