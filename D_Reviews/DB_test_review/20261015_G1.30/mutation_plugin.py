import os, sys
def pytest_configure(config):
    path = os.environ.get("MUTANT")
    if not path:
        return
    import app.services.reset_service as mod
    src = open(path, encoding="utf-8").read()
    exec(compile(src, path, "exec"), mod.__dict__)
    print("MUTANT LOADED", path, file=sys.stderr)
