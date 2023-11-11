# coding=utf-8
import datetime as dt
import time

from BasicPyLib.Printable import PrintableII
from IBridgePy.constants import TimeConcept
from sys import exit


class Repeater(object):
    def __init__(self, repeaterBaseFreq, getTimeNowFuncGlobal, stopFuncGlobal=(lambda x: False), log=None):
        """
        To schedule events
        :param repeaterBaseFreq: repeater will run based on this base frequency, unit=second, fraction of seconds are OK. In backtest mode, it should be set to zero because the simulated time will come in by TimeGenerator and no delay is appropriate.
        :param getTimeNowFuncGlobal: a function can return time. timezone is not used in repeater. The user of the repeater should consider timezone when supplying a time generator because spot-time event is related to timezone.
        :param stopFuncGlobal: a function can return a boolean. True=stop repeater
        :param log: system log
        """
        self.spotEvents = {}  # hold all events scheduled at spot time
        self.repeatedEvents = {}  # hold all repeated events
        self.conceptEvents = {}  # new day, new hour etc
        self.hftEvents = []  # hold all events that need to run every base repeat
        self.getTimeNowFuncGlobal = getTimeNowFuncGlobal
        self.stopFuncGlobal = stopFuncGlobal
        self.timePrevious = dt.datetime(1970, 12, 31, 23, 59, 59)
        self.repeaterBaseFreq = repeaterBaseFreq
        self._log = log

    def schedule_event(self, event):
        if isinstance(event, Event.SpotTimeEvent):
            self._spot_time_scheduler(event)
        elif isinstance(event, Event.RepeatedEvent):
            if event.freq != 0:
                self._repeated_scheduler(event)
        elif isinstance(event, Event.ConceptEvent):
            self._concept_scheduler(event)
        elif isinstance(event, Event.HftEvent):
            self.hftEvents.append(event)
        else:
            self._log.error(__name__ + '::schedule_event: Exit, cannot handle event=%s' % (event,))
            exit()

    def _repeated_scheduler(self, repeatedEvent):
        """
        Change repeated events to spot-time events, Then, add it to repeaterEngine which only process spot-time events
        :param repeatedEvent:
        :return:
        """
        if repeatedEvent.freq not in self.repeatedEvents:
            self.repeatedEvents[repeatedEvent.freq] = []
        self.repeatedEvents[repeatedEvent.freq].append(repeatedEvent)

    def _concept_scheduler(self, conceptEvent):
        """
        Change repeated events to spot-time events, Then, add it to repeaterEngine which only process spot-time events
        :param conceptEvent:
        :return:
        """
        if conceptEvent.concept not in self.conceptEvents:
            self.conceptEvents[conceptEvent.concept] = []
        self.conceptEvents[conceptEvent.concept].append(conceptEvent)

    def _spot_time_scheduler(self, singleEvent):
        spotTime = singleEvent.onHour * 60 * 60 + singleEvent.onMinute * 60 + singleEvent.onSecond
        if spotTime not in self.spotEvents:
            self.spotEvents[spotTime] = []
        self.spotEvents[spotTime].append(singleEvent)

    def _reset_hasExecutedToday_flag_for_spot_time_events(self):
        for spotTime in self.spotEvents:
            for event in self.spotEvents[spotTime]:
                event.hadExecutedToday = False

    def repeat(self):
        self._log.debug(__name__ + '::repeat: spotEvents=%s' % (self.spotEvents,))
        self._log.debug(__name__ + '::repeat: repeatedEvents=%s' % (self.repeatedEvents,))
        self._log.debug(__name__ + '::repeat: conceptEvents=%s' % (self.conceptEvents,))
        self._log.debug(__name__ + '::repeat: hftEvents=%s' % (self.hftEvents,))

        while True:
            try:
                self._log.notset(__name__ + '::repeat: ####    START a new datetime    ####')
                timeNow = self.getTimeNowFuncGlobal()
                self._log.notset(__name__ + '::repeat: timeNow=%s' % (timeNow,))
            except StopIteration:
                break

            if self.stopFuncGlobal(timeNow):
                self._log.notset(__name__ + '::repeat: timeNow=%s not go through repeat engine')
                break

            # Must process NEW DAY first to decide if today is a trading day.
            # Otherwise, other events will not be triggered because timeNow is not with the current trading hours
            if timeNow.day != self.timePrevious.day:
                self._reset_hasExecutedToday_flag_for_spot_time_events()
                if TimeConcept.NEW_DAY in self.conceptEvents:
                    for event in self.conceptEvents[TimeConcept.NEW_DAY]:
                        if event.passFunc(timeNow):
                            event.do_something(timeNow)
            if timeNow.hour != self.timePrevious.hour:
                if TimeConcept.NEW_HOUR in self.conceptEvents:
                    for event in self.conceptEvents[TimeConcept.NEW_HOUR]:
                        if event.passFunc(timeNow):
                            event.do_something(timeNow)

            # print(__name__, timeNow)
            # handle repeated Events
            currentHourMinuteSeconds = timeNow.hour * 60 * 60 + timeNow.minute * 60 + timeNow.second
            # If a new time comes in, check repeatedEvents
            if timeNow.second != self.timePrevious.second or timeNow.minute != self.timePrevious.minute \
                    or timeNow.hour != self.timePrevious.hour or timeNow.day != self.timePrevious.day:
                for freq in self.repeatedEvents:
                    if currentHourMinuteSeconds % freq == 0:
                        # print('repeat _freq=%s %s' % (freq, currentHourMinuteSeconds))
                        for event in self.repeatedEvents[freq]:
                            # print(event.passFunc, timeNow, event.passFunc(timeNow))
                            if event.passFunc(timeNow):
                                event.do_something(timeNow)

            # handle spot-time events, all spot-time events can only run once per day !!!
            # After the event is executed, hasExecutedToday is set to True.
            # When a new day comes, reset hasExecutedToday of all events to False
            # timezone of onHour and onMinute is as same as the timezone of the timeNow, which is passed by by invoker
            currentHourMinuteSeconds = timeNow.hour * 60 * 60 + timeNow.minute * 60 + timeNow.second
            if currentHourMinuteSeconds in self.spotEvents:  # some events are scheduled at this spot time
                for event in self.spotEvents[currentHourMinuteSeconds]:
                    if not event.hadExecutedToday:
                        if event.passFunc(timeNow):
                            event.do_something(timeNow)
                            event.hadExecutedToday = True  # set flag after the event is executed today

            # slow down for live mode
            if self.repeaterBaseFreq != 0:
                time.sleep(self.repeaterBaseFreq)
                if self.hftEvents:
                    for event in self.hftEvents:
                        if event.passFunc(timeNow):
                            event.do_something(timeNow)
            self.timePrevious = timeNow


