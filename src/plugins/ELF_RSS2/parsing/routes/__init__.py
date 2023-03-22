from typing import List


def __list_all_modules() -> List[str]:
    from pathlib import Path

    module_paths = list(Path(__file__).parent.glob("*.py"))
    return [module.name[:-3] for module in module_paths if module.name != "__init__.py"]


ALL_MODULES = sorted(__list_all_modules())
__all__ = ALL_MODULES + ["ALL_MODULES"]
