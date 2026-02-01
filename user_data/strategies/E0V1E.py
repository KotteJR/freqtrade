from datetime import datetime, timedelta
import talib.abstract as ta
import pandas_ta as pta
from freqtrade.persistence import Trade
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
from freqtrade.strategy import DecimalParameter, IntParameter
from functools import reduce

TMP_HOLD = []

class E0V1E(IStrategy):
    """
    E0V1E Strategy
    
    A simple but effective strategy using RSI, SMA, and CTI indicators.
    - 87% win rate reported by users
    - Faster analysis than NFI (only 6 indicators vs 100+)
    - 5m timeframe
    - Works well with Gate.io
    
    Original creator: ssssi (https://github.com/ssssi/freqtrade_strs)
    """
    
    minimal_roi = {
        "0": 10  # Effectively disabled - uses custom exit
    }
    
    timeframe = '5m'
    process_only_new_candles = True
    startup_candle_count = 120
    
    order_types = {
        'entry': 'market',
        'exit': 'market',
        'emergency_exit': 'market',
        'force_entry': 'market',
        'force_exit': "market",
        'stoploss': 'market',
        'stoploss_on_exchange': False,
        'stoploss_on_exchange_interval': 60,
        'stoploss_on_exchange_market_ratio': 0.99
    }
    
    # Stoploss at -18%
    stoploss = -0.18
    
    # Hyperopt parameters
    is_optimize_32 = False
    buy_rsi_fast_32 = IntParameter(20, 70, default=45, space='buy', optimize=is_optimize_32)
    buy_rsi_32 = IntParameter(15, 50, default=35, space='buy', optimize=is_optimize_32)
    buy_sma15_32 = DecimalParameter(0.900, 1, default=0.961, decimals=3, space='buy', optimize=is_optimize_32)
    buy_cti_32 = DecimalParameter(-1, 0, default=-0.58, decimals=2, space='buy', optimize=is_optimize_32)
    
    sell_fastx = IntParameter(50, 100, default=75, space='sell', optimize=True)
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Calculate indicators - only 6 indicators for fast processing
        """
        # Buy indicators
        dataframe['sma_15'] = ta.SMA(dataframe, timeperiod=15)
        dataframe['cti'] = pta.cti(dataframe["close"], length=20)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['rsi_fast'] = ta.RSI(dataframe, timeperiod=4)
        dataframe['rsi_slow'] = ta.RSI(dataframe, timeperiod=20)
        
        # Sell indicators (Stochastic Fast)
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe['fastk'] = stoch_fast['fastk']
        
        return dataframe
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Entry conditions:
        - RSI slow decreasing (momentum slowing)
        - RSI fast < 45 (not overbought)
        - RSI > 35 (not oversold either - looking for bounce)
        - Price below SMA15 * 0.961 (price dipped below average)
        - CTI < -0.58 (trend indicator showing oversold)
        """
        conditions = []
        dataframe.loc[:, 'enter_tag'] = ''
        
        buy_1 = (
            (dataframe['rsi_slow'] < dataframe['rsi_slow'].shift(1)) &
            (dataframe['rsi_fast'] < self.buy_rsi_fast_32.value) &
            (dataframe['rsi'] > self.buy_rsi_32.value) &
            (dataframe['close'] < dataframe['sma_15'] * self.buy_sma15_32.value) &
            (dataframe['cti'] < self.buy_cti_32.value)
        )
        
        conditions.append(buy_1)
        dataframe.loc[buy_1, 'enter_tag'] += 'buy_1'
        
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'enter_long'] = 1
        
        return dataframe
    
    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        """
        Custom exit logic using Stochastic Fast K:
        - After 3 hours: exit if FastK >= 70 and in profit
        - Anytime: exit if in profit and FastK > 75
        - Loss recovery: hold until -10%, then sell on FastK > 75 when recovering
        """
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        current_candle = dataframe.iloc[-1].squeeze()
        
        # After 3 hours delay, sell if FastK >= 70 and in profit
        if current_time - timedelta(hours=3) > trade.open_date_utc:
            if (current_candle["fastk"] >= 70) and (current_profit >= 0):
                return "fastk_profit_sell_delay"
        
        # Quick profit exit
        if current_profit > 0:
            if current_candle["fastk"] > self.sell_fastx.value:
                return "fastk_profit_sell"
        
        # Loss management - hold if loss > 10%
        if current_profit <= -0.1:
            if trade.id not in TMP_HOLD:
                TMP_HOLD.append(trade.id)
        
        # Sell when recovering from loss
        for i in TMP_HOLD:
            if trade.id == i and current_profit > -0.1:
                if current_candle["fastk"] > self.sell_fastx.value:
                    TMP_HOLD.remove(i)
                    return "fastk_loss_sell"
        
        return None
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit trend - disabled, using custom_exit instead
        """
        dataframe['exit_long'] = 0
        dataframe['exit_tag'] = ''
        return dataframe
