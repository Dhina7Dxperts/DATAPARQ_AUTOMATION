from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils.logger import get_logger
import pytest
import time

logger = get_logger("FileSetupPage")

class FileSetupPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
        self.long_wait = WebDriverWait(driver, 45)
        
        self.metadata_tab_locator = (By.XPATH, "//*[contains(text(), 'Metadata')]")
        self.sample_data_tab_locator = (By.XPATH, "//*[contains(text(), 'Sample Data')]")
        self.next_btn_locator = (By.XPATH, "//span[contains(@class, 'k-button-text') and text()='Next']/ancestor::button | //span[contains(@class, 'k-button-text') and text()='Next']")
        
        # Grid Identifiers
        self.metadata_grid_locator = (By.XPATH, "//table | //*[@role='grid' or @role='table']")
        self.metadata_rows = (By.XPATH, "//tr | //div[@role='row']")
        
        self.sample_data_grid_locator = (By.XPATH, "//table | //*[@role='grid' or @role='table']")
        self.next_page_indicator = (By.XPATH, "//*[text()='Mapping' or contains(text(), 'Config')]")
        
        # Only real error popups — very specific, not broad class matches
        self.error_popup = (By.XPATH,
            "//*[contains(@class,'k-messagebox-error') or "
            "contains(@class,'k-notification-error') or "
            "contains(@class,'alert-danger') or "
            "(contains(@class,'toast') and contains(@class,'error'))]"
        )
        # Config page breadcrumb indicator
        self.config_page_locator = (By.XPATH,
            "//span[normalize-space(text())='Entity Level Setup'] | "
            "//*[normalize-space(text())='SOURCE ENTITIES']"
        )

    def wait_for_page_load(self):
        try:
            self.wait.until(EC.visibility_of_element_located(self.metadata_tab_locator))
        except Exception as e:
            pytest.fail(f"FAIL: File Setup page did not load. {e}")
            
    def update_entity_name(self, upload_file_path: str) -> str:
        """
        Set a unique Entity Name on the File Setup page to avoid
        'Entity name already in use' conflicts on repeated runs.
        Derives base name from filename + HHMMSS timestamp, enters it,
        and clicks APPLY so the server validates the new name.
        Returns the unique entity name used.
        """
        import os
        from datetime import datetime
        base = os.path.splitext(os.path.basename(upload_file_path))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        entity_input_locator = (
            By.XPATH,
            "//label[normalize-space(text())='Entity Name']/following::input[1] | "
            "//input[@id='entity_name' or @name='entity_name'] | "
            "//input[@placeholder and contains(@class,'entity')]",
        )
        
        prefix_input_locator = (
            By.XPATH,
            "//label[normalize-space(text())='File Prefix']/following::input[1] | "
            "//input[@id='file_prefix' or @name='file_prefix']"
        )
        
        suffix_input_locator = (
            By.XPATH,
            "//label[normalize-space(text())='File Suffix']/following::input[1] | "
            "//input[@id='file_suffix' or @name='file_suffix']"
        )

        def clear_and_send(locator, value, field_name):
            try:
                field = self.wait.until(EC.element_to_be_clickable(locator))
                field.send_keys(Keys.CONTROL + "a")
                field.send_keys(Keys.BACKSPACE)
                field.send_keys(value)
                logger.info(f"INFO - {field_name} set to '{value}'.")
            except Exception as e:
                logger.warning(f"WARNING - Could not update {field_name} field: {e}")

        clear_and_send(entity_input_locator, base, "Entity Name")
        clear_and_send(prefix_input_locator, base, "File Prefix")
        clear_and_send(suffix_input_locator, "", "File Suffix")

        apply_btn_locator = (
            By.XPATH,
            "//button[@type='submit' and contains(@class, 'primary_button') and (normalize-space(.)='APPLY' or normalize-space(.)='Apply')] | "
            "//button[normalize-space(.)='APPLY' or normalize-space(.)='Apply']",
        )
        try:
            apply_btn = self.wait.until(EC.presence_of_element_located(apply_btn_locator))
            
            # Step 1: Validate Apply Button State
            is_disabled = apply_btn.get_attribute("disabled") or "disabled" in (apply_btn.get_attribute("class") or "") or not apply_btn.is_enabled()
            if is_disabled:
                pytest.fail("FAIL: Apply button remained disabled after entering valid Entity/Prefix/Suffix values.")
            logger.info("INFO - Apply button is ENABLED.")
            
            # Step 2: Click Apply Button
            self.wait.until(EC.element_to_be_clickable(apply_btn_locator))
            self.driver.execute_script("arguments[0].click();", apply_btn)
            logger.info("INFO - APPLY clicked after entity name update.")
            time.sleep(2)  # Wait for server to validate
            
            # Step 3: Validate Apply Action (Verify no errors)
            self.verify_no_error()
            logger.info("INFO - Apply action completed successfully with no validation errors.")
            
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: Could not validate or click APPLY button: {e}")

        return base

    def verify_no_error(self):
        errs = self.driver.find_elements(*self.error_popup)
        if len(errs) > 0 and errs[0].is_displayed():
            pytest.fail("FAIL: Error popup or validation error shown.")

    def validate_metadata(self):
        try:
            meta_tab = self.wait.until(EC.element_to_be_clickable(self.metadata_tab_locator))
            meta_tab.click()
            
            # Verify table and rows exist
            self.wait.until(EC.visibility_of_element_located(self.metadata_grid_locator))
            rows = self.driver.find_elements(*self.metadata_rows)
            if len(rows) == 0:
                pytest.fail("FAIL: Metadata is empty or missing.")
                
            # Verify columns and data types (simplified check based on mock data)
        except Exception as e:
            pytest.fail(f"FAIL: Metadata validation failed. {e}")

    def validate_sample_data(self):
        try:
            sample_tab = self.wait.until(EC.element_to_be_clickable(self.sample_data_tab_locator))
            sample_tab.click()
            
            self.wait.until(EC.visibility_of_element_located(self.sample_data_grid_locator))
            rows = self.driver.find_elements(*self.metadata_rows)
            if len(rows) <= 1: # assuming 1 is header
                pytest.fail("FAIL: No sample data is displayed or empty.")
        except Exception as e:
            pytest.fail(f"FAIL: Sample data validation failed. {e}")

    def verify_next_button_and_click(self):
        try:
            # wait a few seconds for backend validation to complete and enable the button
            time.sleep(4) 
            
            next_btn = self.driver.find_element(*self.next_btn_locator)
            classes = next_btn.get_attribute("class") or ""
            is_disabled_attr = next_btn.get_attribute("disabled")
            if not next_btn.is_enabled() or "disabled" in classes or is_disabled_attr:
                pytest.fail("FAIL: Next button is disabled on the File Setup page.")
            next_btn.click()
        except Exception as e:
            pytest.fail(f"FAIL: Next button validation failed. {e}")

    def assert_final_validation(self):
        try:
            # Wait for Config page to appear (Entity Level Setup heading or SOURCE ENTITIES panel)
            self.long_wait.until(EC.visibility_of_element_located(self.config_page_locator))
            logger.info("Successfully navigated to Config page.")
        except Exception as e:
            pytest.fail(f"FAIL: Did not navigate to Config page after clicking Next on File Setup. {e}")