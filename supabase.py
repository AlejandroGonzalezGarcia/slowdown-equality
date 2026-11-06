# supabase project password 0xTEXVbamNHmJhz8

import os
import json
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Load credentials
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

# Directory where results are stored
results_dir = "./results"