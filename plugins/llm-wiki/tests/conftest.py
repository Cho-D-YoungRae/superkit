import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "source-extract" / "scripts"


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def wiki_check():
    return load_script("wiki_check")


@pytest.fixture(scope="session")
def yt_transcript():
    return load_script("yt_transcript")


@pytest.fixture(scope="session")
def pdf_chunk():
    return load_script("pdf_chunk")


@pytest.fixture(scope="session")
def html_to_md():
    return load_script("html_to_md")
