# ClinIQ - Clinical Decision Support System

A full-stack clinical decision support application with React + TypeScript frontend and FastAPI + Supabase backend.

## 🏗️ Project Structure

```
.
├── frontend/          # React + Vite + Tailwind CSS frontend
│   ├── src/
│   │   ├── App.tsx           # Main application component
│   │   ├── main.tsx          # React entry point
│   │   ├── api.ts            # API client functions
│   │   ├── config.ts         # Configuration and auth helpers
│   │   └── index.css         # Global styles with Tailwind
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
│
├── backend/           # FastAPI + Supabase backend
│   ├── core/
│   │   ├── config.py         # App configuration
│   │   ├── database.py       # Supabase client
│   │   └── security.py       # JWT auth & bcrypt
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   ├── routers/
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── patients.py       # Patient management
│   │   ├── appointments.py   # Appointment scheduling
│   │   ├── analyses.py       # Clinical analysis (AI mock)
│   │   ├── documents.py      # Document upload/retrieval
│   │   └── admin.py          # Admin operations
│   ├── services/
│   │   └── mock_analysis.py  # Mock AI analysis generator
│   ├── main.py               # FastAPI application
│   ├── schema.sql            # Database schema
│   ├── seed_data.sql         # Sample data with Marathi names
│   └── requirements.txt
│
└── README.md          # This file
```

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ and **pnpm** (for frontend)
- **Python** 3.9+ (for backend)
- **Supabase account** ([supabase.com](https://supabase.com))

### 1. Set Up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** in your Supabase dashboard
3. Run the schema creation:
   - Copy contents of `backend/schema.sql`
   - Execute in SQL Editor
4. Run the seed data:
   - Copy contents of `backend/seed_data.sql`
   - Execute in SQL Editor
5. Create a storage bucket:
   - Go to **Storage** in dashboard
   - Create a new **public bucket** named `patient-documents`
6. Note your project credentials:
   - Project URL (e.g., `https://xxx.supabase.co`)
   - Anon/Public key
   - Service role key (keep secret!)

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your Supabase credentials
# REQUIRED:
#   SUPABASE_URL=https://your-project.supabase.co
#   SUPABASE_KEY=your-anon-key
#   SUPABASE_SERVICE_KEY=your-service-role-key
#   JWT_SECRET_KEY=your-secret-key-min-32-chars

# Run the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at **http://localhost:8000**

API docs at **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Create .env file
cp .env.example .env

# Edit .env (default should work):
# VITE_API_BASE_URL=http://localhost:8000

# Run the frontend
pnpm dev
```

Frontend will be available at **http://localhost:8443**

## 🔐 Default Login Credentials

All users have the password: **`clinical-access`**

### Doctor Account
- **Email:** `maya.patel@northlake.org`
- **Name:** Dr. Priya Deshmukh
- **Role:** Doctor (Cardiology)

### Clinical Assistant Account
- **Email:** `jamie.rivera@northlake.org`
- **Name:** Aditya Kulkarni
- **Role:** Assistant (Cardiology)

### Admin Account
- **Email:** `admin@northlake.org`
- **Name:** Sneha Patil
- **Role:** Admin

## 📊 Data Model

### Core Entities

- **Users** - Doctors, assistants, and admins with role-based access
- **Patients** - Patient demographics and medical history
- **Appointments** - Scheduling and queue management
- **Visits** - Timeline of clinical events
- **Clinical Analyses** - AI-generated diagnostic reports
- **Diagnoses** - Differential diagnoses with confidence scores
- **Recommendations** - Clinical next steps
- **Decisions** - Clinician approval/rejection records
- **Documents** - Uploaded files (labs, imaging, etc.)
- **Knowledge Sources** - Clinical guideline databases
- **Audit Log** - System activity tracking

## 🎯 Key Features

### Clinical Workflow
1. **Patient Registration** - Assistants register new patients with medical history
2. **Appointment Management** - Today's queue with status tracking
3. **Patient Chart** - Complete medical history and timeline
4. **Clinical Analysis** - Mock AI generates diagnostic recommendations
5. **Decision Recording** - Doctors approve/modify/reject recommendations
6. **Document Upload** - Attach labs, imaging, prescriptions to patient records

### Admin Console
- User management (CRUD, activate/deactivate)
- System metrics dashboard
- Knowledge source management
- Audit log viewing

### Security
- JWT-based authentication with bcrypt password hashing
- Role-based access control (RBAC)
- Protected endpoints with user role verification
- Secure file storage via Supabase

## 🧪 API Endpoints

### Authentication
- `POST /auth/login` - Login with email/password
- `POST /auth/logout` - Logout

### Patients
- `POST /patients` - Create patient
- `GET /patients/search?q=<query>` - Search patients
- `GET /patients/{id}` - Get patient details
- `PATCH /patients/{id}` - Update patient
- `GET /patients/{id}/timeline` - Get visit history

### Appointments
- `GET /appointments/today` - Today's appointments
- `POST /appointments` - Create appointment
- `PATCH /appointments/{id}` - Update appointment status

### Clinical Analyses
- `POST /analyses` - Request AI analysis
- `GET /analyses/{id}` - Get analysis results
- `GET /analyses/patient/{id}` - Get patient's analyses
- `POST /analyses/{id}/decision` - Record clinical decision

### Documents
- `POST /documents/upload` - Upload document
- `GET /documents/patient/{id}` - Get patient documents
- `DELETE /documents/{id}` - Delete document

### Admin
- `GET /admin/users` - List all users
- `POST /admin/users` - Create user
- `PATCH /admin/users/{id}` - Update user
- `GET /admin/metrics` - System metrics
- `GET /admin/knowledge-sources` - List knowledge sources

## 🤖 Mock AI Analysis

The backend currently generates **mock clinical analysis data** for testing. When you request an analysis:

1. Analysis status starts as "processing"
2. Background task simulates 3-second processing delay
3. Generates random diagnoses, recommendations, and warnings
4. Status updates to "awaiting_review"
5. Doctor can then approve/modify/reject

**To integrate real AI later:** Replace `services/mock_analysis.py` with your AI model inference code.

## 🔄 Integrating Frontend with Backend

The frontend includes API client functions in `frontend/src/api.ts`:

```typescript
import { authAPI, patientsAPI, analysesAPI } from './api';

// Login example
const { access_token, user } = await authAPI.login(email, password);
setAuthToken(access_token);

// Search patients
const results = await patientsAPI.search("Sunita");

// Request analysis
const analysis = await analysesAPI.request({
  patient_id: "CLQ-10482",
  new_symptoms: "...",
  observations: "..."
});
```

Replace hardcoded mock data in `App.tsx` with these API calls for full integration.

## 🌐 Environment Variables

### Backend (`.env`)
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
JWT_SECRET_KEY=generate-a-secure-random-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:8443","http://localhost:3000"]
```

### Frontend (`.env`)
```env
VITE_API_BASE_URL=http://localhost:8000
```

## 📦 Deployment

### Backend Deployment
- Deploy to Railway, Render, or AWS Lambda
- Set environment variables in hosting platform
- Ensure Supabase credentials are secure
- Update CORS_ORIGINS for production domains

### Frontend Deployment
- Build: `cd frontend && pnpm build`
- Deploy `dist/` folder to Vercel, Netlify, or Cloudflare Pages
- Set `VITE_API_BASE_URL` to production backend URL

## 🛠️ Development Notes

### Adding New API Endpoints
1. Create Pydantic schemas in `backend/models/schemas.py`
2. Add router in `backend/routers/`
3. Include router in `backend/main.py`
4. Update `frontend/src/api.ts` with client functions

### Database Migrations
- Modify `backend/schema.sql` for schema changes
- Run updated SQL in Supabase SQL Editor
- Update Pydantic models to match

### Testing Backend
- Visit http://localhost:8000/docs for interactive API docs
- Test endpoints with built-in Swagger UI
- Use curl or Postman for API testing

## 📝 Sample Data

The seed data includes:
- 4 patients with Marathi/Maharashtra names (Sunita Jadhav, Ramesh Bhosale, Manjusha Pawar, Anand Kale)
- 4 appointments for today
- Sample clinical analysis with diagnoses
- Knowledge sources (clinical guidelines)
- Audit log entries

## 🤝 Contributing

This is a prototype clinical decision support system. Key areas for enhancement:
1. Replace mock AI with real ML models
2. Add comprehensive error handling
3. Implement loading states in frontend
4. Add form validation
5. Expand test coverage
6. Add real-time notifications
7. Implement advanced search and filtering

## 📄 License

[Add your license here]

## 🙋 Support

For questions or issues:
1. Check API docs at http://localhost:8000/docs
2. Review Supabase logs in dashboard
3. Check browser console for frontend errors
4. Verify environment variables are set correctly

---

**Built with:** React 19, Vite 8, Tailwind CSS 4, FastAPI, Supabase, PostgreSQL, JWT Auth
