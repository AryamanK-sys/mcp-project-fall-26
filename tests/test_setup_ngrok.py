"""Test setup with synthetic tokens and archive fixtures, without public tunnels."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import ssl
import subprocess
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from urllib.error import URLError
from zipfile import ZipFile

from scripts import setup_ngrok


class NgrokSetupTests(unittest.TestCase):
    def test_platform_download_selection(self):
        cases = [
            ("Darwin", "arm64", "darwin-arm64.zip", "ngrok"),
            ("Darwin", "x86_64", "darwin-amd64.zip", "ngrok"),
            ("Linux", "aarch64", "linux-arm64.tgz", "ngrok"),
            ("Linux", "x86_64", "linux-amd64.tgz", "ngrok"),
            ("Windows", "AMD64", "windows-amd64.zip", "ngrok.exe"),
            # Windows on ARM runs ngrok's x64 build through emulation.
            ("Windows", "ARM64", "windows-amd64.zip", "ngrok.exe"),
        ]
        for system, machine, suffix, name in cases:
            with self.subTest(system=system, machine=machine):
                artifact, binary = setup_ngrok.artifact_for(system, machine)
                self.assertTrue(artifact.endswith(suffix))
                self.assertEqual(binary, name)
        with self.assertRaises(RuntimeError):
            setup_ngrok.artifact_for("Unsupported", "mips")

    def test_certificate_failure_names_the_fix(self):
        failure = URLError(ssl.SSLCertVerificationError("certificate verify failed"))
        with TemporaryDirectory() as directory, patch.object(
            setup_ngrok, "urlopen", side_effect=failure
        ):
            binary = Path(directory) / "ngrok"
            with self.assertRaisesRegex(RuntimeError, "Install Certificates"):
                setup_ngrok.install_ngrok(binary, "ngrok-v3-stable-darwin-arm64.zip")
            self.assertFalse(binary.exists())

    def test_extracts_only_expected_executable(self):
        for suffix in ("zip", "tgz"):
            with self.subTest(archive=suffix), TemporaryDirectory() as directory:
                data = io.BytesIO()
                if suffix == "zip":
                    with ZipFile(data, "w") as archive:
                        archive.writestr("ngrok", b"fixture executable")
                        archive.writestr("../../outside.txt", b"unwanted")
                else:
                    with tarfile.open(fileobj=data, mode="w:gz") as archive:
                        for name, content in (
                            ("ngrok", b"fixture executable"),
                            ("../../outside.txt", b"unwanted"),
                        ):
                            member = tarfile.TarInfo(name)
                            member.size = len(content)
                            archive.addfile(member, io.BytesIO(content))
                data.seek(0)
                binary = Path(directory) / ".local/bin/ngrok"
                with patch.object(setup_ngrok, "urlopen", return_value=data):
                    setup_ngrok.install_ngrok(binary, "fixture." + suffix)
                self.assertEqual(binary.read_bytes(), b"fixture executable")
                self.assertEqual(list(binary.parent.iterdir()), [binary])

    def test_missing_token_does_not_download_or_write(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(setup_ngrok, "urlopen") as download:
                with self.assertRaisesRegex(RuntimeError, "NGROK_AUTHTOKEN"):
                    setup_ngrok.setup(root)
            download.assert_not_called()
            self.assertFalse((root / ".local").exists())

    def test_reuses_binary_updates_private_config_and_redacts_errors(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / ".local/bin/ngrok"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b"existing fixture")
            token = 'synthetic:token#"${UNEXPANDED}'
            (root / ".env").write_text(f"NGROK_AUTHTOKEN='{token}'\n")
            output = io.StringIO()
            with (
                patch.object(setup_ngrok.platform, "system", return_value="Darwin"),
                patch.object(setup_ngrok.platform, "machine", return_value="arm64"),
                patch.object(setup_ngrok, "urlopen") as download,
                patch.object(
                    setup_ngrok.subprocess, "run",
                    return_value=subprocess.CompletedProcess([], 0),
                ) as command,
                redirect_stdout(output),
            ):
                setup_ngrok.setup(root)
                config = root / ".local/ngrok.yml"
                self.assertIn('version: "3"', config.read_text())
                self.assertIn(setup_ngrok.json.dumps(token), config.read_text())
                if setup_ngrok.os.name != "nt":
                    self.assertEqual(config.stat().st_mode & 0o777, 0o600)
                self.assertIn("127.0.0.1:8000", (root / ".local/ngrok-policy.json").read_text())
                self.assertNotIn(token, output.getvalue())
                self.assertNotIn(token, str(command.call_args))
                download.assert_not_called()

                (root / ".env").write_text("NGROK_AUTHTOKEN=updated-fixture\n")
                setup_ngrok.setup(root)
                self.assertIn("updated-fixture", config.read_text())
                command.return_value = subprocess.CompletedProcess([], 1, stderr=token)
                with self.assertRaises(RuntimeError) as failure:
                    setup_ngrok.setup(root)
                self.assertNotIn(token, str(failure.exception))
                self.assertNotIn(token, output.getvalue())
