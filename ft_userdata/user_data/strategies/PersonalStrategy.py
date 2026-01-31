# Save as: user_data/strategies/AggroStrategy.py

from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta
from technical import qtpylib

class PersonalStrategy(IStrategy):
    """
    Aggressive but safe strategy based on RSI + Bollinger Bands + EMA
    Designed for 24/7 hands-off trading with multiple pairs
    """
    
    INTERFACE_VERSION = 3
    
    # Timeframe
    timeframe = '5m'
    
    # Can go short? (futures only)
    can_short = False
    
    # ROI - Take profits at these levels
    minimal_roi = {
        "0": 0.04,    # 4% profit immediately
        "30": 0.025,  # 2.5% after 30 min
        "60": 0.015,  # 1.5% after 60 min
        "120": 0.01   # 1% after 2 hours
    }
    
    # Stoploss - Max loss per trade
    stoploss = -0.08  # 8% max loss
    
    # Trailing stop to lock in profits
    trailing_stop = True
    trailing_stop_positive = 0.01  # Start trailing at 1% profit
    trailing_stop_positive_offset = 0.02  # Activate after 2% profit
    trailing_only_offset_is_reached = True
    
    # Only process new candles
    process_only_new_candles = True
    
    # Use exit signals
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    
    # Startup candles needed
    startup_candle_count = 50
    
    # Hyperopt parameters
    buy_rsi = IntParameter(20, 35, default=28, space="buy")
    sell_rsi = IntParameter(65, 85, default=72, space="sell")
    
    # Order types
    order_types = {
        "entry": "limit",
        "exit": "limit", 
        "stoploss": "market",
        "stoploss_on_exchange": False
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # Bollinger Bands
        bollinger = qtpylib.bollinger_bands(dataframe['close'], window=20, stds=2)
        dataframe['bb_lower'] = bollinger['lower']
        dataframe['bb_middle'] = bollinger['mid']
        dataframe['bb_upper'] = bollinger['upper']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
        
        # EMAs for trend
        dataframe['ema_8'] = ta.EMA(dataframe, timeperiod=8)
        dataframe['ema_21'] = ta.EMA(dataframe, timeperiod=21)
        dataframe['ema_50'] = ta.EMA(dataframe, timeperiod=50)
        
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macd_signal'] = macd['macdsignal']
        dataframe['macd_hist'] = macd['macdhist']
        
        # Volume
        dataframe['volume_mean'] = dataframe['volume'].rolling(window=20).mean()
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # RSI oversold
                (dataframe['rsi'] < self.buy_rsi.value) &
                
                # Price near or below lower Bollinger Band
                (dataframe['close'] <= dataframe['bb_lower'] * 1.01) &
                
                # Uptrend: EMA 8 > EMA 21 OR price recovering
                (
                    (dataframe['ema_8'] > dataframe['ema_21']) |
                    (dataframe['close'] > dataframe['close'].shift(1))
                ) &
                
                # MACD turning bullish
                (dataframe['macd_hist'] > dataframe['macd_hist'].shift(1)) &
                
                # Volume confirmation
                (dataframe['volume'] > dataframe['volume_mean'] * 0.5) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'
        ] = 1
        
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # RSI overbought
                (dataframe['rsi'] > self.sell_rsi.value) &
                
                # Price near upper Bollinger Band
                (dataframe['close'] >= dataframe['bb_upper'] * 0.99) &
                
                # MACD turning bearish
                (dataframe['macd_hist'] < dataframe['macd_hist'].shift(1)) &
                
                (dataframe['volume'] > 0)
            ),
            'exit_long'
        ] = 1
        
        return dataframe