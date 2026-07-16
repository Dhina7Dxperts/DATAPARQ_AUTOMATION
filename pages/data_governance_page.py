from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import get_logger
import pytest
import os
import time

logger = get_logger("DataGovernancePage")

class DataGovernancePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        self.long_wait = WebDriverWait(driver, 300)
        
        # Locators
        self.data_governance_menu = (By.XPATH, "//div[contains(@class, 'flex-grow') and normalize-space(text())='Data Governance']")
        self.upload_tab = (By.XPATH, "//div[contains(text(), 'upload')] | //div[contains(translate(text(), 'UPLOAD', 'upload'), 'upload')]")
        self.search_box = (By.XPATH, "//input[@name='search' and @placeholder='Search...']")
        self.select_files_input = (By.XPATH, "//input[@type='file']")
        self.validate_btn = (By.XPATH, "//button[contains(translate(text(), 'validate', 'VALIDATE'), 'VALIDATE')]")
        self.submit_btn = (By.XPATH, "//button[contains(translate(text(), 'submit', 'SUBMIT'), 'SUBMIT')]")
        self.file_validated_msg = (By.XPATH, "//p[normalize-space(text())='File Validated Successfully']")
        self.file_submitted_msg = (By.XPATH, "//p[normalize-space(text())='File Submitted Successfully']")
        # Historical table locator
        self.history_grid = (By.XPATH, "//table | //*[@role='grid']")

    def navigate_to_data_governance(self):
        try:
            menu = self.wait.until(EC.presence_of_element_located(self.data_governance_menu))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", menu)
            self.wait.until(EC.element_to_be_clickable(self.data_governance_menu))
            self.driver.execute_script("arguments[0].click();", menu)
            logger.info("Clicked Data Governance menu.")
        except Exception as e:
            pytest.fail(f"FAIL: Unable to navigate to Data Governance page. {e}")

    def open_upload_section(self):
        try:
            tab = self.wait.until(EC.presence_of_element_located(self.upload_tab))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
            self.wait.until(EC.element_to_be_clickable(self.upload_tab))
            self.driver.execute_script("arguments[0].click();", tab)
            logger.info("Opened Upload section.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not open Upload page. {e}")

    def search_workflow(self, workflow_name):
        try:
            search = self.wait.until(EC.presence_of_element_located(self.search_box))
            search.clear()
            search.send_keys(workflow_name)
            time.sleep(2) # Wait for debounce
            logger.info(f"Searched for workflow: {workflow_name}")
        except Exception as e:
            pytest.fail(f"FAIL: Search field is not visible. {e}")
            
    def validate_workflow_exists(self, workflow_name):
        try:
            workflow_lower = workflow_name.lower()
            workflow_card = (By.XPATH, f"//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{workflow_lower}')]")
            self.wait.until(EC.presence_of_element_located(workflow_card))
            logger.info(f"Workflow '{workflow_name}' found in grid results.")
            return True
        except Exception as e:
            pytest.fail(f"FAIL: Workflow '{workflow_name}' was not found in the grid results. {e}")
            
    def open_workflow(self, workflow_name):
        try:
            workflow_lower = workflow_name.lower()
            workflow_card = (By.XPATH, f"//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{workflow_lower}')]")
            row = self.wait.until(EC.presence_of_element_located(workflow_card))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
            self.wait.until(EC.element_to_be_clickable(workflow_card))
            self.driver.execute_script("arguments[0].click();", row)
            time.sleep(2) # Give UI time to open the upload page
            logger.info(f"Opened workflow: {workflow_name}")
        except Exception as e:
            pytest.fail(f"FAIL: Unable to click/open workflow '{workflow_name}'. {e}")

    def _is_button_disabled(self, element) -> bool:
        classes = element.get_attribute("class") or ""
        class_list = classes.split()
        disabled_attr = element.get_attribute("disabled")
        is_disabled_attr = bool(disabled_attr) and str(disabled_attr).lower() != "false"
        
        return (
            "k-disabled" in class_list
            or "disabled" in class_list
            or "pointer-events-none" in class_list
            or is_disabled_attr
            or element.get_attribute("aria-disabled") == "true"
            or not element.is_enabled()
        )

    def validate_validate_button_disabled(self):
        try:
            # Ensure it is disabled
            btn = self.wait.until(EC.presence_of_element_located(self.validate_btn))
            if not self._is_button_disabled(btn):
                pytest.fail("FAIL: Validate button is enabled before file upload.")
            logger.info("Validate button is disabled before file upload.")
        except Exception as e:
            if "FAIL" not in str(e):
                pytest.fail(f"FAIL: Validate button is enabled before file upload. {e}")
            raise

    def upload_file(self, file_path):
        try:
            # Ensure file exists
            abs_path = os.path.abspath(file_path)
            file_name = os.path.basename(abs_path)
            file_input = self.wait.until(EC.presence_of_element_located(self.select_files_input))
            file_input.send_keys(abs_path)
            logger.info(f"Uploaded file: {abs_path}")
            
            # Verify that file upload completes successfully by waiting for the completion text
            success_text_locator = (By.XPATH, "//*[contains(normalize-space(text()), 'successfully uploaded')]")
            self.long_wait.until(EC.visibility_of_element_located(success_text_locator))
            logger.info("File upload completed successfully.")
        except Exception as e:
            pytest.fail(f"FAIL: File upload failed. {e}")

    def validate_validate_button(self):
        try:
            btn = self.wait.until(EC.presence_of_element_located(self.validate_btn))
            def check_enabled(driver):
                b = driver.find_element(*self.validate_btn)
                return not self._is_button_disabled(b)
            
            self.long_wait.until(check_enabled)
            logger.info("Validate button is enabled.")
        except Exception as e:
            pytest.fail(f"FAIL: Validate button did not become enabled after file upload. {e}")

    def click_validate(self):
        """
        Click the Validate button and dynamically wait for validation to complete.

        Strategy:
        - Waits until the "File successfully uploaded" message is visible.
        - Waits an additional 15 seconds after the upload success message appears
          to allow the UI to fully stabilise before clicking Validate.
        - Polls every 15 seconds for completion signals.
        - Proceeds immediately as soon as validation is detected (no fixed wait).
        - Checks multiple signals: 'Rejected Records' summary, 'File Validated
          Successfully' text, or disappearance of any loading/progress indicator.
        - Logs elapsed time on each poll so the test output shows live progress.
        - Maximum wait is 30 minutes; fails only if timeout is reached.
        """
        try:
            # ── Step 1: Wait for "File successfully uploaded" message ─────────
            upload_success_locator = (By.XPATH, "//*[contains(normalize-space(text()), 'successfully uploaded')]")
            self.long_wait.until(EC.visibility_of_element_located(upload_success_locator))
            logger.info("'File successfully uploaded' message is visible.")

            # ── Step 2: Wait an additional 15 seconds before clicking Validate ─
            logger.info("Waiting 15 seconds before clicking Validate button...")
            time.sleep(15)

            # ── Step 3: Wait for Validate button to be fully enabled ──────────
            def check_enabled(driver):
                b = driver.find_element(*self.validate_btn)
                return not self._is_button_disabled(b)
            self.wait.until(check_enabled)

            btn = self.wait.until(EC.element_to_be_clickable(self.validate_btn))
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("Clicked Validate button. Dynamic polling started (max 30 min, poll every 15 s).")

            # ── Dynamic polling loop ──────────────────────────────────────────
            max_wait      = 30 * 60   # 30 minutes in seconds
            poll_interval = 15        # check every 15 seconds
            start_time    = time.time()

            # XPaths for all known completion signals
            COMPLETION_SIGNALS = [
                # Signal 1: Rejected Records count/summary block appears
                (
                    "Rejected Records summary",
                    "//*[contains(translate(normalize-space(text()),"
                    " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
                    " 'rejected records')]"
                ),
                # Signal 2: Explicit 'File Validated Successfully' message
                (
                    "File Validated Successfully message",
                    "//*[contains(normalize-space(text()), 'File Validated Successfully')]"
                ),
                # Signal 3: Generic validation success banner
                (
                    "Validation success banner",
                    "//*[contains(translate(normalize-space(text()),"
                    " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
                    " 'validation complete') or "
                    " contains(translate(normalize-space(text()),"
                    " 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
                    " 'validated successfully')]"
                ),
            ]

            while True:
                elapsed = time.time() - start_time
                elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

                if elapsed >= max_wait:
                    pytest.fail(
                        f"FAIL: File validation timed out after 30 minutes. "
                        f"No completion signal was detected."
                    )

                # ── Check each completion signal ──────────────────────────────
                completed = False
                for signal_name, xpath in COMPLETION_SIGNALS:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        if elements and any(e.is_displayed() for e in elements):
                            logger.info(
                                f"Validation completed after {elapsed_str}. "
                                f"Signal detected: '{signal_name}'."
                            )
                            completed = True
                            break
                    except Exception as inner_e:
                        logger.debug(f"Transient error while checking '{signal_name}': {inner_e}")

                if completed:
                    return True

                # ── Log progress and wait before next poll ────────────────────
                remaining = max_wait - elapsed
                logger.info(
                    f"Validation in progress... Elapsed: {elapsed_str} | "
                    f"Remaining: {int(remaining // 60)}m {int(remaining % 60)}s. "
                    f"Next check in {poll_interval}s."
                )
                time.sleep(poll_interval)

        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: File validation was not completed successfully. {e}")

    def validate_submit_button_disabled(self):
        try:
            # The button might be disabled OR completely absent from the DOM
            # Use find_elements to avoid a long wait if it's absent
            buttons = self.driver.find_elements(*self.submit_btn)
            if not buttons:
                logger.info("Submit button is not present before validation completes (treated as disabled).")
                return
            
            btn = buttons[0]
            if not self._is_button_disabled(btn):
                pytest.fail("FAIL: Submit button is enabled before validation completes.")
            logger.info("Submit button is disabled before validation completes.")
        except Exception as e:
            if "FAIL" not in str(e):
                pytest.fail(f"FAIL: Submit button is enabled before validation completes. {e}")
            raise

    def validate_submit_button(self):
        try:
            btn = self.wait.until(EC.presence_of_element_located(self.submit_btn))
            def check_enabled(driver):
                b = driver.find_element(*self.submit_btn)
                return not self._is_button_disabled(b)
            self.wait.until(check_enabled)
            logger.info("Submit button is enabled.")
        except Exception as e:
            try:
                b = self.driver.find_element(*self.submit_btn)
                html = b.get_attribute("outerHTML")
                pytest.fail(f"FAIL: Submit button did not become enabled after validation. HTML: {html} | Error: {e}")
            except Exception:
                pytest.fail(f"FAIL: Submit button did not become enabled after validation. {e}")

    def click_submit(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.submit_btn))
            self.driver.execute_script("arguments[0].click();", btn)
            # Wait for success message
            self.long_wait.until(EC.visibility_of_element_located(self.file_submitted_msg))
            logger.info("File Submitted Successfully.")
        except Exception as e:
            pytest.fail(f"FAIL: File submission failed. {e}")

    def validate_historical_upload_status(self):
        try:
            # After submission the history shows a NEW entry with status 'NEW' (processing)
            # or 'COMPLETED' if already done. We accept either as a valid post-submit state.
            # XPath: any element that contains 'NEW' or 'COMPLETED' near the history section
            status_locator = (
                By.XPATH,
                "//*["
                "contains(translate(normalize-space(text()), 'newcompletd', 'NEWCOMPLETD'), 'NEW') or "
                "contains(translate(normalize-space(text()), 'completed', 'COMPLETED'), 'COMPLETED')"
                "]"
            )
            self.wait.until(EC.visibility_of_element_located(status_locator))
            logger.info("Historical Upload Status was updated (entry visible with NEW or COMPLETED state).")
        except Exception as e:
            pytest.fail(f"FAIL: Historical Upload Status was not updated after submission. {e}")

    def get_rejected_records_count(self):
        try:
            # Locate the count adjacent to the "Rejected Records" label based on provided HTML
            rejected_label_xpath = "//*[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'rejected records')]"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, rejected_label_xpath)))
            
            count_xpath = rejected_label_xpath + "/preceding-sibling::div"
            rejected_elem = self.driver.find_element(By.XPATH, count_xpath)
            count_str = rejected_elem.text.strip()
            logger.info(f"UI Rejected Records Count captured: {count_str}")
            
            return int(count_str)
        except Exception as e:
            pytest.fail(f"FAIL: Could not retrieve Rejected Records count from UI. {e}")

    def click_download_rejected(self):
        try:
            # Find the <a> tag that contains the 'Download Rejected' text
            download_xpath = "//a[.//div[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'download rejected')]]"
            download_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, download_xpath)))
            
            # Extract the href to guarantee download without relying on JS click bubbling
            href = download_btn.get_attribute("href")
            if href:
                logger.info(f"Triggering download directly via href: {href}")
                self.driver.get(href)
            else:
                logger.info("No href found, falling back to native click.")
                self.wait.until(EC.element_to_be_clickable((By.XPATH, download_xpath))).click()
                
            logger.info("Clicked 'Download Rejected' button.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Download Rejected button. {e}")
