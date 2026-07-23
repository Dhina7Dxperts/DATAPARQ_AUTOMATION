import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger("ScreenshotManager")


class ScreenshotManager:
    """
    Captures and manages per-step screenshots for a test run.
    Screenshots are saved sequentially as Step_01.png, Step_02.png, etc.
    """

    def __init__(self, driver, test_name: str):
        self.driver = driver
        self.test_name = test_name
        self.run_dir = self._create_run_dir()
        self.screenshots: list[dict] = []  # [{step, path, description}]

    def _create_run_dir(self) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join("reports", "runs", f"{self.test_name}_{timestamp}")
        os.makedirs(run_dir, exist_ok=True)
        return run_dir

    def capture(self, step_number: int, description: str, is_failure: bool = False) -> str:
        """
        Capture a screenshot for a given step.
        Returns absolute path to the saved screenshot.
        """
        prefix = "FAIL" if is_failure else "PASS"
        filename = f"{prefix}_{step_number:02d}.png"
        path = os.path.abspath(os.path.join(self.run_dir, filename))
        try:
            self.driver.save_screenshot(path)
            self.screenshots.append({
                "step": step_number,
                "path": path,
                "description": description,
                "is_failure": is_failure,
            })
            logger.info(f"INFO - Screenshot captured: {filename} | {description}")
        except Exception as e:
            logger.error(f"Failed to capture screenshot for Step {step_number}: {e}")
        return path

    def get_all(self) -> list[dict]:
        return self.screenshots

    def get_run_dir(self) -> str:
        return self.run_dir
