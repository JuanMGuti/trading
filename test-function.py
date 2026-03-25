import time
import logging
from datetime import datetime

import MetaTrader5 as mt5

# Magic number must match config.json
MAGIC_NUMBER = 234567
VALID_ORDER_TYPES = frozenset({'BUY', 'SELL'})

logger = logging.getLogger(__name__)


def validate_symbol(symbol: str) -> bool:
    """Return True if the symbol is available and visible in Market Watch."""
    info = mt5.symbol_info(symbol)
    if info is None:
        logger.error('Symbol %s not found.', symbol)
        return False
    if not info.visible:
        logger.warning('Symbol %s not visible; adding to Market Watch.', symbol)
        if not mt5.symbol_select(symbol, True):
            logger.error('Failed to add %s to Market Watch.', symbol)
            return False
    return True


def calculate_safe_lot_size(symbol: str, risk_amount: float, stop_loss_pips: float) -> float:
    """Calculate a position size based on a fixed monetary risk.

    Args:
        symbol:          Trading symbol.
        risk_amount:     Maximum loss in account currency.
        stop_loss_pips:  Stop-loss distance in *pips* (not points).

    Returns:
        Validated lot size rounded to the broker's lot step.
    """
    info = mt5.symbol_info(symbol)
    if info is None:
        logger.error('Cannot get symbol info for %s; using minimum lot.', symbol)
        return 0.01

    min_lot  = info.volume_min
    max_lot  = info.volume_max
    lot_step = info.volume_step
    tick_val = info.trade_tick_value   # value of one tick in account currency
    tick_sz  = info.trade_tick_size    # size of one tick in price

    # Pip size: 0.0001 for most pairs, 0.01 for JPY pairs
    pip_size = 0.01 if symbol.endswith('JPY') else 0.0001
    pip_value = tick_val * (pip_size / tick_sz)

    if pip_value <= 0:
        logger.error('Invalid pip_value (%s) for %s; using minimum lot.', pip_value, symbol)
        return min_lot

    raw_lots = risk_amount / (stop_loss_pips * pip_value)
    # Round to broker lot step
    rounded = round(raw_lots / lot_step) * lot_step
    return max(min_lot, min(rounded, max_lot))


def place_test_order(symbol: str = 'EURUSD', order_type: str = 'BUY', risk_amount: float = 50.0) -> bool:
    """Place a market order for testing purposes.

    Args:
        symbol:       Trading symbol.
        order_type:   'BUY' or 'SELL' (case-insensitive).
        risk_amount:  Risk in account currency.

    Returns:
        True if the order was filled, False otherwise.
    """
    order_type = order_type.upper()
    if order_type not in VALID_ORDER_TYPES:
        logger.error("Invalid order_type '%s'. Must be 'BUY' or 'SELL'.", order_type)
        return False

    if mt5.terminal_info() is None and not mt5.initialize():
        logger.error('Failed to initialize MT5: %s', mt5.last_error())
        return False

    if not validate_symbol(symbol):
        return False

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logger.error('No tick data for %s.', symbol)
        return False

    # Pip size depends on pair type (must be consistent with lot-size calc)
    is_jpy = symbol.endswith('JPY')
    pip_size   = 0.01 if is_jpy else 0.0001
    stop_pips  = 50  # fixed SL distance in pips
    sl_dist    = stop_pips * pip_size
    tp_dist    = stop_pips * 2 * pip_size  # 1:2 risk-reward

    if order_type == 'BUY':
        price       = tick.ask
        stop_loss   = price - sl_dist
        take_profit = price + tp_dist
        mt5_type    = mt5.ORDER_TYPE_BUY
    else:
        price       = tick.bid
        stop_loss   = price + sl_dist
        take_profit = price - tp_dist
        mt5_type    = mt5.ORDER_TYPE_SELL

    lot_size = calculate_safe_lot_size(symbol, risk_amount, stop_pips)

    request = {
        'action':       mt5.TRADE_ACTION_DEAL,
        'symbol':       symbol,
        'volume':       lot_size,
        'type':         mt5_type,
        'price':        price,
        'sl':           stop_loss,
        'tp':           take_profit,
        'deviation':    20,
        'magic':        MAGIC_NUMBER,
        'comment':      f'Test {order_type} order',
        'type_filling': mt5.ORDER_FILLING_IOC,
        'type_time':    mt5.ORDER_TIME_GTC,
    }

    logger.info('Placing %s order for %s | vol=%.2f price=%.5f sl=%.5f tp=%.5f',
                order_type, symbol, lot_size, price, stop_loss, take_profit)

    result = mt5.order_send(request)
    if result is None:
        logger.error('order_send returned None. Last error: %s', mt5.last_error())
        return False

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        error_map = {
            mt5.TRADE_RETCODE_INVALID_VOLUME: 'Invalid volume',
            mt5.TRADE_RETCODE_INVALID_PRICE:  'Invalid price',
            mt5.TRADE_RETCODE_INVALID_STOPS:  'Invalid SL/TP',
            mt5.TRADE_RETCODE_TRADE_DISABLED: 'Trading disabled',
            mt5.TRADE_RETCODE_MARKET_CLOSED:  'Market closed',
            mt5.TRADE_RETCODE_NO_MONEY:        'Insufficient funds',
            mt5.TRADE_RETCODE_PRICE_CHANGED:  'Price changed',
            mt5.TRADE_RETCODE_REJECT:          'Request rejected',
            mt5.TRADE_RETCODE_INVALID_FILL:   'Invalid filling type',
        }
        reason = error_map.get(result.retcode, 'Unknown error')
        logger.error('Order failed. retcode=%s reason=%s comment=%s',
                     result.retcode, reason, result.comment)
        return False

    logger.info('Order placed. ticket=%s deal=%s volume=%.2f price=%.5f ts=%s',
                result.order, result.deal, result.volume, result.price,
                datetime.fromtimestamp(result.time))
    return True


def main() -> None:
    """Run a quick BUY + SELL smoke test."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    print('MetaTrader 5 Order Testing Script')
    print('=' * 40)

    try:
        print('\nTesting BUY order...')
        if place_test_order('EURUSD', 'BUY', 25.0):
            time.sleep(2)
            print('\nTesting SELL order...')
            place_test_order('GBPUSD', 'SELL', 25.0)
    except KeyboardInterrupt:
        print('\nTesting cancelled by user.')
    except Exception:
        logger.exception('Unexpected error during testing.')
    finally:
        mt5.shutdown()
        print('\n' + '=' * 40)
        print('Testing completed.')


if __name__ == '__main__':
    main()