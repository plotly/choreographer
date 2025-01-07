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

import logistro

logger = logistro.getLogger(__name__)


class TmpDirWarning(UserWarning):
    """A warning if for whatever reason we can't eliminate the tmp dir."""


class TmpDirectory:
    """
    The python stdlib TemporaryDirectory wrapper for easier use.

    Python's TemporaryDirectory suffered a couple API changes that mean
    you can't call it the same way for similar versions. This wrapper is
    also much more aggressive about deleting the directory when it's done,
    not necessarily relying on OS functions.
    """

    def __init__(self, path=None, *, sneak=False):
        """
        Construct a wrapped TemporaryDirectory (TmpDirectory).

        Args:
            path: manually specify the directory to use
            sneak: (default False) avoid using /tmp
                Ubuntu's snap will sandbox /tmp

        """
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

    def _delete_manually(self, *, check_only=False):  # noqa: C901, PLR0912
        if not self.path.exists():
            self.exists = False
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
                    try:
                        fp.chmod(stat.S_IWUSR)
                        fp.unlink()
                    except BaseException as e:  # noqa: BLE001 yes catch and report
                        errors.append((fp, e))
                for d in dirs:
                    fp = Path(root) / d
                    try:
                        fp.chmod(stat.S_IWUSR)
                        fp.rmdir()
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
                TmpDirWarning,
            )
            self.exists = True
        else:
            self.exists = False

        return n_dirs, n_files, errors

    def clean(self):
        """Try several different ways to eliminate the temporary directory."""
        try:
            # no faith in this python implementation, always fails with windows
            # very unstable recently as well, lots new arguments in tempfile package
            self.temp_dir.cleanup()
            self.exists = False
        except BaseException:
            logger.exception("TemporaryDirectory.cleanup() failed.")

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
        except BaseException:
            self._delete_manually(check_only=True)
            if not self.exists:
                return
            logger.exception("shutil.rmtree() failed to delete temporary file.")

            def extra_clean():
                time.sleep(3)
                self._delete_manually()

            t = Thread(target=extra_clean)
            t.run()
            if self.path.exists():
                logger.warning("Temporary dictory couldn't be removed manually.")
