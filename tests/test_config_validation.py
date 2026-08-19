import unittest
from dataclasses import replace

from bot.config import Config, _validate_config


def valid_config() -> Config:
    return Config(
        bot_token="123456789:abcdefghijklmnopqrstuvwxyzABCDE",
        report_channel_id=-1001234567890,
        admin_ids={123456789},
        excel_file="data/abonents.xlsx",
        inspectors_file="data/inspectors.xlsx",
        database_file="storage/bot.sqlite3",
        contact_phones="71-262-55-81",
        district_address="Olimlar ko'chasi 51-uy",
        district_lat=41.0,
        district_lon=69.0,
        backup_dir="backups",
        backup_interval_hours=24,
        backup_retention_days=30,
        backup_keep_sets=30,
        encryption_enabled=True,
        encryption_password="test",
        health_check_interval_hours=6,
        backup_maximum_age_hours=48,
        minimum_disk_free_gb=2,
        minimum_disk_free_percent=5,
        request_window_seconds=10,
        user_request_limit=15,
        staff_request_limit=60,
        flood_block_seconds=60,
        max_excel_upload_mb=25,
        max_meter_photo_mb=10,
        max_meter_photos=10,
        bulk_send_delay=0.15,
        error_channel_id=-1001234567890,
        location_channel_id=None,
        health_port=None,
    )


class ConfigValidationTests(unittest.TestCase):
    def test_valid_config_is_accepted(self) -> None:
        config = valid_config()
        self.assertIs(_validate_config(config), config)

    def test_invalid_token_is_rejected_early(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "BOT_TOKEN"):
            _validate_config(replace(valid_config(), bot_token="bad-token"))

    def test_super_admin_is_required(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "ADMIN_IDS"):
            _validate_config(replace(valid_config(), admin_ids=set()))

    def test_report_channel_is_required(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "REPORT_CHANNEL_ID"):
            _validate_config(
                replace(valid_config(), report_channel_id=None)
            )


if __name__ == "__main__":
    unittest.main()
