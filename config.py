import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    SYMBOL: str = os.getenv("SYMBOL", "XAUUSDm")
    MT5_MODE: str = os.getenv("MT5_MODE", "direct")
    MT5_BRIDGE_URL: str = os.getenv("MT5_BRIDGE_URL", "http://host.docker.internal:8081")
    WEB_HOST: str = os.getenv("WEB_HOST", "127.0.0.1")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))
    POLL_INTERVAL_MS: int = int(os.getenv("POLL_INTERVAL_MS", "150"))

    # Multi-timeframe
    TF_MACRO: str = "H4"
    TF_CONFIRM: str = "M15"
    TF_EXECUTION: str = "M5"

    # Killzone UTC hours
    LONDON_OPEN_UTC: tuple = (7, 10)
    NY_OPEN_UTC: tuple = (12, 15)
    ASIAN_SESSION_UTC: tuple = (0, 6)

    # Risk parameters
    MIN_RR: float = 2.0
    SWEEP_TOLERANCE_PIPS: float = 1.0
    SL_BUFFER_PIPS: float = 2.0
    MAX_SL_PIPS: float = 15.0

    # Trap parameters
    EMA_PERIOD: int = 200
    ATR_PERIOD: int = 14
    EQL_TOLERANCE_PIPS: float = 1.5
    EQL_MIN_GAP_CANDLES: int = 5
    IFVG_MAX_AGE_CANDLES: int = 20
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0

settings = Settings()
