"""Wait until a local web server responds. Used in CI and setup checks."""
import sys
import time
from urllib.request import urlopen

url = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000/api/health'
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 35
for second in range(limit):
    try:
        with urlopen(url, timeout=2) as response:
            if response.status == 200:
                print('OK: Attendance application is running at', url)
                sys.exit(0)
    except Exception:
        pass
    time.sleep(1)
print('ERROR: Attendance application did not start. Check the server terminal.', file=sys.stderr)
sys.exit(1)
