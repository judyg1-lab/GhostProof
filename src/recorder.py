import cv2
import os
import time
from datetime import datetime


class SegmentRecorder:
    def __init__(
        self,
        output_dir="recordings",
        segment_minutes=20,
        fps=20.0,
        codec="mp4v"
    ):
        self.output_dir = output_dir

        self.segment_seconds = (
            segment_minutes * 60
        )

        self.fps = fps
        self.codec = codec

        self.writer = None
        self.segment_start_time = None
        self.current_path = None

        self.frame_width = None
        self.frame_height = None

        os.makedirs(
            self.output_dir,
            exist_ok=True
        )


    def _create_writer(
        self,
        frame
    ):
        """
        根據目前 frame 建立新的影片檔。
        """

        height, width = frame.shape[:2]

        self.frame_width = width
        self.frame_height = height

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        filename = (
            f"recording_{timestamp}.mp4"
        )

        self.current_path = os.path.join(
            self.output_dir,
            filename
        )

        fourcc = cv2.VideoWriter_fourcc(
            *self.codec
        )

        self.writer = cv2.VideoWriter(
            self.current_path,
            fourcc,
            self.fps,
            (
                self.frame_width,
                self.frame_height
            )
        )

        if not self.writer.isOpened():
            raise RuntimeError(
                "無法建立錄影檔案"
            )

        self.segment_start_time = (
            time.time()
        )

        print(
            f"[REC] 開始錄影："
            f"{self.current_path}"
        )


    def write(
        self,
        frame
    ):
        """
        寫入 frame。

        若超過 segment_seconds，
        自動切換成新的影片。
        """

        if self.writer is None:

            self._create_writer(
                frame
            )


        elapsed = (
            time.time()
            - self.segment_start_time
        )


        # 到達分段時間
        if elapsed >= self.segment_seconds:

            self.rotate(
                frame
            )


        self.writer.write(
            frame
        )


    def rotate(
        self,
        frame
    ):
        """
        關閉目前影片並開始下一段。
        """

        if self.writer is not None:

            old_path = (
                self.current_path
            )

            self.writer.release()

            print(
                f"[REC] 分段完成："
                f"{old_path}"
            )


        self.writer = None

        self._create_writer(
            frame
        )


    def close(
        self
    ):
        """
        程式結束時安全關閉影片。
        """

        if self.writer is not None:

            path = self.current_path

            self.writer.release()

            self.writer = None

            print(
                f"[REC] 錄影已儲存："
                f"{path}"
            )