class Event(object):
    def __init__(self):
        pass

    class HftEvent(PrintableII):
        def __init__(self, do_something, passFunc=(lambda x: True)):
            self.type = 'HftEvent'
            self.passFunc = passFunc
            self.do_something = do_something

    class SpotTimeEvent(PrintableII):
        def __init__(self, onHour, onMinute, onSecond, do_something, passFunc=(lambda x: True)):
            self.type = 'SpotTimeEvent'
            self.passFunc = passFunc
            self.do_something = do_something  # !!!!!! do_something must have one input -- datetime
            self.onHour = onHour
            self.onMinute = onMinute
            self.onSecond = onSecond
            self.hadExecutedToday = False

    class RepeatedEvent(PrintableII):
        def __init__(self, freq, do_something, passFunc=(lambda x: True)):
            """

            :param freq: number in seconds !!!
            :param do_something: !!!!!! do_something must have one input -- datetime
            :param passFunc: True = stop repeater
            """
            self.type = 'RepeatedEvent'
            self.freq = freq
            self.do_something = do_something
            self.passFunc = passFunc

    class ConceptEvent(PrintableII):
        def __init__(self, concept, do_something, passFunc=(lambda x: True)):
            """

            :param concept: NEW_DAY, NEW_HOUR
            :param do_something: !!!!!! do_something must have one input -- datetime
            :param passFunc: True = stop repeater
            """
            self.type = 'ConceptEvent'
            self.concept = concept
            self.do_something = do_something
            self.passFunc = passFunc
