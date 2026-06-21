import importlib
import pathlib


def test_import_all_src_modules_except_main():
    project_root = pathlib.Path(__file__).resolve().parents[1]
    src_root = project_root / 'src'
    assert src_root.exists(), f'src directory not found at {src_root}'

    failures = []
    for path in sorted(src_root.rglob('*.py')):
        if path.name == 'main.py' or path.name.startswith('__'):
            continue

        rel = path.relative_to(project_root)
        module_name = '.'.join(rel.with_suffix('').parts)
        try:
            importlib.import_module(module_name)
        except Exception as e:
            failures.append((module_name, e))

    if failures:
        lines = [f"{m}: {ex!r}" for m, ex in failures]
        raise AssertionError("Failed to import modules:\n" + "\n".join(lines))
