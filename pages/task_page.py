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
        try:
            logger.info(f"Monitoring task execution status for up to {max_wait_seconds/60} minutes...")
            end_time = time.monotonic() + max_wait_seconds
            
            while time.monotonic() < end_time:
                rows = self.driver.find_elements(*self.task_row)
                if not rows:
                    pytest.fail("FAIL: No tasks found during monitoring.")
                    
                all_completed = True
                
                for i, row in enumerate(rows):
                    # Find status badge in this row
                    try:
                        badge = row.find_element(*self.status_badge)
                        status_text = badge.text.strip().lower()
                    except Exception:
                        status_text = "unknown"
                        
                    logger.debug(f"Task {i+1} status: {status_text.capitalize()}")
                    
                    if status_text in ['failed', 'error', 'aborted']:
                        pytest.fail(f"FAIL: Task {i+1} reached terminal failure status: {status_text.capitalize()}")
                        
                    if status_text != 'completed':
                        all_completed = False
                        
                if all_completed:
                    logger.info("All tasks successfully reached COMPLETED status.")
                    return True
                    
                # Wait before polling again
                logger.info(f"Tasks are still executing. Waiting {poll_interval} seconds before next check...")
                time.sleep(poll_interval)
                
            pytest.fail(f"FAIL: Tasks did not complete within the maximum wait time of {max_wait_seconds} seconds.")
        except Exception as e:
            pytest.fail(f"FAIL: Error occurred while monitoring task status: {e}")
