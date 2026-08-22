import nox

nox.options.default_venv_backend = "uv"
nox.options.sessions = ["quality", "tests"]
DEVELOPMENT_EXTRAS = ".[dev]"


@nox.session
def quality(session: nox.Session) -> None:
    session.install("-e", DEVELOPMENT_EXTRAS)
    session.run("ruff", "format", "--check", "src", "tests")
    session.run("ruff", "check", "src", "tests")
    session.run("pyright")
    session.run("lint-imports")
    session.run("deptry", "src")
    session.run("vulture", "src")


@nox.session
def tests(session: nox.Session) -> None:
    session.install("-e", DEVELOPMENT_EXTRAS)
    session.run("pytest")


@nox.session
def typing(session: nox.Session) -> None:
    session.install("-e", DEVELOPMENT_EXTRAS)
    session.run("pyright")
