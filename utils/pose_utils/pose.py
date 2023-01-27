import random
import cv2
import mediapipe as mp
from mediapipe.python.solutions.drawing_utils import _normalized_to_pixel_coordinates
import numpy as np

from utils.operation_utils import Operation
from utils.timer_utils import Timer
from utils.drawing_utils import Draw
from utils.pose_utils.const import POSE, PRESENCE_THRESHOLD, VISIBILITY_THRESHOLD
from utils.timer import TestTimer

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)


class Pose():
    """ Base: Pose Class """

    def __init__(self, video_reader) -> None:
        self.video_reader = video_reader
        self.operation = Operation()
        self.pushup_counter = self.plank_counter = self.squat_counter = 0
        self.key_points = self.prev_pose = self.current_pose = None
        self.ang1_tracker = []
        self.ang4_tracker = []
        self.pose_tracker = []
        self.headpoint_tracker = []
        self.width = int(self.video_reader.get_frame_width())
        self.height = int(self.video_reader.get_frame_height())
        self.video_fps = self.video_reader.get_video_fps()
        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.draw = Draw(self.width, self.height)
        self.test_timer = TestTimer("20:22:00")
        self.hour_angle_dict = {
            -90: 12,
            -60: 1,
            -30: 2,
            0: 3,
            30: 4,
            60: 5,
            90: 6,
            120: 7,
            150: 8,
            180: 9,
            -150: 10,
            -120: 11
        }

        self.minute_angle_dict = {
            -90: 00,
            -60: 5,
            -30: 10,
            0: 15,
            30: 20,
            60: 25,
            90: 30,
            120: 35,
            150: 40,
            180: 45,
            -150: 50,
            -120: 55
        }

    def get_keypoints(self, image, pose_result):
        """ Get keypoints """
        key_points = {}
        image_rows, image_cols, _ = image.shape
        for idx, landmark in enumerate(pose_result.pose_landmarks.landmark):
            if ((landmark.HasField('visibility') and landmark.visibility < VISIBILITY_THRESHOLD) or
                    (landmark.HasField('presence') and landmark.presence < PRESENCE_THRESHOLD)):
                continue
            landmark_px = _normalized_to_pixel_coordinates(landmark.x, landmark.y,
                                                           image_cols, image_rows)
            if landmark_px:
                key_points[idx] = landmark_px
        return key_points

    def is_point_in_keypoints(self, str_point):
        """ Check if point is in keypoints """
        if str_point is None:
            return False

        if self.key_points is None:
            return False

        return POSE[str_point] in self.key_points

    def get_point(self, str_point):
        """ Get point from keypoints """
        return self.key_points[POSE[str_point]] if self.is_point_in_keypoints(str_point) else None

    def get_available_point(self, points):
        """
        Get highest priority keypoint from points list.
        i.e. first index is 1st priority, second index is 2nd priority, and so on.
        """
        available_point = None
        for point in points:
            if self.is_point_in_keypoints(point) and available_point is None:
                available_point = self.get_point(point)
                break
        return available_point

    def two_line_angle(self, str_point1, str_point2, str_point3):
        """ Angle between two lines """
        coord1 = self.get_point(str_point1)
        coord2 = self.get_point(str_point2)
        coord3 = self.get_point(str_point3)
        return self.operation.angle(coord1, coord2, coord3)

    def one_line_angle(self, str_point1, str_point2):
        """ Angle of a line """
        coord1 = self.get_point(str_point1)

        if coord1 is None:
            return -1

        coord2 = self.get_point(str_point2)

        if coord2 is None:
            return -1

        return self.operation.angle_of_singleline(coord1, coord2)

    def estimate(self) -> None:
        """ Estimate pose (base function) """
        out = cv2.VideoWriter("output.avi", self.fourcc, self.video_fps, (self.width, self.height))

        while self.video_reader.is_opened():
            image = self.video_reader.read_frame()
            if image is None:
                break

            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.writeable = False
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            image = self.draw.overlay(image)
            image = self.draw.skeleton(image, results)

            self.test_timer.update()

            if self.test_timer.alarm_should_ring:
                self.test_timer.playAlarmSound()

            if results.pose_landmarks is not None:
                self.key_points = self.get_keypoints(image, results)
                self.test_timer.in_frame = True
            else:
                if self.test_timer.has_printed is True and self.test_timer.should_add is True:
                    self.test_timer.addTimeToAlarm()
                self.test_timer.in_frame = False

            l = self.one_line_angle("left_shoulder", "left_wrist")
            hour = self.hour_angle_dict.get(l, self.hour_angle_dict[min(self.hour_angle_dict.keys(), key=lambda k: abs(l - k))])

            if self.test_timer.period == "pm":
                hour += 12

            r = self.one_line_angle("right_shoulder", "right_wrist")
            minute = self.minute_angle_dict.get(r, self.minute_angle_dict[min(self.minute_angle_dict.keys(), key=lambda j: abs(r - j))])

            ll = self.one_line_angle("left_foot_index", "left_ankle")
            if ll is not None and ll != -1 and ll >= 0:
                if self.test_timer.can_set_time:
                    self.test_timer.swapPeriod()
                else:
                    if self.test_timer.alarm_should_ring:
                        self.test_timer.stopAlarm()

            rr = self.one_line_angle("right_foot_index", "right_ankle")
            if rr is not None and rr != -1 and rr >= 0:
                if self.test_timer.can_set_time:
                    self.test_timer.setTimer(hour, minute)
                else:
                    if self.test_timer.alarm_should_ring is not True:
                        self.test_timer.clearTimer()

            image = self.draw.pose_text(image, str(hour) + ":" + str(minute) + self.test_timer.period)

            if self.test_timer.alarm_time != "NONE":
                image = self.draw.actionText(image, "Set timer: " + self.test_timer.alarm_time)

            # When timer is set, left foot to chest = stop timer, able to update timer
            # Allows use of right foot for other functionality

            img = cv2.imread("clock.png", cv2.IMREAD_UNCHANGED)
            img = cv2.resize(img, (self.width, self.height))

            image = np.where((img[..., 3] < 128)[..., None], image, img[..., 0:3])

            out.write(image)
            cv2.imshow('Intractable Clock', image)
            if cv2.waitKey(5) & 0xFF == 27:
                break


        self.video_reader.release()
