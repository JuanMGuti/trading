import sys
import logging
from datetime import datetime

import MetaTrader5 as mt5

logger = logging.getLogger(__name__)


def _ensure_initialized() -> bool:
    """Initialize MT5 only if not already connected."""
    if mt5.terminal_info() is not None:
        return True
    if not mt5.initialize():
        logger.error('Failed to initialize MetaTrader 5: %s', mt5.last_error())
        return False
    return True


def get_detailed_account_info():
    """Retrieve comprehensive account information.

    Returns:
        A dictionary of account fields, or None on failure.
    """
    if not _ensure_initialized():
        return None
    account_info = mt5.account_info()
    if account_info is None:
        logger.error('Failed to get account info. Last error: %s', mt5.last_error())
        return None
    return {
        'login':        account_info.login,
        'server':       account_info.server,
        'name':         account_info.name,
        'company':      account_info.company,
        'currency':     account_info.currency,
        'balance':      account_info.balance,
        'equity':       account_info.equity,
        'margin':       account_info.margin,
        'free_margin':  account_info.margin_free,
        'margin_level': account_info.margin_level,
        'profit':       account_info.profit,
        'trade_allowed': account_info.trade_allowed,
        'trade_expert': account_info.trade_expert,
        'leverage':     account_info.leverage,
        'margin_so_mode': account_info.margin_so_mode,
        'margin_so_call': account_info.margin_so_call,
        'margin_so_so': account_info.margin_so_so,
    }


def print_account_summary(account_data):
    """Print a formatted account summary."""
    if not account_data:
        print('No account data available.')
        return
    cur = account_data['currency']
    print('\n' + '=' * 50)
    print(' ACCOUNT INFORMATION')
    print('=' * 50)
    print(f"Account ID   : {account_data['login']}")
    print(f"Server       : {account_data['server']}")
    print(f"Company      : {account_data['company']}")
    print(f"Account Name : {account_data['name']}")
    print(f"Currency     : {cur}")
    print(f"Leverage     : 1:{account_data['leverage']}")
    print('\n' + '-' * 30)
    print(' FINANCIAL DATA')
    print('-' * 30)
    for label, key in (('Balance','balance'),('Equity','equity'),('Profit/Loss','profit'),('Free Margin','free_margin')):
        print(f"{label:<13}: {account_data[key]:>12.2f} {cur}")
    print(f"Margin Level : {account_data['margin_level']:>11.2f}%")
    print('\n' + '-' * 30)
    print(' TRADING STATUS')
    print('-' * 30)
    print(f"Trading Allowed : {'yes' if account_data['trade_allowed'] else 'NO'}")
    print(f"Expert Advisors : {'yes' if account_data['trade_expert'] else 'NO'}")
    print(f"Last Updated    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print('=' * 50)


def check_trading_conditions(account_data):
    """Check if account is ready for trading. Returns bool."""
    if not account_data:
        return False
    warnings, errors = [], []
    if not account_data['trade_allowed']:
        errors.append('Trading is not allowed on this account.')
    if not account_data['trade_expert']:
        errors.append('Expert Advisors are not enabled.')
    ml = account_data['margin_level']
    if ml < 100:
        errors.append(f'Critical margin level: {ml:.2f}%')
    elif ml < 200:
        warnings.append(f'Low margin level: {ml:.2f}%')
    if account_data['free_margin'] < 100:
        warnings.append(f"Low free margin: {account_data['free_margin']:.2f}")
    if warnings:
        print('\nWARNINGS:')
        for w in warnings: print(f'  - {w}')
    if errors:
        print('\nERRORS:')
        for e in errors: print(f'  - {e}')
        return False
    if not warnings:
        print('\nAccount is ready for trading.')
    return True


def main():
    """Entry point."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    try:
        logger.info('Retrieving account information...')
        data = get_detailed_account_info()
        if data:
            print_account_summary(data)
            check_trading_conditions(data)
        else:
            logger.error('Failed. Ensure MT5 is running and you are logged in.')
            sys.exit(1)
    except KeyboardInterrupt:
        print('\nOperation cancelled by user.')
    except Exception:
        logger.exception('Unexpected error.')
        sys.exit(1)
    finally:
        mt5.shutdown()


if __name__ == '__main__':
    main()