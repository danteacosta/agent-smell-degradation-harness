from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from label_plane.private_env import PrivateEnvError, load_private_env


class PrivateEnvTests(unittest.TestCase):
    def _load_text(self, text: str, *, environment: dict[str, str] | None = None) -> dict[str, str]:
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(text, encoding="utf-8")
            target = {} if environment is None else environment
            load_private_env(path, environ=target)
            return target

    def test_private_env_loader_module_is_available(self) -> None:
        self.assertIsNotNone(importlib.util.find_spec("label_plane.private_env"))

    def test_missing_file_preserves_environment(self) -> None:
        environment = {"EXISTING": "value"}

        load_private_env(Path("/definitely/missing/private-panel.env"), environ=environment)

        self.assertEqual(environment, {"EXISTING": "value"})

    def test_loads_basic_exported_empty_and_whitespace_assignments(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(
                "\n# private panel\n  PANEL_ALPHA = first  \n\texport PANEL_BETA=second\nPANEL_EMPTY=\n",
                encoding="utf-8",
            )
            environment: dict[str, str] = {}

            load_private_env(path, environ=environment)

        self.assertEqual(
            environment,
            {"PANEL_ALPHA": "first", "PANEL_BETA": "second", "PANEL_EMPTY": ""},
        )

    def test_inherited_presence_wins_including_empty_values(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("PANEL_ALPHA=file\nPANEL_EMPTY=file\n", encoding="utf-8")
            environment = {"PANEL_ALPHA": "inherited", "PANEL_EMPTY": ""}

            load_private_env(path, environ=environment)

        self.assertEqual(environment, {"PANEL_ALPHA": "inherited", "PANEL_EMPTY": ""})

    def test_distinguishes_embedded_hash_from_whitespace_comment(self) -> None:
        environment = self._load_text(
            "PANEL_EMBEDDED=alpha#beta\nPANEL_COMMENT=alpha # private comment\n"
        )

        self.assertEqual(environment, {"PANEL_EMBEDDED": "alpha#beta", "PANEL_COMMENT": "alpha"})

    def test_parses_quoted_hashes_supported_escapes_and_trailing_comments(self) -> None:
        environment = self._load_text(
            "PANEL_SINGLE='alpha # beta' # comment\n"
            'PANEL_DOUBLE="alpha \\"beta\\" \\\\ path"\n'
        )

        self.assertEqual(
            environment,
            {"PANEL_SINGLE": "alpha # beta", "PANEL_DOUBLE": 'alpha "beta" \\ path'},
        )

    def test_rejects_duplicate_names(self) -> None:
        with self.assertRaisesRegex(PrivateEnvError, r"duplicate.*PANEL_VALUE.*line 2"):
            self._load_text("PANEL_VALUE=first\nPANEL_VALUE=second\n")

    def test_rejects_invalid_names_and_exact_export_boundary(self) -> None:
        for text in ("panel_lower=value\n", "_PANEL=value\n", "exportPANEL=value\n"):
            with self.subTest(text=text), self.assertRaisesRegex(PrivateEnvError, r"line 1"):
                self._load_text(text)

    def test_rejects_unsupported_quoted_escape(self) -> None:
        with self.assertRaisesRegex(PrivateEnvError, r"line 1"):
            self._load_text('PANEL_VALUE="alpha\\n"\n')

    def test_rejects_trailing_text_after_quoted_value(self) -> None:
        with self.assertRaisesRegex(PrivateEnvError, r"line 1"):
            self._load_text('PANEL_VALUE="alpha" trailing\n')

    def test_invalid_utf8_fails_without_exposing_path_or_bytes(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "private-secret-name.env"
            path.write_bytes(b"PANEL_VALUE=\xff\n")

            with self.assertRaises(PrivateEnvError) as raised:
                load_private_env(path, environ={})

        message = str(raised.exception)
        self.assertNotIn("private-secret-name", message)
        self.assertNotIn("PANEL_VALUE", message)

    def test_directory_path_fails_without_exposing_path(self) -> None:
        with TemporaryDirectory(prefix="private-secret-directory-") as directory:
            with self.assertRaises(PrivateEnvError) as raised:
                load_private_env(Path(directory), environ={})

        self.assertNotIn("private-secret-directory", str(raised.exception))

    def test_read_failure_is_translated_without_exposing_operating_system_error(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("PANEL_VALUE=unused\n", encoding="utf-8")
            with patch.object(Path, "read_text", side_effect=OSError("SECRET_PATH_SENTINEL")):
                with self.assertRaises(PrivateEnvError) as raised:
                    load_private_env(path, environ={})

        self.assertNotIn("SECRET_PATH_SENTINEL", str(raised.exception))

    def test_late_error_does_not_partially_mutate_environment_or_expose_value(self) -> None:
        secret = "SECRET_VALUE_SENTINEL"
        environment = {"EXISTING": "preserved"}
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text(f"PANEL_SECRET={secret}\nmalformed-line\n", encoding="utf-8")

            with self.assertRaises(PrivateEnvError) as raised:
                load_private_env(path, environ=environment)

        self.assertEqual(environment, {"EXISTING": "preserved"})
        self.assertNotIn(secret, str(raised.exception))
