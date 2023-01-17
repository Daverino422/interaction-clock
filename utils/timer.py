import datetime
import time
import winsound


class TestTimer:
    def __init__(self, alarm_time):
        self.paused = False
        self.last_time = ""
        self.alarm_time = datetime.datetime.fromtimestamp(time.time() + 60).strftime("%H:%M:%S")
        self.has_printed = False

    def update(self):
        if self.paused is True:
            return self.last_time

        current_time = datetime.datetime.now()
        self.last_time = current_time.strftime("%H:%M:%S")

        if self.last_time == self.alarm_time and self.has_printed is False:
            self.pause()
            self.has_printed = True
            winsound.PlaySound("sound.mp3", winsound.SND_ASYNC)
            print("bedtime for you david, you nonce")
            return self.last_time

    def pause(self):
        self.paused = True

    def unpause(self):
        if self.has_printed is False:
            self.paused = False
