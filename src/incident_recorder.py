import cv2
import os
import time
from collections import deque
from datetime import datetime


class IncidentRecorder:
    def __init__(
        self,
        output_dir="events",
        fps=20.0,
        pre_event_seconds=10,
        post_event_seconds=30,
        codec="mp4v"
    ):
        self.output_dir = output_dir
        self.fps = fps

        self.pre_event_seconds = pre_event_seconds
        self.post_event_seconds = post_event_seconds

        self.codec = codec

        self.max_buffer_frames = int(
            self.fps * self.pre_event_seconds
        )

        self.pre_buffer = deque(
            maxlen=self.max_buffer_frames
        )

        self.recording = False

        self.writer = None
        self.event_dir = None
        self.incident_path = None

        self.event_start_time = None

        os.makedirs(
            self.output_dir,
            exist_ok=True
        )


    def add_frame(self, frame):
        """
        每個 Camera frame 都呼叫。

        平常：
            放進 pre-event buffer。

        事件錄影中：
            寫入 incident.mp4。

        如果事件剛完成：
            回傳 event 資訊。
        """

        completed_event = None

        if self.recording:

            self.writer.write(
                frame
            )

            elapsed = (
                time.time()
                - self.event_start_time
            )

            if elapsed >= self.post_event_seconds:

                completed_event = (
                    self.stop_event()
                )

        else:

            self.pre_buffer.append(
                frame.copy()
            )

        return completed_event


    def trigger(
        self,
        frame,
        trigger_source="AI",
        trigger_confidence=None
    ):
        """
        異常事件觸發。

        會把：
        前 10 秒 buffer
        +
        trigger frame
        +
        後 30 秒

        存成 incident.mp4。
        """

        # 已經在錄事件，就不要重複開新事件
        if self.recording:

            return None


        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        event_name = (
            f"event_{timestamp}"
        )

        self.event_dir = os.path.join(
            self.output_dir,
            event_name
        )

        os.makedirs(
            self.event_dir,
            exist_ok=True
        )


        self.incident_path = os.path.join(
            self.event_dir,
            "incident.mp4"
        )


        height, width = frame.shape[:2]


        fourcc = cv2.VideoWriter_fourcc(
            *self.codec
        )


        self.writer = cv2.VideoWriter(
            self.incident_path,
            fourcc,
            self.fps,
            (
                width,
                height
            )
        )


        if not self.writer.isOpened():

            raise RuntimeError(
                "無法建立 incident video"
            )


        # =========================
        # 先寫入前 10 秒
        # =========================

        pre_frame_count = len(
            self.pre_buffer
        )


        for buffered_frame in self.pre_buffer:

            self.writer.write(
                buffered_frame
            )


        # trigger frame
        self.writer.write(
            frame
        )


        self.recording = True

        self.event_start_time = (
            time.time()
        )


        print(
            "\n[INCIDENT] 事件錄影開始"
        )

        print(
            f"[INCIDENT] Event ID : "
            f"{event_name}"
        )

        print(
            f"[INCIDENT] Pre-event frames : "
            f"{pre_frame_count}"
        )

        print(
            f"[INCIDENT] Post-event duration : "
            f"{self.post_event_seconds} sec"
        )

        print(
            f"[INCIDENT] File : "
            f"{self.incident_path}"
        )


        return {
            "event_name":
                event_name,

            "event_dir":
                self.event_dir,

            "incident_path":
                self.incident_path,

            "trigger_source":
                trigger_source,

            "trigger_confidence":
                trigger_confidence
        }


    def stop_event(self):
        """
        完成事件錄影。

        回傳完成事件資訊。
        """

        if not self.recording:
            return None


        if self.writer is not None:

            self.writer.release()


        completed_event = {
            "event_dir":
                self.event_dir,

            "incident_path":
                self.incident_path
        }


        print(
            f"[INCIDENT] 事件錄影完成："
            f"{self.incident_path}"
        )


        self.writer = None
        self.recording = False
        self.event_start_time = None


        self.pre_buffer.clear()


        return completed_event


    def close(self):
        """
        程式關閉時安全完成事件錄影。

        如果當下有事件正在錄製，
        回傳 completed_event，
        讓 main.py 可以繼續執行證據保護。
        """

        if self.recording:

            return self.stop_event()

        return None