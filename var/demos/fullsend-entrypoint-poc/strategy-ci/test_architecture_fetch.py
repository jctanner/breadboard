"""Offline check for Git cone-mode version alias handling."""
import ast
from pathlib import Path


def test_version_directories_ignore_aliases_but_detect_extra_versions(tmp_path):
    source = Path(__file__).resolve().parent.parent / "runner-validation/architecture-fetch.py"
    tree = ast.parse(source.read_text())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == "version_directories")
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
    versions = namespace["version_directories"]
    assert versions(tmp_path / "missing") == []
    (tmp_path / "rhoai-3.6-ea.2").mkdir()
    (tmp_path / "early-access").symlink_to("rhoai-3.6-ea.2", target_is_directory=True)
    assert versions(tmp_path) == ["rhoai-3.6-ea.2"]
    (tmp_path / "rhoai-3.5").mkdir()
    assert versions(tmp_path) == ["rhoai-3.5", "rhoai-3.6-ea.2"]
