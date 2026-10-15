#!/bin/sh
set -e
mkdir -p /app/logs
python - <<'PY'
import os, re
from urllib.parse import quote_plus
url = "postgresql://{u}:{p}@{h}:5432/{d}".format(
    u=quote_plus(os.environ["POSTGRES_USER"]),
    p=quote_plus(os.environ["POSTGRES_PASSWORD"]),
    h=os.environ["POSTGRES_SERVER"],
    d=os.environ["POSTGRES_DB"])
url = url.replace("%", "%%")
t = open("alembic.ini").read()
t = re.sub(r"(?m)^sqlalchemy\.url\s*=.*$", lambda m: "sqlalchemy.url = " + url, t)
open("alembic.ini", "w").write(t)
PY
alembic upgrade head
exec "$@"
