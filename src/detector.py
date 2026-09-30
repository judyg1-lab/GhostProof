import time
from ultralytics import YOLO


class PersonDetector:
    def __init__(
        self,
        model_path="yolo26n.pt",
        confidence_threshold=0.7,
        cooldown_seconds=10
    ):
        self.model = YOLO(model_path)
        self.confidence_threshold = confidence_threshold
        self.cooldown_seconds = cooldown_seconds

        self.last_trigger_time = 0.0


    def detect(self, frame):
        """
        Returns:
            triggered:
                是否觸發 GhostProof

            annotated_frame:
                YOLO 畫框後影像

            max_confidence:
                畫面中最高 person confidence

            cooldown_remaining:
                若目前仍在 cooldown，
                回傳剩餘秒數
        """

        results = self.model.predict(
            source=frame,
            conf=self.confidence_threshold,
            verbose=False
        )

        result = results[0]

        person_detected = False
        max_confidence = 0.0

        if result.boxes is not None:

            for box in result.boxes:

                class_id = int(
                    box.cls[0].item()
                )

                confidence = float(
                    box.conf[0].item()
                )

                class_name = result.names[
                    class_id
                ]

                if class_name == "person":

                    max_confidence = max(
                        max_confidence,
                        confidence
                    )

                    if (
                        confidence
                        >= self.confidence_threshold
                    ):
                        person_detected = True


        current_time = time.time()

        elapsed = (
            current_time
            - self.last_trigger_time
        )

        cooldown_remaining = max(
            0.0,
            self.cooldown_seconds - elapsed
        )


        triggered = False

        if (
            person_detected
            and elapsed >= self.cooldown_seconds
        ):

            triggered = True

            self.last_trigger_time = (
                current_time
            )

            cooldown_remaining = (
                self.cooldown_seconds
            )


        annotated_frame = result.plot()

        return (
            triggered,
            annotated_frame,
            max_confidence,
            cooldown_remaining
        )