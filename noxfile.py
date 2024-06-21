import nox


@nox.session(reuse_venv=True)
def lint(session):
    """Lint code without applying fixes or changes"""
    session.install(".[dev]")
    session.run("ruff", "check")
    session.run("black", "miniscope_io", "--diff")


@nox.session(reuse_venv=True)
def format(session):
    """Lint and format code"""
    session.install(".[dev]")
    session.run("ruff", "check", "--fix")
    session.run("black", "miniscope_io")
