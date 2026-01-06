import os
import importlib.util

# Load backend/app.py as a module regardless of package import paths
APP_PATH = os.path.join(os.path.dirname(__file__), "app.py")
spec = importlib.util.spec_from_file_location("backend_app", APP_PATH)
app_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_mod)

# app instance is defined as `app` in backend/app.py
app = getattr(app_mod, "app")

if __name__ == "__main__":
    # Run without the reloader so the process stays in this terminal
    app.run(debug=False, use_reloader=False)
