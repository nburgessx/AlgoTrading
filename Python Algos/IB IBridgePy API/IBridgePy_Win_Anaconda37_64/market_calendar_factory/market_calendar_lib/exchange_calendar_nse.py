# -*- coding: utf-8 -*-
"""
Created on Mon Jul 30 07:02:43 2018

@author: ThinkPad
"""

from datetime import time
from pandas.tseries.holiday import (
    Holiday,
    DateOffset,
    MO,
    weekend_to_monday,
    GoodFriday
)
from pytz import timezone

from .market_calendar import MarketCalendar
from pandas.tseries.holiday import AbstractHolidayCalendar

from .us_holidays import Christmas
start = pd.Timestamp('1994-01-01', tz='UTC')
end_base = pd.Timestamp('today', tz='UTC')
end = end_base + pd.Timedelta(days=365)
'''
monday tuesday wednessday thusday friday
0         1     2           3      4
'''
#republic day is fixed in India January 26
republic_day = Holiday(
    'republic_day',
    month=1,
    day=26,
    offset=DateOffset(weekday=MO(-4)),
)


##2018 holiday#13-Feb-2018,TUESDAY
Mahashivratri = Holiday(
    'Mahashivratri',
    month=1,
    day=13,
    offset=DateOffset(weekday=MO(-1)),
)
##2018 holiday#13-Feb-2018,TUESDAY
holi = Holiday(
    'holi',
    month=3,
    day=2,
    offset=DateOffset(weekday=MO(1)),
)
#Mahavir Jayanti: 29-Mar-2018 Thursday
MahavirJayanti = Holiday(
    'MahavirJayanti',
    month=3,
    day=29,
    offset=DateOffset(weekday=MO(3)),
)
''' already added in panda calendar
#GoodFri: 30-Mar-2018Friday
GoodFriday = Holiday(
    'Good Friday',
    month=3,
    day=30,
    offset=DateOffset(weekday=MO(-1)),
)


'''
##01-May-201:MaharastraDay Tuesday
MaharastraDay = Holiday(
    'MaharastraDay',
    month=5,
    day=1,
    offset=DateOffset(weekday=MO(1)),
)
#indipendece day is fixed in India 15th Aug each year 2018 Wednesday
Independenceday = Holiday(
    'Independence day',
    month=8,
    day=15,
    offset=DateOffset(weekday=MO(2)),
)
# #22-Aug-2018:Bakri Id,Wednesday
Bakri_Id = Holiday(
    'Bakri Id',
    month=8,
    day=22,
    offset=DateOffset(weekday=MO(2)),
)
# #13-Sep-2018:Ganesh Chaturthi Thursday
GaneshChaturthi = Holiday(
    'Ganesh Chaturthi',
    month=9,
    day=13,
    offset=DateOffset(weekday=MO(3)),
)
# #20-Sep-2018:Moharram Thursday
Moharram = Holiday(
    'Moharram',
    month=9,
    day=20,
    offset=DateOffset(weekday=MO(-1)),
)
#02-Oct-2018:Mahatma Gandhi Jayanti: Fixed holidayTuesday
MahatmaGandhiJayanti = Holiday(
    'MahatmaGandhiJayanti',
    month=10,
    day=2,
    offset=DateOffset(weekday=MO(2)),
)
#18-Oct-2018:Dasera Thursday
Dasera = Holiday(
    'MahatmaGandhiJayanti',
    month=10,
    day=18,
    offset=DateOffset(weekday=MO(3)),
)
# #07-Nov-2018:Diwali-Laxmi Pujan*  TIMING 6:7:30 Wednesday
DiwaliLaxmiPujan = Holiday(
    'DiwaliLaxmiPujan',
    month=10,
    day=18,
    offset=DateOffset(weekday=MO(2)),
)
#08-Nov-2018:Diwali-Balipratipada Thursday 
DiwaliBalipratipada = Holiday(
    'DiwaliBalipratipada',
    month=10,
    day=18,
    offset=DateOffset(weekday=MO(3)),
)
# #23-Nov-2018 Gurunanak Jayanti  friday
GurunanakJayanti = Holiday(
    'Gurunanak Jayanti',
    month=11,
    day=23,
    offset=DateOffset(weekday=MO(4)),
)

class NSEExchangeCalendar(MarketCalendar):
    """
    Exchange calendar for the National Stock Exchange

    Open Time: 9:15 AM, IST
    Close Time: 3:15 PM, IST

    Regularly-Observed Holidays: 2018
    - Sr. No. Date       Day       Description
      1      26-Jan-2018 Friday    Republic Day 
      2      13-Feb-2018 Tuesday   Mahashivratri 
      3      02-Mar-2018 Friday    Holi 
      4      29-Mar-2018 Thursday  Mahavir Jayanti 
      5      30-Mar-2018 Friday    Good Friday 
      6     01-May-2018  Tuesday   Maharashtra Day 
      7     15-Aug-2018  Wednesday Independence Day 
      8     22-Aug-2018  Wednesday Bakri ID 
      9     13-Sep-2018  Thursday  Ganesh Chaturthi 
      10    20-Sep-2018  Thursday  Moharram 
      11    02-Oct-2018  Tuesday   Mahatama Gandhi Jayanti 
      12    18-Oct-2018  Thursday  Dasera 
      13    07-Nov-2018  Wednesday Diwali-Laxmi Pujan* 
      14    08-Nov-2018  Thursday  Diwali-Balipratipada 
      15    23-Nov-2018  Friday    Gurunanak Jayanti 
      16     25-Dec-2018 Tuesday   Christmas 
    """

    @property
    def name(self):
        return "NSE"

    @property
    def tz(self):
        return timezone('Asia/Kolkata')

    @property
    def open_time(self):
        return time(9, 15)

    @property
    def close_time(self):
        return time(15,30)

    @property
    def regular_holidays(self):
        return AbstractHolidayCalendar(rules=[
            republic_day,
            Mahashivratri,
            holi,
            MahavirJayanti,
            MaharastraDay,
            Independenceday,
            Bakri_Id,
            GaneshChaturthi,
            Moharram,
            MahatmaGandhiJayanti,
            Dasera,
            DiwaliLaxmiPujan,
            DiwaliBalipratipada,
            GurunanakJayanti,
            Christmas,
            GoodFriday
            ])

  