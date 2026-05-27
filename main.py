from dotenv import load_dotenv
import os
import sys

load_dotenv()

secret = os.getenv("APP_SECRET")

if not secret:
    print("ERROR: APP_SECRET not found")
    sys.exit(1)

print(f"System started. Secret hash: {secret[:3]}**")
