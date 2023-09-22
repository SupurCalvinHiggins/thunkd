import pytest
from thunkd import *


@pytest.fixture
def project() -> dict:
    return load_json(Path("test_data/project.json").read_text())


@pytest.fixture
def clean_project() -> dict:
    return load_json(Path("test_data/clean_project.json").read_text())


@pytest.fixture
def modular_project() -> dict:
    return read_modular_project(project_path=Path("test_data/modular_project"))


def test_to_clean_project(project: dict, clean_project: dict) -> None:
    assert to_clean_project(project=project) == clean_project


def test_to_modular_project(clean_project: dict, modular_project: dict) -> None:
    print(modular_project, flush=True)
    print(to_modular_project(project=clean_project), flush=True)
    assert to_modular_project(project=clean_project) == modular_project


def test_from_modular_project(clean_project: dict, modular_project: dict) -> None:
    assert from_modular_project(modular_project=modular_project) == clean_project