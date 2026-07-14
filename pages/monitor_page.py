import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pytest
from utils.logger import get_logger

logger = get_logger("MonitorPage")

class MonitorPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self.long_wait = WebDriverWait(driver, 40)
        
        # Locators based on user instructions
        self.monitor_nav_locator = (By.XPATH, "//a[@href='/monitor']")
        self.monitor_header_locator = (By.XPATH, "//*[normalize-space(text())='Monitor' and contains(@class, 'text-xl')]")
        
        self.data_lakehouse_radio = (By.XPATH, "//label[contains(@class, 'k-radio-label') and contains(@aria-label, 'Data Lakehouse')]")
        
        # Grid elements
        self.domain_name_column = (By.XPATH, "//span[contains(@class, 'k-column-title') and normalize-space(text())='Domain Name']")
        
        # Since Kendo might have multiple search boxes, we'll try to find the one associated with the grid or just the first visible one
        self.search_input_locator = (By.XPATH, "//input[@type='text' and @placeholder='Search' and contains(@class, 'k-input-inner')]")

    def navigate_to_monitor(self):
        try:
            # We assume we are logged in and the side menu is available.
            # First, try to expand 'Observe & Ask' section if it's collapsed
            try:
                observe_ask_section = self.driver.find_element(By.XPATH, "//*[normalize-space(text())='OBSERVE & ASK']")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", observe_ask_section)
                self.driver.execute_script("arguments[0].click();", observe_ask_section)
                time.sleep(1)
            except Exception:
                pass # It might already be expanded or not require clicking
                
            nav_item = self.wait.until(EC.element_to_be_clickable(self.monitor_nav_locator))
            
            # Use JS to click in case it's obscured
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", nav_item)
            self.driver.execute_script("arguments[0].click();", nav_item)
            
            # Wait for URL to change or header to appear
            self.wait.until(EC.url_contains("/monitor"))
            logger.info("Successfully navigated to Monitor module.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not navigate to Monitor section. {e}")

    def select_data_lakehouse_view(self):
        try:
            # Wait for radio button
            radio = self.wait.until(EC.presence_of_element_located(self.data_lakehouse_radio))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
            
            # Click if it's not already selected
            is_checked = self.driver.execute_script("return arguments[0].control.checked;", radio)
            if not is_checked:
                self.driver.execute_script("arguments[0].click();", radio)
                logger.info("Clicked Data Lakehouse radio button.")
            else:
                logger.info("Data Lakehouse view is already selected.")
                
            # Allow time for grid to refresh
            time.sleep(2)
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Data Lakehouse radio button. {e}")

    def search_domain(self, domain_name):
        try:
            # Ensure the Domain Name column is visible to confirm grid is loaded
            self.wait.until(EC.visibility_of_element_located(self.domain_name_column))
            
            # The user says "in drop down box choose that file".
            # Locate search box
            search_box = self.wait.until(EC.visibility_of_element_located(self.search_input_locator))
            search_box.clear()
            search_box.send_keys(domain_name)
            logger.info(f"Entered '{domain_name}' into search field to trigger dropdown.")
            
            # Wait for Kendo popup list to appear and select the exact domain name
            option_locator = (By.XPATH, f"//li[contains(@class, 'k-list-item') and contains(normalize-space(.), '{domain_name}')]")
            option = self.wait.until(EC.element_to_be_clickable(option_locator))
            self.driver.execute_script("arguments[0].click();", option)
            
            logger.info(f"Selected '{domain_name}' from the dropdown box.")
            
            # Give UI time to filter
            time.sleep(2)
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Domain Name from dropdown in Monitor module. {e}")

    def validate_domain_presence(self, domain_name):
        try:
            # After filtering, look for a cell containing this domain name (accounting for icons/spans inside the td)
            domain_cell = (By.XPATH, f"//td[contains(normalize-space(.), '{domain_name}')]")
            self.wait.until(EC.visibility_of_element_located(domain_cell))
            logger.info(f"Domain '{domain_name}' successfully found in the Monitor grid results.")
            return True
        except TimeoutException:
            logger.error(f"Domain '{domain_name}' was NOT found in the Monitor grid results after search.")
            pytest.fail(f"FAIL: Domain '{domain_name}' was not found in the Monitor results grid.")

    def click_task_button(self, domain_name):
        try:
            # Find the row containing the domain name, then locate the button inside its Action cell.
            # Using the exact button classes provided by user, or selecting the 3rd button if there are multiple.
            # To be safe, we look for the button containing an icon or just by index if multiple share the class.
            # Usually Kendo task buttons have a title or an icon. Let's just find the buttons in that row's action cell.
            row_xpath = f"//tr[td[contains(normalize-space(.), '{domain_name}')]]"
            action_cell_xpath = f"{row_xpath}//td[contains(@class, 'action_cell')]"
            
            # The user specifically highlighted this button class:
            button_xpath = f"{action_cell_xpath}//button[contains(@class, 'tbl_action_btn')]"
            
            # Wait for the action cell
            self.wait.until(EC.presence_of_element_located((By.XPATH, action_cell_xpath)))
            
            # Get all action buttons in this row
            buttons = self.driver.find_elements(By.XPATH, button_xpath)
            
            if not buttons:
                pytest.fail(f"FAIL: No action buttons found in the row for domain '{domain_name}'.")
                
            # If there are multiple buttons, the Task button is typically the 3rd one based on standard DataParq UI (list/task icon)
            # We will try to click the 3rd button if available, otherwise the first one that matches the specific class.
            target_button = buttons[2] if len(buttons) >= 3 else buttons[0]
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", target_button)
            time.sleep(1) # wait for scroll
            self.driver.execute_script("arguments[0].click();", target_button)
            
            logger.info(f"Clicked the Task button for domain '{domain_name}'.")
            time.sleep(2) # Give UI time to transition
        except Exception as e:
            pytest.fail(f"FAIL: Could not click the Task button for domain '{domain_name}'. {e}")

    def validate_data_quality_and_lake_status(self):
        import time
        try:
            # Wait for grid headers to load
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'k-column-title') and contains(text(), 'Layer Name')]")))
            
            # Find column indices dynamically
            headers = self.driver.find_elements(By.XPATH, "//th")
            layer_idx = -1
            status_idx = -1
            for i, header in enumerate(headers):
                text = header.get_attribute("textContent").strip()
                if "Layer Name" in text:
                    layer_idx = i + 1
                elif "Status" in text:
                    status_idx = i + 1
                    
            if layer_idx == -1 or status_idx == -1:
                pytest.fail("Could not find 'Layer Name' or 'Status' column in the task details grid.")
                
            layers_to_check = ["dataquality", "datalake"]
            layers_completed = {"dataquality": False, "datalake": False}
            
            start_time = time.time()
            max_wait = 10 * 60 # 10 minutes
            poll_interval = 30
            
            logger.info(f"Starting 10-minute polling for layers {layers_to_check}. Layer Name col: {layer_idx}, Status col: {status_idx}")
            
            while time.time() - start_time < max_wait:
                all_completed = True
                
                for layer in layers_to_check:
                    if layers_completed[layer]:
                        continue
                        
                    # Find the row for this layer
                    row_xpath = f"//tr[td[{layer_idx}][normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='{layer}']]"
                    
                    try:
                        # Attempt to find the specific cell
                        status_cell = self.driver.find_element(By.XPATH, f"{row_xpath}//td[{status_idx}]")
                        status_text = status_cell.text.strip()
                        
                        logger.info(f"Layer '{layer}' current status: {status_text}")
                        
                        if status_text in ["Failed", "Error", "Stopped", "Cancelled"]:
                            pytest.fail(f"Task for layer '{layer}' failed with status: {status_text}")
                        elif status_text == "Completed":
                            layers_completed[layer] = True
                        else:
                            all_completed = False
                    except Exception:
                        # Row might not be spawned yet or grid might be refreshing
                        logger.info(f"Layer '{layer}' not yet visible or grid refreshing. Waiting...")
                        all_completed = False
                        
                if all_completed and all(layers_completed.values()):
                    logger.info("Both 'dataquality' and 'datalake' tasks are Completed successfully!")
                    return True
                    
                time.sleep(poll_interval)
                
            pytest.fail("Timeout reached: Tasks did not complete within 10 minutes.")
        except Exception as e:
            pytest.fail(f"Failed to validate task statuses: {e}")
