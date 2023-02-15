import astroid
from astroid import nodes

from pylint import utils
from pylint.checkers import BaseChecker
from pylint.lint import PyLinter


class ModuleOnlyImports(BaseChecker):
    DEFAULT_EXCLUDED_MODULES = {"typing", "typing_extensions", "six.moves", "collections.abc", "__future__"}
    DEFAULT_EXCLUDED_NAMES = {"_", "__"}
    ONLY_IMPORTING_MODULES_IS_ALLOWED = "only-importing-modules-is-allowed"

    name = "check-if-we-import-only-modules"

    msgs = {
        "C5101": (
            '"%s" shouldn\'t be imported directly.',
            ONLY_IMPORTING_MODULES_IS_ALLOWED,
            "",
        ),
    }

    options = (
        (
            "google-style-excluded-modules",
            {
                "default": "",
                "type": "string",
                "metavar": "<str>",
                "help": "Comma-separated list of modules to ignore during check",
            },
        ),
        (
            "google-style-excluded-names",
            {
                "default": "",
                "type": "string",
                "metavar": "<str>",
                "help": "Comma-separated list of import names to ignore during check",
            },
        ),
    )

    priority = -1


    def visit_importfrom(self, node):
        _excluded_modules = frozenset(
            self.DEFAULT_EXCLUDED_MODULES | set(utils._splitstrip(self.linter.config.google_style_excluded_modules))
        )
        _excluded_names = frozenset(
            self.DEFAULT_EXCLUDED_NAMES | set(utils._splitstrip(self.linter.config.google_style_excluded_names))
        )

        imported = node.do_import_module()
        if imported.name in _excluded_modules:
            return

        for name, _ in node.names:
            if name in _excluded_names:
                continue

            _, result = imported.lookup(name)
            if not result:
                # it's not there, so probably this is another module - fine.
                continue
            imported_node, *_ = result
            if isinstance(imported_node, nodes.Module):
                continue

            # maybe a submodule?
            try:
                imported.import_module(name, relative_only=True)
            except astroid.AstroidImportError:
                self.add_message(
                    self.ONLY_IMPORTING_MODULES_IS_ALLOWED, node=node, args=(name,)
                )


def register(linter):
    linter.register_checker(ModuleOnlyImports(linter))
