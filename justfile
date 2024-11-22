# Show this help list
help:
    @echo 'Run `just get-started` to init a development env.'
    @just --list

# Init a development env
get-started:
    @echo 'Checking that you have `uv` installed'
    @echo 'If you need it, I recommend installing `pipx` from https://pipx.pypa.io/stable/ then `pipx install uv`'
    uv --version
    @echo 'Checking that you have Python 3.12 installed'
    @echo 'If you need it, I recommend installing `pyenv` from https://github.com/pyenv/pyenv then `pyenv install 3.12`'
    @echo 'You also might need to activate the global shim with `pyenv global system 3.12`'
    python3.12 --version
    @echo 'Creating the development virtual env in `venvs/dev/`'
    mkdir -p venvs
    test -d venvs/dev/ || uv venv -p 3.12 venvs/dev/
    @echo 'Compiling all dependencies'
    just venv-compile-all
    @echo 'Installing all the tools and dependencies'
    just venv-sync dev
    @echo 'All done!'
    @echo 'Each time before you do any work in this repo you should run `. venvs/dev/bin/activate`'
    @echo 'Once the `dev` venv is activated, run:'
    @echo
    @echo '`just develop` to re-build Bytewax and install it in the venv'
    @echo '`just test-py` to run the Python test suite'
    @echo '`just lint` to lint the source code'
    @echo '`just --list` to show more advanced recipes'

# Assert we are in a venv.
_assert-venv:
    #!/usr/bin/env python
    import sys
    p = sys.prefix
    if not (p.endswith("venvs/dev") or p.endswith("venv")):
        print("You must activate the `dev` venv with `. venvs/dev/bin/activate` before running this command", file=sys.stderr)
        sys.exit(1)


# Install the library locally in an editable state
develop: _assert-venv
    @# You never need to run with `-E` / `--extras`; the `dev` and test
    @# virtualenvs already have the optional dependencies pinned.
    uv pip install -e .

venv-sync venv:
    VIRTUAL_ENV={{justfile_directory()}}/venvs/{{venv}} uv pip sync --strict requirements/{{venv}}.txt

# Sync all venvs
venv-sync-all: (venv-sync "doc") (venv-sync "dev")


venv-compile-all:
    uv pip compile --generate-hashes -p 3.9 --all-extras pyproject.toml -o requirements/lib-py3.9.txt
    uv pip compile --generate-hashes -p 3.10 --all-extras pyproject.toml -o requirements/lib-py3.10.txt
    uv pip compile --generate-hashes -p 3.11 --all-extras pyproject.toml -o requirements/lib-py3.11.txt
    uv pip compile --generate-hashes -p 3.12 --all-extras pyproject.toml -o requirements/lib-py3.12.txt

# Lint the code in the repo; runs in CI
lint: _assert-venv
    vermin --config-file vermin-lib.ini src/ pytests/
    vermin --config-file vermin-dev.ini docs/ *.py
    ruff check src/ pytests/ docs/
    mypy -p bytewax.duckdb
    mypy pytests/ docs/


pytests := 'pytests/'

# Run the Python tests; runs in CI
test-py tests=pytests: _assert-venv
    pytest {{tests}}

# Run all the checks that will be run in CI locally
ci-pre: lint test-py

# Build the package
build: _assert-venv
    @echo 'Installing build tools'
    uv pip install build
    @echo 'Cleaning old build artifacts'
    rm -rf dist/
    @echo 'Building the package'
    python -m build

# Upload the package to PyPI
upload: _assert-venv build
    @echo 'Installing twine'
    uv pip install twine
    @echo 'Uploading the package to PyPI'
    twine upload dist/*
