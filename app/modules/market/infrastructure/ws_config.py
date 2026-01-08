DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
]


def get_default_streams() -> list[str]:
    streams = []
    for symbol in DEFAULT_SYMBOLS:
        streams.append(f"{symbol.lower()}@ticker")
    return streams


def get_symbol_ticker_stream(symbol: str) -> str:
    return f"{symbol.lower()}@ticker"


def get_symbol_miniticker_stream(symbol: str) -> str:
    return f"{symbol.lower()}@miniTicker"


def get_symbol_depth_stream(symbol: str, level: int = 20) -> str:
    return f"{symbol.lower()}@depth{level}@100ms"
