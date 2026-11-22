"""Point the app at a throwaway database before any test imports it."""
import os
import tempfile

os.environ["LANER_DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
