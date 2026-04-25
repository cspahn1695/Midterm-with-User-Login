from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#password encryption and verification functions, using bcrypt via passlib. These are used in the auth_routes.py file for registration and login.
# this code is the same as the in class examples
def hash_password(password: str):
    # bcrypt max length = 72 bytes
    password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)