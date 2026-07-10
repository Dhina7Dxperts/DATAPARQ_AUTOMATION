import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import get_logger
import pytest

logger = get_logger("DataLakehousePage")

class DataLakehousePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)
        self.data_lakehouse_heading = (By.XPATH, "//h4[normalize-space(text())='Data Lakehouse']")
        self.data_lakehouse_desc = (By.XPATH, "//h4[normalize-space(text())='Data Lakehouse']/following::*[contains(text(), 'Connect real data sources, build transformations, and prepare datasets ready for analytics at scale.')]")
        # Find the first Create New button that comes after the Data Lakehouse heading
        self.create_new_locator = (By.XPATH, "//h4[normalize-space(text())='Data Lakehouse']/following::button[.//span[normalize-space(text())='Create New']][1]")
        
        # Tabs for validation
        self.cloud_storage_tab = (By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(text(), 'Cloud Storage')]")
        self.db_warehouse_tab = (By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(text(), 'Database & Warehouse')]")
        self.governance_tab = (By.XPATH, "//div[contains(@class, 'cursor-pointer') and text()='Governance']")
        self.api_tab = (By.XPATH, "//div[contains(@class, 'cursor-pointer') and contains(text(), 'API')]")
        
        self.file_input_locator = (By.CSS_SELECTOR, "input[type='file']")
        self.upload_area_locator = (By.XPATH, "//*[contains(translate(text(), 'UPLOAD', 'upload'), 'upload') or contains(text(), 'Drag and drop')]")
        
        self.next_btn_locator = (By.XPATH, "//span[contains(@class, 'k-button-text') and text()='Next']/ancestor::button | //span[contains(@class, 'k-button-text') and text()='Next']")
        self.success_msg_locator = (By.XPATH, "//*[contains(translate(text(), 'SUCCESS', 'success'), 'success')]")

        # Error locators — only real upload error messages, NOT sidebar nav items
        # Matches Kendo upload error state, toast notifications, or explicit error text in the main content
        self.error_locator = (By.XPATH, """
            //*[
                contains(@class, 'k-upload-status-failed') or
                contains(@class, 'k-notification-error') or
                contains(@class, 'k-messagebox-error') or
                (
                    (contains(@class, 'toast') or contains(@class, 'alert') or contains(@class, 'notification'))
                    and (
                        contains(translate(., 'INVALID UNSUPPORTED FORMAT ERROR FAILED', 'invalid unsupported format error failed'), 'invalid') or
                        contains(translate(., 'INVALID UNSUPPORTED FORMAT ERROR FAILED', 'invalid unsupported format error failed'), 'unsupported') or
                        contains(translate(., 'INVALID UNSUPPORTED FORMAT ERROR FAILED', 'invalid unsupported format error failed'), 'failed') or
                        contains(translate(., 'INVALID UNSUPPORTED FORMAT ERROR FAILED', 'invalid unsupported format error failed'), 'error')
                    )
                )
            ]
        """)

    def click_create_new(self):
        try:
            # Verify the Data Lakehouse card is visible
            self.wait.until(EC.visibility_of_element_located(self.data_lakehouse_heading))
            # Verify the description
            self.wait.until(EC.visibility_of_element_located(self.data_lakehouse_desc))
            logger.info("Verified Data Lakehouse section and description.")
            
            # Click the Create New button specific to Data Lakehouse
            btn = self.wait.until(EC.element_to_be_clickable(self.create_new_locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("Clicked 'Create New' button in Data Lakehouse section.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not verify Data Lakehouse section or click Create New button. {e}")

    def wait_for_choose_source_page(self):
        try:
            self.wait.until(EC.visibility_of_element_located(self.cloud_storage_tab))
            self.wait.until(EC.visibility_of_element_located(self.db_warehouse_tab))
            self.wait.until(EC.visibility_of_element_located(self.governance_tab))
            self.wait.until(EC.visibility_of_element_located(self.api_tab))
        except Exception as e:
            pytest.fail(f"FAIL: Choose Source page did not load properly or missing tabs. {e}")

    def select_governance(self):
        try:
            self.wait.until(EC.element_to_be_clickable(self.governance_tab)).click()
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Governance tab. {e}")
            
    def wait_for_upload_page(self):
        try:
            self.wait.until(EC.visibility_of_element_located(self.upload_area_locator))
        except Exception as e:
            pytest.fail(f"FAIL: Upload component is not displayed. {e}")

    def upload_file(self, relative_file_path: str):
        absolute_path = os.path.abspath(relative_file_path)
        try:
            file_input = self.driver.find_element(*self.file_input_locator)
            file_input.send_keys(absolute_path)
        except Exception as e:
            pytest.fail(f"FAIL: Could not upload file. {e}")

    def check_for_upload_error(self):
        """Check if the application shows an error after file upload (e.g. unsupported format)."""
        import time
        time.sleep(2)  # brief pause to let error toast/message render
        try:
            error_elements = self.driver.find_elements(*self.error_locator)
            for el in error_elements:
                if el.is_displayed():
                    error_text = el.text.strip()
                    if error_text:
                        logger.error(f"Upload error detected: {error_text}")
                        pytest.fail(
                            f"FAIL: Application showed an error after file upload. "
                            f"The file format may be unsupported. Error: '{error_text}'"
                        )
        except Exception as e:
            # If pytest.fail was raised inside, re-raise it
            if "FAIL:" in str(e):
                raise
            logger.warning(f"Error check encountered an issue: {e}")

    def wait_for_upload_complete(self, file_name: str):
        # Use a long wait to handle large files (e.g., 14MB)
        long_wait = WebDriverWait(self.driver, 120)

        # Step 1: Wait for any upload progress/spinner to disappear
        try:
            spinner_locator = (By.XPATH, "//*[contains(@class, 'k-loading') or contains(@class, 'spinner') or contains(@class, 'progress')]")
            long_wait.until(EC.invisibility_of_element_located(spinner_locator))
        except Exception:
            pass  # spinner may not exist, continue

        # Step 2: Check for any error message shown by the app (e.g. unsupported file type)
        self.check_for_upload_error()

        # Step 3: Try to confirm filename appears in the UI
        try:
            uploaded_file_display = (By.XPATH, f"//*[contains(translate(text(), '{file_name.upper()}', '{file_name.lower()}'), '{file_name.lower()}')]")
            long_wait.until(EC.visibility_of_element_located(uploaded_file_display))
            logger.info(f"Upload confirmed: '{file_name}' visible in UI.")
        except Exception:
            logger.warning(f"File name '{file_name}' not visible in UI after upload. Proceeding to check Next button.")

        # Step 4: Wait until Next button becomes enabled (upload fully processed)
        # If Next button never enables, it means the upload was rejected (e.g., unsupported xlsx format)
        try:
            long_wait.until(EC.element_to_be_clickable(self.next_btn_locator))
        except Exception:
            # Next button never became enabled — check if a visible error message exists
            visible_error = ""
            try:
                error_elements = self.driver.find_elements(*self.error_locator)
                for el in error_elements:
                    if el.is_displayed() and el.text.strip():
                        visible_error = el.text.strip()
                        break
            except Exception:
                pass
            if visible_error:
                pytest.fail(
                    f"FAIL: File upload was rejected by the application. "
                    f"Error message: '{visible_error}'"
                )
            else:
                pytest.fail(
                    f"FAIL: File upload did not complete — Next button never became enabled. "
                    f"The file format '{os.path.splitext(file_name)[1]}' may not be supported."
                )
            
    def validate_next_button_and_click(self):
        try:
            next_btn = self.driver.find_element(*self.next_btn_locator)
            classes = next_btn.get_attribute("class") or ""
            is_disabled_attr = next_btn.get_attribute("disabled")
            if not next_btn.is_enabled() or "disabled" in classes or is_disabled_attr:
                pytest.fail("FAIL: Next button did not become enabled after successful CSV upload.")
            next_btn.click()
        except Exception as e:
            pytest.fail(f"FAIL: Next button validation or click failed. {e}")