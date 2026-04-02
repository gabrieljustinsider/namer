"""
Tests namer_configparser
"""

from configupdater import ConfigUpdater
import tempfile
import unittest
from importlib import resources
from pathlib import Path

from loguru import logger

from namer.configuration import NamerConfig
from namer.configuration_utils import from_config, to_ini
from test import utils


class UnitTestAsTheDefaultExecution(unittest.TestCase):
    """
    Always test first.
    """

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)

        if not utils.is_debugging():
            logger.remove()

    def test_configuration(self) -> None:
        updater = ConfigUpdater(allow_no_value=True)
        config_str = ''
        if hasattr(resources, 'files'):
            config_str = resources.files('namer').joinpath('namer.cfg.default').read_text()
        elif hasattr(resources, 'read_text'):
            config_str = resources.read_text('namer', 'namer.cfg.default')
        updater.read_string(config_str)
        namer_config = from_config(updater, NamerConfig())
        namer_config.config_updater = updater
        namer_config.sites_with_no_date_info = ['badsite']
        ini_content = to_ini(namer_config)
        self.assertIn('sites_with_no_date_info = badsite', ini_content.splitlines())

        updated = ConfigUpdater(allow_no_value=True)
        lines = ini_content.splitlines()
        lines.remove('sites_with_no_date_info = badsite')
        files_no_sites_with_no_date_info = '\n'.join(lines)

        updated.read_string(files_no_sites_with_no_date_info)
        double_read = NamerConfig()
        double_read = from_config(updated, double_read)
        self.assertEqual(double_read.sites_with_no_date_info, [])
        updated.read_string(ini_content)
        double_read = from_config(updated, double_read)
        self.assertIn('badsite', double_read.sites_with_no_date_info)

        updated.read_string(files_no_sites_with_no_date_info)
        double_read = from_config(updated, double_read)
        self.assertIn('badsite', double_read.sites_with_no_date_info)

    def test_default_config_and_save_settings(self) -> None:
        from namer.configuration_utils import default_config

        with tempfile.TemporaryDirectory(prefix='test') as tmp_dir:
            cfg_path = Path(tmp_dir) / 'namer.cfg'
            if hasattr(resources, 'files'):
                default_val = resources.files('namer').joinpath('namer.cfg.default').read_text()
            else:
                default_val = resources.read_text('namer', 'namer.cfg.default')
            cfg_path.write_text(default_val, encoding='UTF-8')

            config = default_config(cfg_path)
            self.assertEqual(config.config_file, cfg_path)
            original_token = config.porndb_token
            config.config_updater['namer']['porndb_token'].value = 'test-token'
            config.config_file.write_text(str(config.config_updater), encoding='UTF-8')

            reloaded = default_config(cfg_path)
            self.assertEqual(reloaded.porndb_token, 'test-token')
            self.assertNotEqual(original_token, reloaded.porndb_token)

