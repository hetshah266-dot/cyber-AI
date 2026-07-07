import bcrypt

# Real passwords we want to use
passwords = {
    "STUDENT_BCRYPT_HASH": "student123",
    "TEACHER_BCRYPT_HASH": "teacher123",
    "INVESTIGATOR_BCRYPT_HASH": "cyber123",
    "OTHER_BCRYPT_HASH": "other123"
}

print("--- COPY THESE EXACTLY INTO YOUR .env FILE --- \n")
for env_variable_name, plain_password in passwords.items():
    # Generate a real salt and cryptographic hash matching the password
    hashed_bytes = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
    # Decode to text string format for the environment file
    print(f"{env_variable_name}={hashed_bytes.decode('utf-8')}")