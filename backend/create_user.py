import sys
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.security import get_password_hash
from core.database import get_db

def create_user(email: str, password: str, full_name: str, role: str, department: str = None):
    db = get_db()
    
    # Check if user already exists
    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        print(f"Error: User with email '{email}' already exists (ID: {existing.data[0]['id']}).")
        return None

    hashed_pw = get_password_hash(password)
    user_data = {
        "email": email,
        "password_hash": hashed_pw,
        "full_name": full_name,
        "role": role,
        "department": department,
        "status": "active"
    }
    
    res = db.table("users").insert(user_data).execute()
    if res.data:
        new_u = res.data[0]
        print(f"\nSUCCESS: User created successfully!")
        print(f"  - User ID:    {new_u.get('id')}")
        print(f"  - Name:       {new_u.get('full_name')}")
        print(f"  - Email:      {new_u.get('email')}")
        print(f"  - Role:       {new_u.get('role')}")
        print(f"  - Department: {new_u.get('department')}")
        print(f"  - Password:   {password}")
        return new_u
    else:
        print("Error creating user in database.")
        return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create a new ClinIQ user account")
    parser.add_argument("--email", help="User email address")
    parser.add_argument("--password", default="clinical-access", help="User password (default: clinical-access)")
    parser.add_argument("--name", help="Full name")
    parser.add_argument("--role", choices=["doctor", "assistant", "admin"], help="User role")
    parser.add_argument("--department", default="General Medicine", help="Department")

    args = parser.parse_args()

    if args.email and args.name and args.role:
        create_user(args.email, args.password, args.name, args.role, args.department)
    else:
        print("Interactive ClinIQ User Creator:")
        email = input("Enter email: ").strip()
        name = input("Enter full name (e.g. Dr. Jane Doe): ").strip()
        role = input("Enter role [doctor / assistant / admin]: ").strip().lower()
        dept = input("Enter department (e.g. Cardiology, Neurology): ").strip() or "General Medicine"
        password = input("Enter password (press Enter for 'clinical-access'): ").strip() or "clinical-access"
        create_user(email, password, name, role, dept)
