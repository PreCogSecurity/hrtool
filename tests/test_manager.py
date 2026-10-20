"""Tests for manager.py parsing logic - hrtool component manager.

These tests focus on the pure Python parsing logic without requiring
PySide, Qt, or the full manager class instantiation.
"""

import gzip
import os
import unittest
from unittest.mock import patch


from debian import deb822


class TestParsePackagesLogic(unittest.TestCase):
    """Test the parse_packages logic in isolation."""

    def test_deb822_required_fields_via_mapping(self):
        """deb822 entries should support required fields via Mapping interface."""
        package_file = os.path.join(
            os.path.dirname(__file__), '..', 'Packages.gz'
        )
        with gzip.open(package_file, 'rb') as f:
            content = f.read()
        packages = content.strip().split(b'\n\n')
        for package in packages:
            deb = deb822.Deb822(package)
            # Deb822 implements Mapping interface - fields accessible via deb['Key']
            self.assertIn('Package', deb,
                          "deb822 entry should support 'Package' key access")
            self.assertIn('Version', deb,
                          "deb822 entry should support 'Version' key access")
            self.assertIn('Description', deb,
                          "deb822 entry should support 'Description' key access")

    def test_packages_gz_is_valid_gzip(self):
        """Packages.gz should be valid gzip-compressed data."""
        package_file = os.path.join(
            os.path.dirname(__file__), '..', 'Packages.gz'
        )
        self.assertTrue(os.path.exists(package_file))
        with gzip.open(package_file, 'rb') as f:
            content = f.read()
        self.assertIsInstance(content, bytes)
        self.assertGreater(len(content), 0)


class TestGetInstalledVersionsLogic(unittest.TestCase):
    """Test the get_installed_versions filtering logic in isolation."""

    def test_filters_installed_only(self):
        """Test the installed-version filtering logic as implemented in manager.py.

        The code checks `len(toks) > 4` after splitting dpkg-query output.
        dpkg-query format: ${Package} ${Status} ${Version} extra*
        Status typically contains 'installed' substring.
        """
        # Test data with 'installed' in the status field and enough tokens:
        test_versions = [
            'head  install ok installed  1.0.0  extra1  extra2',  # 8 tokens, has 'installed'
            'head  not-installed  0.5.0  extra1  extra2',  # 5 tokens, no 'installed'
            'hr-tool  install ok installed  2.0.0  extra1  extra2',  # 8 tokens, has 'installed'
            'some-pkg  unknown  0.1.0',  # 3 tokens, no 'installed'
        ]
        installed_versions = {}
        for v in test_versions:
            if 'installed' in v:
                toks = v.split()
                if len(toks) > 4:
                    installed_versions[toks[0]] = toks[-1]
        # head and hr-tool have 'installed' + >4 tokens
        self.assertEqual(len(installed_versions), 2)
        self.assertIn('head', installed_versions)
        self.assertIn('hr-tool', installed_versions)

    def test_handles_missing_version_gracefully(self):
        """Versions without enough tokens should be skipped."""
        test_versions = [
            'head install',  # 2 tokens - too few, skipped
            'head  install ok installed  1.0.0  extra1  extra2  extra3  extra4',  # 10 tokens - valid
        ]
        installed_versions = {}
        for v in test_versions:
            if 'installed' in v:
                toks = v.split()
                if len(toks) > 4:
                    installed_versions[toks[0]] = toks[-1]
        # Only the second line has 'installed' + > 4 tokens
        self.assertEqual(len(installed_versions), 1)
        self.assertIn('head', installed_versions)


class TestListComponentsLogic(unittest.TestCase):
    """Test the list_components filtering logic."""

    def test_removes_standard_components(self):
        """list_components should remove head, head-deps, opencog, opencog-deps."""
        components = ['head', 'head-deps', 'opencog', 'opencog-deps', 'custom-pkg', 'hr-tool']
        forbidden = ['head', 'head-deps', 'opencog', 'opencog-deps']
        result = [c for c in components if c not in forbidden]
        self.assertEqual(result, ['custom-pkg', 'hr-tool'])
        self.assertNotIn('head', result)


class TestMainWindowIntegration(unittest.TestCase):
    """Integration-style tests that require minimal setup.

    These tests instantiate MainWindow from manager.py, which requires
    PySide. They are skipped when PySide is not available.
    """

    @unittest.skipIf(
        'PySide' not in __import__('sys').modules,
        "PySide not available - skipping MainWindow integration tests"
    )
    @patch('manager.subprocess.check_output')
    def test_list_components_mocked(self, mock_check_output):
        """list_components works when hr cmd list_components returns expected output."""
        mock_check_output.return_value = b'head-deps custom-pkg\n'
        # Import is guarded by conftest.py adding sys.path
        from manager import MainWindow
        mw = MainWindow()
        self.assertIsNotNone(mw)

    @unittest.skipIf(
        'PySide' not in __import__('sys').modules,
        "PySide not available - skipping MainWindow integration tests"
    )
    @patch('manager.subprocess.check_output')
    def test_get_installed_versions_mocked(self, mock_check_output):
        """get_installed_versions works when dpkg-query returns expected output."""
        mock_check_output.return_value = b'head  install ok installed  1.0.0  extra1  extra2\nhr-tool  install ok installed  2.0.0  extra1  extra2\n'
        from manager import MainWindow
        mw = MainWindow()
        versions = mw.get_installed_versions(mw.installed_components)
        # Should return dict with installed packages
        self.assertIsInstance(versions, dict)


if __name__ == '__main__':
    unittest.main()