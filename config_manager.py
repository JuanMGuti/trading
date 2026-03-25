import json
import os
import shutil
import logging
from typing import Any, Dict, List, Optional

# ── Logging configuration ────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# Allowed value ranges for validation
_TRADING_RULES: dict = {
    "risk_amount":      (lambda v: isinstance(v, (int, float)) and v > 0,
                         "risk_amount must be a positive number"),
    "max_daily_loss":   (lambda v: isinstance(v, (int, float)) and v > 0,
                         "max_daily_loss must be a positive number"),
    "min_risk_reward":  (lambda v: isinstance(v, (int, float)) and v >= 1.0,
                         "min_risk_reward must be >= 1.0"),
    "max_spread_pips":  (lambda v: isinstance(v, (int, float)) and v > 0,
                         "max_spread_pips must be a positive number"),
    "max_risk_percent": (lambda v: isinstance(v, (int, float)) and 0 < v <= 100,
                         "max_risk_percent must be between 0 and 100"),
    "magic_number":     (lambda v: isinstance(v, int) and v > 0,
                         "magic_number must be a positive integer"),
}

REQUIRED_SECTIONS = ("trading", "analysis", "symbols", "logging", "mt5")


class ConfigManager:
    """
    Configuration manager for the Expert Advisor trading bot.

    Handles loading, validation, access, and persistence of configuration
    settings stored in a JSON file.
    """

    def __init__(self, config_file: str = "config.json") -> None:
        """
        Args:
            config_file: Path to the JSON configuration file.
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()

    # ── Loading ──────────────────────────────────────────────────────────────

    def load_config(self) -> bool:
        """Load and validate configuration from the JSON file.

        Returns:
            True if loading and validation succeeded, False otherwise.
        """
        if not os.path.exists(self.config_file):
            logger.warning("Config file '%s' not found. Creating default.", self.config_file)
            self.create_default_config()
            return False

        try:
            with open(self.config_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            logger.error("Cannot parse config file '%s': %s", self.config_file, exc)
            return False
        except OSError as exc:
            logger.error("Cannot read config file '%s': %s", self.config_file, exc)
            return False

        if not data:
            logger.error("Config file '%s' is empty.", self.config_file)
            return False

        self.config = data
        if not self.validate_config():
            logger.error("Configuration validation failed.")
            return False

        logger.info("Configuration loaded from '%s'.", self.config_file)
        return True

    # ── Validation ───────────────────────────────────────────────────────────

    def validate_config(self) -> bool:
        """Validate all required sections and trading parameters.

        Returns:
            True if the configuration is valid, False otherwise.
        """
        # 1. Check required top-level sections
        for section in REQUIRED_SECTIONS:
            if section not in self.config:
                logger.error("Missing required config section: '%s'.", section)
                return False

        # 2. Validate trading fields with type + range checks
        trading = self.config["trading"]
        for field, (rule, msg) in _TRADING_RULES.items():
            if field not in trading:
                logger.error("Missing trading field: '%s'.", field)
                return False
            if not rule(trading[field]):
                logger.error("Invalid value for '%s': %s. %s", field, trading[field], msg)
                return False

        # 3. At least one symbol must be configured
        if not self.config.get("symbols"):
            logger.error("At least one symbol must be configured.")
            return False

        return True

    # ── Read / Write helpers ─────────────────────────────────────────────────

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a config value using dot-notation (e.g. 'trading.risk_amount').

        Args:
            key_path: Dot-separated path to the desired value.
            default:  Value returned when the key is not found.

        Returns:
            The configuration value, or *default* if not found.
        """
        try:
            node = self.config
            for key in key_path.split("."):
                node = node[key]
            return node
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> bool:
        """Set a config value using dot-notation.

        Intermediate dictionaries are created automatically.

        Args:
            key_path: Dot-separated path to the target key.
            value:    Value to assign.

        Returns:
            True on success, False on error.
        """
        try:
            keys = key_path.split(".")
            node = self.config
            for key in keys[:-1]:
                node = node.setdefault(key, {})
            node[keys[-1]] = value
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Error setting '%s': %s", key_path, exc)
            return False

    # ── Persistence ──────────────────────────────────────────────────────────

    def save_config(self) -> bool:
        """Persist current configuration to disk.

        A timestamped backup of the existing file is created before
        overwriting to prevent data loss.

        Returns:
            True on success, False on error.
        """
        # Create backup of existing file
        if os.path.exists(self.config_file):
            backup_path = self.config_file + ".bak"
            try:
                shutil.copy2(self.config_file, backup_path)
                logger.debug("Backup created at '%s'.", backup_path)
            except OSError as exc:
                logger.warning("Could not create backup: %s", exc)

        try:
            with open(self.config_file, "w", encoding="utf-8") as fh:
                json.dump(self.config, fh, indent=2, ensure_ascii=False)
            logger.info("Configuration saved to '%s'.", self.config_file)
            return True
        except OSError as exc:
            logger.error("Error saving config: %s", exc)
            return False

    def create_default_config(self) -> None:
        """Write a default configuration file to disk."""
        default: Dict[str, Any] = {
            "trading": {
                "risk_amount": 50.0,
                "max_daily_loss": 200.0,
                "min_risk_reward": 2.0,
                "max_spread_pips": 3.0,
                "max_risk_percent": 5.0,
                "magic_number": 234567,
            },
            "analysis": {
                "lookback_period": 20,
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "support_resistance_touches": 2,
                "candle_body_threshold": 1.5,
            },
            "symbols": [
                {"name": "EURUSD", "enabled": True, "max_spread": 0.0003, "timeframe": "M1"},
                {"name": "GBPUSD", "enabled": True, "max_spread": 0.0004, "timeframe": "M1"},
            ],
            "logging": {
                "enabled": True,
                "level": "INFO",
                "log_trades": True,
                "log_analysis": False,
            },
            "mt5": {
                "terminal_paths": [
                    "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                    "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
                ],
                "connection_timeout": 60,
                "retry_attempts": 3,
            },
        }
        try:
            with open(self.config_file, "w", encoding="utf-8") as fh:
                json.dump(default, fh, indent=2, ensure_ascii=False)
            self.config = default
            logger.info("Default configuration created at '%s'.", self.config_file)
        except OSError as exc:
            logger.error("Could not create default config: %s", exc)

    # ── Convenience accessors ────────────────────────────────────────────────

    def get_trading_config(self) -> Dict[str, Any]:
        """Return the trading configuration section."""
        return self.config.get("trading", {})

    def get_analysis_config(self) -> Dict[str, Any]:
        """Return the analysis configuration section."""
        return self.config.get("analysis", {})

    def get_enabled_symbols(self) -> List[Dict[str, Any]]:
        """Return only the enabled symbol entries."""
        return [s for s in self.config.get("symbols", []) if s.get("enabled", False)]

    def get_mt5_config(self) -> Dict[str, Any]:
        """Return the MT5 configuration section."""
        return self.config.get("mt5", {})

    def is_logging_enabled(self) -> bool:
        """Return True if logging is enabled in the configuration."""
        return bool(self.config.get("logging", {}).get("enabled", True))

    def print_config(self) -> None:
        """Print the full configuration in human-readable JSON format."""
        print("\nCurrent Configuration:")
        print("=" * 50)
        print(json.dumps(self.config, indent=2))


def main() -> None:
    """Smoke-test the ConfigManager."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    cfg = ConfigManager()
    print("Configuration Manager Test")
    print("=" * 30)

    print(f"Risk amount     : {cfg.get('trading.risk_amount')}")
    print(f"MACD fast period: {cfg.get('analysis.macd_fast')}")
    print(f"Enabled symbols : {[s['name'] for s in cfg.get_enabled_symbols()]}")

    cfg.set("trading.risk_amount", 75.0)
    print(f"Updated risk    : {cfg.get('trading.risk_amount')}")

    cfg.print_config()


if __name__ == "__main__":
    main()
