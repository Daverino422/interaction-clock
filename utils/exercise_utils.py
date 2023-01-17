import sys

from utils.pose_utils.pose import Pose, Pushup, Plank, Squat, Jumpingjack
from utils.video_reader_utils import VideoReader

class Exercise():
    """ Toplevel class for exercises """
    def __init__(self) -> None:
        self.video_reader = VideoReader(1)

        if self.video_reader.is_opened() is False:
            print("Error File Not Found.")

    def estimate_exercise(self):
        """ Run estimator """
        pose_estimator = getattr(sys.modules[__name__], "Pose")
        pose_estimator = pose_estimator(self.video_reader)
        pose_estimator.estimate()
