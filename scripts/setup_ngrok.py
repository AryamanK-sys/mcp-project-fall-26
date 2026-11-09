"""Download ngrok and configure it from the repository's private .env file."""

import io
import json
import os
import platform
from pathlib import Path
import ssl
import subprocess
import tarfile
from urllib.error import URLError
from urllib.request import urlopen
from zipfile import BadZipFile, ZipFile

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_BASE = "https://bin.ngrok.com/c/bNyj1mQVY4c/"


def artifact_for(system: str, machine: str) -> tuple[str, str]:
    systems = {"Darwin": "darwin", "Linux": "linux", "Windows": "windows"}
    # Python and ngrok use different names for the same CPU architecture.
    architectures = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }
    os_name = systems.get(system)
    arch = architectures.get(machine.lower())
    if not os_name or not arch:
        raise RuntimeError(
            "Supported platforms: macOS, Windows and Linux on x64 or ARM64 processors."
        )
    if system == "Windows":
        # ngrok publishes only an x64 build for Windows. Windows 11 on ARM
        # runs x64 programs through its built-in emulation.
        arch = "amd64"
    suffix = "tgz" if system == "Linux" else "zip"
    binary_name = "ngrok.exe" if system == "Windows" else "ngrok"
    return f"ngrok-v3-stable-{os_name}-{arch}.{suffix}", binary_name


def install_ngrok(binary: Path, artifact: str) -> None:
    if binary.is_file():
        return
    try:
        with urlopen(DOWNLOAD_BASE + artifact, timeout=30) as response:
            archive_data = io.BytesIO(response.read())
        # Read only the executable; archive paths never become filesystem paths.
        if artifact.endswith(".zip"):
            with ZipFile(archive_data) as archive:
                data = archive.read(binary.name)
        else:
            with tarfile.open(fileobj=archive_data, mode="r:gz") as archive:
                member = archive.getmember(binary.name)
                if not member.isfile():
                    raise ValueError("The archive member is not an executable file.")
                data = archive.extractfile(member).read()
    except URLError as error:
        if isinstance(error.reason, ssl.SSLCertVerificationError):
            # Python from python.org on macOS ships without trusted certificates
            # until its "Install Certificates" script has been run once.
            raise RuntimeError(
                "Python could not verify the download's security certificate. On macOS, "
                "open the Python 3.14 folder in Applications, run "
                "'Install Certificates.command', then run this helper again."
            ) from None
        raise RuntimeError("Could not download the official ngrok executable.") from None
    except (OSError, ValueError, KeyError, BadZipFile, tarfile.TarError):
        raise RuntimeError("Could not download or extract the official ngrok executable.") from None
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_bytes(data)
    binary.chmod(0o755)


def setup(root: Path = ROOT) -> None:
    token = dotenv_values(root / ".env", interpolate=False).get("NGROK_AUTHTOKEN")
    if not token or not token.strip():
        raise RuntimeError("Add NGROK_AUTHTOKEN to .env before running setup.")
    artifact, name = artifact_for(platform.system(), platform.machine())
    local = root / ".local"
    binary = local / "bin" / name
    install_ngrok(binary, artifact)

    config = local / "ngrok.yml"
    # JSON-quoted strings are valid YAML and preserve special token characters.
    config_text = f'version: "3"\nagent:\n  authtoken: {json.dumps(token.strip())}\n'
    # On POSIX systems, restrict credential access before writing the token.
    descriptor = os.open(config, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        config.chmod(0o600)
        stream.write(config_text)
    policy = {
        "on_http_request": [{
            "actions": [{
                "type": "add-headers",
                "config": {"headers": {"host": "127.0.0.1:8000"}},
            }],
        }],
    }
    # The tunnel forwards the local Host value expected by the MCP HTTP server.
    (local / "ngrok-policy.json").write_text(json.dumps(policy, indent=2) + "\n")
    result = subprocess.run(
        [str(binary), "config", "check", "--config", str(config)],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        # Agent diagnostics can include config values, so keep them out of logs.
        raise RuntimeError("ngrok rejected the configuration; check your .env token.")
    print("ngrok is installed and the project-local configuration is valid.")
    print("See docs/week1/ngrok-setup.md to start the HTTP server and tunnel.")


if __name__ == "__main__":
    try:
        setup()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
    except OSError:
        raise SystemExit("Could not write or run the project-local ngrok configuration.") from None
