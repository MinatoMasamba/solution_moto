"""Own the local server lifecycle so a stopped background server cannot invalidate QA."""
from pathlib import Path
import socket
import subprocess
import time
import urllib.request

app=Path(__file__).resolve().parents[1]
root=app.parent
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0))
    port=sock.getsockname()[1]
with (root/'.local/profile-qa-server.log').open('w') as log:
    server=subprocess.Popen([str(root/'venv/bin/python'),'manage.py','runserver',f'127.0.0.1:{port}','--noreload'],cwd=root,stdout=log,stderr=log)
    try:
        for _ in range(100):
            if server.poll() is not None:raise RuntimeError('Le serveur de recette ne démarre pas. Consulter .local/profile-qa-server.log.')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/v1/health/',timeout=1) as response:
                    if response.status==200:break
            except OSError:time.sleep(.1)
        else:raise RuntimeError('Délai de démarrage dépassé.')
        result=subprocess.run(['flutter','test','test/profile_live_test.dart','--dart-define=LIVE_DG=true',f'--dart-define=LIVE_API_URL=http://127.0.0.1:{port}'],cwd=app)
        raise SystemExit(result.returncode)
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill();server.wait()
