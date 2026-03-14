import os

from pathlib import Path

from docker.types import Mount


BASE = Path(os.environ["HOST_PROJECT_DIR"])


src = Mount("/project/src", str(BASE / "src"), type="bind")
datalake = Mount("/project/datalake", str(BASE / "datalake"), type="bind")
env = Mount("/project/", str(BASE / ".env"), type="bind")