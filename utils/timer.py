import datetime
import time
import winsound


class TestTimer:
    def __init__(self, alarm_time):
        self.paused = False
        self.alarm_time = "NONE"
        self.has_printed = False
        self.period = "am"
        self.period_last_changed = -1
        self.period_cooldown = 5  # time in seconds
        self.alarm_time_last_changed = -1
        self.in_frame = True
        self.should_add = False
        self.has_added = False
        self.can_set_time = True

    def update(self):
        if datetime.datetime.now().strftime("%H:%M:%S") == self.alarm_time and self.has_printed is False:
            self.has_printed = True
            winsound.PlaySound("sound.mp3", winsound.SND_ASYNC)

            if self.in_frame is True:
                self.should_add = True

    def addTimeToAlarm(self):
        if self.has_added is False:
            self.alarm_time = datetime.datetime.fromtimestamp(time.time() + 300).strftime("%H:%M:%S")
            self.has_added = True
            self.has_printed = False
            self.can_set_time = False

    def swapPeriod(self):
        if self.period_last_changed != -1 and (self.period_last_changed + self.period_cooldown) > datetime.datetime.now().timestamp():
            return self.period

        if self.period == "am":
            self.period = "pm"
        else:
            self.period = "am"

        self.period_last_changed = datetime.datetime.now().timestamp()

        return self.period

    def setTimer(self, hour, minute):
        if self.can_set_time is not True:
            return

        if self.alarm_time_last_changed != -1 and (self.alarm_time_last_changed + self.period_cooldown) > datetime.datetime.now().timestamp():
            return

        self.alarm_time = datetime.time(hour, minute).strftime("%H:%M:%S")
        self.alarm_time_last_changed = datetime.datetime.now().timestamp()
