from pathlib import Path
import subprocess
from sodatools import CD
import platform

deno_command = (
    "deno" if platform.system() == "Windows" else Path.home().joinpath(".deno/bin/deno")
)
CR = Path(__file__).resolve().parent


def main():
    with CD(str(CR)):
        subprocess.run(f"{deno_command} task build", shell=True)
        subprocess.run(
            f"{deno_command} --allow-net --allow-env --allow-read main.ts", shell=True
        )


if __name__ == "__main__":
    main()
