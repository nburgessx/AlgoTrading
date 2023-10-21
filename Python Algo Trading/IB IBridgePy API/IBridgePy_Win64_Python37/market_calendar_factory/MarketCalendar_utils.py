from IBridgePy.constants import MarketName
from market_calendar_factory import MarketCalendar
from market_calendar_factory.FakeMarketCalendar import FakeMarketCalendar


def get_marketCalendar(marketName):
    if marketName != MarketName.NONSTOP:
        return MarketCalendar(marketName)
    else:
        return FakeMarketCalendar()
