import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest
from utils.logger import get_logger

logger = get_logger("TaskPage")

class TaskPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        
        # Locators based on user instructions
        self.task_grid_content = (By.XPATH, "//div[contains(@class, 'k-grid-content')]")
        self.task_row = (By.XPATH, "//tr[contains(@class, 'k-master-row')]")
        
        # Individual Task Status Locator
        self.status_badge = (By.XPATH, ".//td[@aria-colindex='3']//div[contains(@class, 'text-sm') and contains(@class, 'capitalize')]")

    def validate_task_count(self):
        try:
            # Wait for grid to load
            self.wait.until(EC.presence_of_element_located(self.task_grid_content))
            
            # Give UI time to render rows
            time.sleep(2)
            
            rows = self.driver.find_elements(*self.task_row)
            count = len(rows)
            
            if count >= 1:
                logger.info(f"Task count validation PASSED: Found {count} tasks.")
                return count
            else:
                pytest.fail("FAIL: Task Count = 0. Expected at least 1 task.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not validate task count. {e}")

    def monitor_task_execution(self, max_wait_seconds=600, poll_interval=30):
        """
        Poll task rows and monitor their status until all reach 'Completed'
        or the timeout is reached.

        Improvements over the previous version:
        - Logs EVERY task's current status on each poll cycle (not just changes).
        - Collects ALL failed/errored tasks before calling pytest.fail,
          so the full picture is visible in the report.
        - Shows elapsed time and remaining time on each poll log line.
        - Handles 'unknown' status gracefully (keeps waiting, not an instant fail).
        """
        try:
            logger.info(
                f"Monitoring task execution for up to "
                f"{max_wait_seconds // 60}m {max_wait_seconds % 60}s "
                f"(poll every {poll_interval}s)..."
            )
            start_time = time.monotonic()
            end_time   = start_time + max_wait_seconds

            TERMINAL_FAIL   = {'failed', 'error', 'aborted', 'cancelled'}
            TERMINAL_SUCCESS = {'completed'}

            while time.monotonic() < end_time:
                elapsed   = time.monotonic() - start_time
                remaining = end_time - time.monotonic()
                elapsed_str   = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"
                remaining_str = f"{int(remaining // 60)}m {int(remaining % 60)}s"

                rows = self.driver.find_elements(*self.task_row)
                if not rows:
                    pytest.fail("FAIL: No task rows found in the task grid during monitoring.")

                all_completed  = True
                failed_tasks   = []

                logger.info(
                    f"─── Poll at {elapsed_str} elapsed "
                    f"| {len(rows)} task(s) | Remaining: {remaining_str} ───"
                )

                for i, row in enumerate(rows):
                    try:
                        badge = row.find_element(*self.status_badge)
                        status_text = badge.text.strip().lower()
                    except Exception:
                        status_text = "unknown"

                    status_display = status_text.capitalize()
                    logger.info(f"  Task {i + 1}: {status_display}")

                    if status_text in TERMINAL_FAIL:
                        failed_tasks.append((i + 1, status_display))

                    if status_text not in TERMINAL_SUCCESS:
                        all_completed = False

                # ── Report all failures at once ───────────────────────────────
                if failed_tasks:
                    fail_summary = ", ".join(
                        f"Task {n} → {s}" for n, s in failed_tasks
                    )
                    pytest.fail(
                        f"FAIL: {len(failed_tasks)} task(s) reached a terminal "
                        f"failure status after {elapsed_str}: [{fail_summary}]. "
                        f"Check the application backend for details."
                    )

                if all_completed:
                    logger.info(
                        f"✅ All {len(rows)} task(s) reached COMPLETED status "
                        f"after {elapsed_str}."
                    )
                    return True

                logger.info(
                    f"Tasks still executing. Next check in {poll_interval}s..."
                )
                time.sleep(poll_interval)

            # ── Timeout ───────────────────────────────────────────────────────
            pytest.fail(
                f"FAIL: Tasks did not complete within the maximum wait time "
                f"of {max_wait_seconds // 60} minutes. "
                f"Last known row count: {len(self.driver.find_elements(*self.task_row))}."
            )
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: Error occurred while monitoring task status: {e}")
