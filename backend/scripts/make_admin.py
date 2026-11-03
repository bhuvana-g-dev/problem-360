"""Promote an EXISTING registered account to admin (there is no admin sign-up, by design).
    cd backend && PYTHONPATH=. python scripts/make_admin.py person@example.com
Run on a trusted machine with the service-account credentials. The person must have registered (e.g. as a citizen) first."""
import sys

from dotenv import load_dotenv
from firebase_admin import auth

from app.core.constants import USERS, AccountType
from app.core.firebase import get_app, get_db

load_dotenv()
if len(sys.argv) != 2:
    raise SystemExit(__doc__)
user = auth.get_user_by_email(sys.argv[1], app=get_app())
ref = get_db().collection(USERS).document(user.uid)
if not ref.get().exists:
    raise SystemExit("That login has no Problem 360 account yet. Register first, then run this again.")
ref.update({"accountType": AccountType.ADMIN, "organizationId": None})
auth.set_custom_user_claims(user.uid, {"accountType": AccountType.ADMIN}, app=get_app())
print(f"{sys.argv[1]} is now an admin.")
