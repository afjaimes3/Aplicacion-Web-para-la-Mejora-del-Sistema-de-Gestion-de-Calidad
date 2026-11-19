import os
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('POWERBI_API_KEY', '')  # Configura POWERBI_API_KEY en tu .env
url = f"http://127.0.0.1:5000/api/bi/procesos?key={api_key}"
headers = {}

req = urllib.request.Request(url, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.status}")
        print(response.read().decode('utf-8')[:100])
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.reason}")
    print(e.read().decode('utf-8'))
except urllib.error.URLError as e:
    print(f"URLError: {e.reason}")
