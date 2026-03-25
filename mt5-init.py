import MetaTrader5 as mt5
import os
import sys
import glob
import logging
from datetime import datetime

# ── Logging configuration ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def initialize_mt5(terminal_path=None):
    """
    Initialize MetaTrader 5 connection with error handling.

    Args:
        terminal_path (str | None): Path to MT5 terminal executable.
            If None, common installation paths are tried automatically.

    Returns:
        bool: True if initialization was successful, False otherwise.
    """
    try:
        if terminal_path:
            # ── Use the explicitly provided path ────────────────────────────
            if not isinstance(terminal_path, str) or not terminal_path.strip():
                logger.error("terminal_path must be a non-empty string.")
                return False

            if not mt5.initialize(terminal_path):
                logger.error(
                    "Failed to initialize MT5 with path '%s'. Error: %s",
                    terminal_path,
                    mt5.last_error(),
                )
                return False

        else:
            # ── Try default initialization first ────────────────────────────
            if mt5.initialize():
                logger.info("MetaTrader 5 initialized with default settings.")
            else:
                # Build common paths; use glob to resolve wildcard entries
                username = os.getenv("USERNAME") or os.getenv("USER", "")
                raw_paths = [
                    r"C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                    r"C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
                    rf"C:\\Users\\{username}\\AppData\\Roaming\\MetaQuotes\\Terminal\\*\\terminal64.exe",
                ]

                # Expand glob patterns so wildcards are resolved correctly
                common_paths = []
                for p in raw_paths:
                    expanded = glob.glob(p)
                    common_paths.extend(expanded if expanded else [p])

                initialized = False
                for path in common_paths:
                    if os.path.isfile(path) and mt5.initialize(path):
                        logger.info("MetaTrader 5 initialized using: %s", path)
                        initialized = True
                        break

                if not initialized:
                    logger.error(
                        "Failed to initialize MetaTrader 5. "
                        "Tried default and %d alternative path(s).",
                        len(common_paths),
                    )
                    return False

        # ── Verify connection ────────────────────────────────────────────────
        account_info = mt5.account_info()
        if account_info is None:
            logger.error(
                "MT5 initialized but could not retrieve account info. Error: %s",
                mt5.last_error(),
            )
            mt5.shutdown()
            return False

        logger.info("MetaTrader 5 initialized successfully.")
        logger.info("  Account : %s", account_info.login)
        logger.info("  Server  : %s", account_info.server)
        logger.info("  Time    : %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return True

    except Exception:
        logger.exception("Unexpected exception during MT5 initialization.")
        return False


def main():
    """Entry point: initialize MT5 or print troubleshooting tips on failure."""
    if not initialize_mt5():
        logger.error(
            "Initialization failed. Troubleshooting tips:\n"
            "  1. Ensure MetaTrader 5 is installed.\n"
            "  2. Check that the MT5 terminal is running.\n"
            "  3. Verify your trading account credentials.\n"
            "  4. Make sure algorithmic trading is enabled in MT5."
        )
        sys.exit(1)

    logger.info("Initialization complete. You can now run your trading scripts.")


if __name__ == "__main__":
    main()
