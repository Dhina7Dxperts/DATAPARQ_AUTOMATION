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

    def search_and_select_workflow(self, workflow_name):
        try:
            # Search
            search = self.wait.until(EC.presence_of_element_located(self.search_box))
            search.clear()
            search.send_keys(workflow_name)
            time.sleep(2) # Wait for debounce
            
            # The result appears as a card, not a table row. Locate by workflow name text.
            workflow_card = (By.XPATH, f"//*[normalize-space(text())='{workflow_name}']")
            row = self.wait.until(EC.presence_of_element_located(workflow_card))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row)
            self.wait.until(EC.element_to_be_clickable(workflow_card))
            self.driver.execute_script("arguments[0].click();", row)
            logger.info(f"Selected workflow: {workflow_name}")
        except Exception as e:
            pytest.fail(f"FAIL: Search field is not visible or Workflow created in TC1 was not found or Unable to select workflow. {e}")

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
            
            self.wait.until(check_enabled)
            logger.info("Validate button is enabled.")
        except Exception as e:
            pytest.fail(f"FAIL: Validate button did not become enabled after file upload. {e}")

    def click_validate(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.validate_btn))
            self.driver.execute_script("arguments[0].click();", btn)
            # Wait for success message
            self.long_wait.until(EC.visibility_of_element_located(self.file_validated_msg))
            logger.info("File Validated Successfully.")
        except Exception as e:
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

