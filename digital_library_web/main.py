from pathlib import Path
import subprocess
from sodatools import CD

CR = Path(__file__).resolve().parent


def main():
    with CD(str(CR)):
        subprocess.run("deno task build", shell=True)
        subprocess.run("deno run --allow-net --allow-env --allow-read main.ts", shell=True)


if __name__ == "__main__":
    main()
