if __name__ != "__main__":
    raise ImportError("This is a standalone script and should not be imported.")


import doctest
import warnings
import traceback

import pdoc

import linearmoney  # noqa: F401


class CustomRunner(doctest.DocTestRunner):
    def summarize(self, verbose=None):
        """Override the default summary output to print the total number of
        passed tests every time."""

        if verbose is None:
            verbose = self._verbose
        if verbose:
            return super().summarize(verbose=True)
        else:
            passed = []
            for x in self._name2ft.items():
                name, (f, t) = x
                assert f <= t
                if f == 0 and t > 0:
                    passed.append((name, t))
            if passed:
                print(len(passed), "items passed all tests:")
                passed.sort()
                for thing, count in passed:
                    print(" %3d tests in %s" % (count, thing))

            return super().summarize(verbose=False)


runner = CustomRunner()
finder = doctest.DocTestFinder()


class TMP:
    pass


def _run_module_doctests(module: pdoc.doc.Module):
    for i in finder.find(module, module.fullname):
        runner.run(i)
    for i in module.flattened_own_members:
        # Run doctests on documented variables and public api members
        # imported from package-private submodules.
        tmp = TMP()
        tmp.__doc__ = i.docstring
        for i in finder.find(tmp, i.fullname):
            runner.run(i)


# Mostly copied from pdoc.pdoc() implementation:
all_modules: list[pdoc.doc.Module] = []
for module_name in pdoc.extract.walk_specs(["linearmoney"]):
    try:
        all_modules.append(pdoc.doc.Module.from_name(module_name))
    except RuntimeError:
        warnings.warn(f"Error importing {module_name}:\n{traceback.format_exc()}")

if not all_modules:
    raise RuntimeError("Unable to import any modules.")


# Collect and run all docstring examples as doctests.
for i in all_modules:
    _run_module_doctests(i)


# Print the summarized doctest results
runner.summarize()
