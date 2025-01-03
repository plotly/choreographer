import os
import platform
import shutil
import stat
import sys
import tempfile
import time
import warnings
from pathlib import Path
from threading import Thread


class TempDirWarning(UserWarning):
    pass


# Python's built-in temporary directory functions are lacking
# In short, they don't handle removal well, and there's
# lots of API changes over recent versions.
# Here we have our own class to deal with it.
class TempDirectory:
    def __init__(self, path=None, *, sneak=False):
        self.debug = True  # temporary! TODO
        self._with_onexc = bool(sys.version_info[:3] >= (3, 12))
        args = {}

        if path:
            args = {"dir": path}
        elif sneak:
            args = {"prefix": ".choreographer-", "dir": Path.home()}

        if platform.system() != "Windows":
            self.temp_dir = tempfile.TemporaryDirectory(**args)
        else:  # is windows
            vinfo = sys.version_info[:3]
            if vinfo >= (3, 12):
                self.temp_dir = tempfile.TemporaryDirectory(
                    delete=False,
                    ignore_cleanup_errors=True,
                    **args,
                )
            elif vinfo >= (3, 10):
                self.temp_dir = tempfile.TemporaryDirectory(
                    ignore_cleanup_errors=True,
                    **args,
                )
            else:
                self.temp_dir = tempfile.TemporaryDirectory(**args)

        self.path = Path(self.temp_dir.name)
        self.exists = True
        if self.debug:
            print(f"TEMP DIR PATH: {self.path}", file=sys.stderr)

    def delete_manually(self, *, check_only=False):  # noqa: C901, PLR0912
        if not self.path.exists():
            self.exists = False
            if self.debug:
                print(
                    "No retry delete manual necessary, path doesn't exist",
                    file=sys.stderr,
                )
            return 0, 0, []
        n_dirs = 0
        n_files = 0
        errors = []
        for root, dirs, files in os.walk(self.path, topdown=False):
            n_dirs += len(dirs)
            n_files += len(files)
            if not check_only:
                for f in files:
                    fp = Path(root) / f
                    if self.debug:
                        print(f"Removing file: {fp}", file=sys.stderr)
                    try:
                        fp.chmod(stat.S_IWUSR)
                        fp.unlink()
                        if self.debug:
                            print("Success", file=sys.stderr)
                    except BaseException as e:  # noqa: BLE001 yes catch and report
                        errors.append((fp, e))
                for d in dirs:
                    fp = Path(root) / d
                    if self.debug:
                        print(f"Removing dir: {fp}", file=sys.stderr)
                    try:
                        fp.chmod(stat.S_IWUSR)
                        fp.rmdir()
                        if self.debug:
                            print("Success", file=sys.stderr)
                    except BaseException as e:  # noqa: BLE001 yes catch and report
                        errors.append((fp, e))

            # clean up directory
        if not check_only:
            try:
                self.path.chmod(stat.S_IWUSR)
                self.path.rmdir()
            except BaseException as e:  # noqa: BLE001 yes catch and report
                errors.append((self.path, e))

        if check_only:
            if n_dirs or n_files:
                self.exists = True
            else:
                self.exists = False
        elif errors:
            warnings.warn(  # noqa: B028
                "The temporary directory could not be deleted, "
                f"execution will continue. errors: {errors}",
                TempDirWarning,
            )
            self.exists = True
        else:
            self.exists = False

        return n_dirs, n_files, errors

    def clean(self):  # noqa: C901
        try:
            # no faith in this python implementation, always fails with windows
            # very unstable recently as well, lots new arguments in tempfile package
            self.temp_dir.cleanup()
            self.exists = False
        except BaseException as e:  # noqa: BLE001 yes catch and report
            if self.debug:
                print(
                    f"First tempdir deletion failed: TempDirWarning: {e!s}",
                    file=sys.stderr,
                )

        def remove_readonly(func, path, _excinfo):
            try:
                Path(path).chmod(stat.S_IWUSR)
                func(str(path))
            except FileNotFoundError:
                pass

        try:
            if self._with_onexc:
                shutil.rmtree(self.path, onexc=remove_readonly)
            else:
                shutil.rmtree(self.path, onerror=remove_readonly)
            self.exists = False
            del self.temp_dir
        except FileNotFoundError:
            pass  # it worked!
        except BaseException as e:  # noqa: BLE001 yes catch like this and report and try
            if self.debug:
                print(
                    f"Second tmpdir deletion failed (shutil.rmtree): {e!s}",
                    file=sys.stderr,
                )
            self.delete_manually(check_only=True)
            if not self.exists:
                return

            def extra_clean():
                time.sleep(3)
                self.delete_manually()

            t = Thread(target=extra_clean)
            t.run()
        if self.debug:
            print(
                f"Tempfile still exists?: {self.path.exists()!s}",
                file=sys.stderr,
            )
