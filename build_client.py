import shutil
import subprocess
import os

from betsys import __version__

licenses = ["LICENSE", "LICENSE.qasync"]
DIST_FOLDER = f"Build [BetSys v.{__version__}] - Client"
PROJECT_FOLDER = f"Betting System - Client"


if __name__ == "__main__":
    if os.path.exists(DIST_FOLDER):
        shutil.rmtree(DIST_FOLDER, ignore_errors=True)

    try:
        subprocess.run(
            [
                "pyinstaller",
                "build_client.spec",
                "--distpath", DIST_FOLDER, # noqa
                "--clean",
                "--noconfirm" # noqa
            ],
            check=True
        )

        if os.path.exists("build"):
            shutil.rmtree("build", ignore_errors=True)

        for lic in licenses:
            shutil.copy2(lic, os.path.join(DIST_FOLDER, PROJECT_FOLDER))

    except Exception as exception:
        print(f"Error: {exception}")

        if os.path.exists(DIST_FOLDER):
            shutil.rmtree(DIST_FOLDER, ignore_errors=True)
