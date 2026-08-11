import os

os.environ["ACD_DATABASE_URL"] = "sqlite:////tmp/acd_test_studio.db"
os.environ["ACD_MEDIA_ROOT"] = "/tmp/acd_test_media"
os.environ["ACD_MASTER_KEY"] = "test-master-key"

from app import models  # noqa: E402,F401
from app.database import Base, engine  # noqa: E402

Base.metadata.create_all(bind=engine)
