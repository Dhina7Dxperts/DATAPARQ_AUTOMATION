from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import get_logger
import pytest

logger = get_logger("DataLakehouseWorkflowPage")

class DataLakehouseWorkflowPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)
        
        # Locators based on user requirements
        self.parq_your_data_nav = (By.XPATH, "//div[contains(@class, 'flex-grow') and contains(text(), 'ParQ Your Data')]")
        
        # Step 2: Data Lakehouse View All
        self.dl_section_view_all = (By.XPATH, "//div[contains(@class, 'grid-col') and contains(., 'Data Lakehouse') and not(contains(., 'Sandbox'))]//button[contains(@class, 'button-primary-outline') and contains(translate(., 'VIEW ALL', 'view all'), 'view all')]")
        
        # Step 3: Create New
        self.create_new_btn = (By.XPATH, "//button[contains(., 'Create New') or contains(., 'CREATE NEW')]")
        
        # Step 4: Data Lakehouse Tab
        self.dl_tab = (By.XPATH, "//div[contains(@class, 'capitalize text-sm') and contains(text(), 'Data Lakehouse')]")
        
        # Step 5: Search Box
        self.search_box = (By.CSS_SELECTOR, "input.k-input-inner[placeholder='Search']")
        
        # Step 6: Grid
        self.grid_container = (By.CSS_SELECTOR, "div.k-grid-container")
        
        # New Steps 6-13: Business DQ Rule
        self.add_modify_rules_btn = (By.CSS_SELECTOR, "button.primary_button.h-9.w-full.justify-center")
        self.dq_rule_dropdown = (By.CSS_SELECTOR, "#dq_rule")
        self.dq_action_dropdown = (By.CSS_SELECTOR, "#dq_action")
        self.notification_checkbox = (By.CSS_SELECTOR, "label.k-checkbox-label[for='notification']")
        self.attribute_dropdown = (By.CSS_SELECTOR, "span.custom_dq_validation_field")
        self.operator_dropdown = (By.CSS_SELECTOR, "span[id^='busdq_comparision_operator_'] button.k-input-button")
        self.attribute_value_input = (By.CSS_SELECTOR, "input[id^='busdq_comparision_input_']")
        self.create_rule_btn = (By.CSS_SELECTOR, "button[type='submit'].bg-brand-2")
        
    def navigate_to_parq_your_data(self):
        try:
            self.wait.until(EC.element_to_be_clickable(self.parq_your_data_nav)).click()
            logger.info("Clicked on ParQ Your Data module.")
        except Exception as e:
            pytest.fail(f"Failed to navigate to ParQ Your Data: {e}")
            
    def click_view_all_data_lakehouse(self):
        import time
        from selenium.webdriver.common.action_chains import ActionChains
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.dl_section_view_all))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            
            click_success = False
            for _ in range(5):
                time.sleep(1)
                try:
                    btn.click()
                    click_success = True
                    break
                except Exception as e:
                    logger.warning(f"Standard click attempt failed.")
                    
            if not click_success:
                logger.warning("All standard click attempts failed, trying ActionChains.")
                try:
                    ActionChains(self.driver).move_to_element(btn).click().perform()
                except Exception as e2:
                    logger.warning(f"ActionChains click failed, falling back to JS click.")
                    self.driver.execute_script("arguments[0].click();", btn)
                    
            logger.info("Clicked View All in Data Lakehouse section.")
        except Exception as e:
            pytest.fail(f"Failed to click View All in Data Lakehouse section: {e}")
            
    def click_create_new(self):
        import time
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.create_new_btn))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            time.sleep(1)
            try:
                btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", btn)
            logger.info("Clicked Create New button.")
        except Exception as e:
            pytest.fail(f"Failed to click Create New button: {e}")
            
    def click_data_lakehouse_tab(self):
        try:
            tab = self.wait.until(EC.element_to_be_clickable(self.dl_tab))
            self.driver.execute_script("arguments[0].click();", tab)
            logger.info("Clicked Data Lakehouse tab.")
        except Exception as e:
            pytest.fail(f"Failed to click Data Lakehouse tab: {e}")
            
    def search_workflow(self, workflow_name):
        import time
        from selenium.webdriver.common.keys import Keys
        from selenium.common.exceptions import StaleElementReferenceException
        try:
            # Wait for any potential spinner to clear before searching
            try:
                spinner_xpath = "//*[contains(@class, 'k-loading-mask') or contains(@class, 'spinner') or contains(@class, 'loader')]"
                WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, spinner_xpath)))
                WebDriverWait(self.driver, 60).until(EC.invisibility_of_element_located((By.XPATH, spinner_xpath)))
            except Exception:
                pass
                
            long_wait = WebDriverWait(self.driver, 30)
            
            search_box_locators = [
                self.search_box,
                (By.XPATH, "//input[@placeholder='Search' or @placeholder='search']"),
                (By.XPATH, "//input[contains(@class,'k-input-inner')]"),
                (By.XPATH, "//input[@type='search']"),
                (By.XPATH, "//input[@type='text'][contains(@class,'k-input')]")
            ]
            
            for attempt in range(3):
                try:
                    search_input = None
                    for loc in search_box_locators:
                        try:
                            search_input = long_wait.until(EC.element_to_be_clickable(loc))
                            if search_input:
                                break
                        except Exception:
                            continue
                            
                    if not search_input:
                        raise Exception("Search box could not be found with any locator.")
                        
                    self.driver.execute_script("arguments[0].click();", search_input)
                    self.driver.execute_script("arguments[0].value = '';", search_input)
                    search_input.clear()
                    search_input.send_keys(workflow_name)
                    time.sleep(1) # wait for dropdown
                    
                    # Re-locate to prevent StaleElementReferenceException
                    search_input = long_wait.until(EC.element_to_be_clickable(loc))
                    search_input.send_keys(Keys.ENTER) # press enter to close dropdown and filter grid
                    time.sleep(2) # wait for grid to update
                    break
                except StaleElementReferenceException:
                    if attempt == 2:
                        raise
                    time.sleep(1)
            logger.info(f"Searched for workflow: {workflow_name}")
        except Exception as e:
            pytest.fail(f"Failed to search for workflow: {e}")
            
    def validate_workflow_presence(self, workflow_name):
        try:
            self.wait.until(EC.visibility_of_element_located(self.grid_container))
            # verify workflow name exists in the grid
            workflow_locator = (By.XPATH, f"//div[contains(@class, 'k-grid-container')]//*[contains(text(), '{workflow_name}')]")
            self.wait.until(EC.visibility_of_element_located(workflow_locator))
            logger.info(f"Workflow '{workflow_name}' found in grid.")
        except Exception as e:
            pytest.fail(f"Workflow '{workflow_name}' not found in grid: {e}")
            
    def click_profile_icon_for_workflow(self, workflow_name):
        import time
        from selenium.common.exceptions import StaleElementReferenceException
        from selenium.webdriver.common.action_chains import ActionChains
        try:
            # Wait for grid to settle after search
            time.sleep(1.5)
            # Find the exact row containing the workflow name, then find the 2nd action button (Profile)
            profile_btn_locator = (By.XPATH, f"(//td[contains(., '{workflow_name}')]/ancestor::tr//button[contains(@class, 'tbl_action_btn')])[2]")
            
            for _ in range(3):
                try:
                    btn = self.wait.until(EC.element_to_be_clickable(profile_btn_locator))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.5)
                    
                    click_success = False
                    for _ in range(5):
                        try:
                            btn.click()
                            click_success = True
                            break
                        except Exception:
                            time.sleep(1)
                            
                    if not click_success:
                        try:
                            ActionChains(self.driver).move_to_element(btn).click().perform()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", btn)
                            
                    logger.info(f"Clicked profile icon for workflow '{workflow_name}'.")
                    
                    # Ensure the correct flow details page is displayed by waiting for navigation
                    try:
                        self.wait.until(EC.staleness_of(btn))
                        logger.info("Flow details page displayed successfully (navigation confirmed).")
                    except Exception as e:
                        pytest.fail(f"Failed to verify navigation to flow details page: {e}")
                    return
                except StaleElementReferenceException:
                    time.sleep(1)
            
            pytest.fail(f"Failed to click profile icon for workflow '{workflow_name}' due to stale element.")
        except Exception as e:
            pytest.fail(f"Failed to click profile icon for workflow '{workflow_name}': {e}")

    def click_add_modify_rules(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.add_modify_rules_btn))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            btn.click()
            logger.info("Clicked 'Add / Modify Rules' button.")
        except Exception as e:
            pytest.fail(f"Failed to click 'Add / Modify Rules' button: {e}")

    def select_dq_rule(self, rule_name="Business DQ"):
        import time
        try:
            dropdown = self.wait.until(EC.element_to_be_clickable(self.dq_rule_dropdown))
            dropdown.click()
            time.sleep(1)
            # Wait for any element containing the text to be present in the DOM
            option_xpath = f"//*[normalize-space(text())='{rule_name}' or contains(text(), '{rule_name}') and not(self::script)]"
            self.wait.until(EC.presence_of_element_located((By.XPATH, option_xpath)))
            options = self.driver.find_elements(By.XPATH, option_xpath)
            if not options:
                pytest.fail(f"Option '{rule_name}' not found in the DOM using permissive XPath.")
            
            # Force click the first one using JavaScript since Selenium is_displayed() often fails on Kendo popups
            self.driver.execute_script("arguments[0].click();", options[0])
            logger.info(f"Selected DQ Rule: {rule_name}")
        except Exception as e:
            pytest.fail(f"Failed to select DQ Rule '{rule_name}': {e}")

    def select_dq_action(self, action_name="Rejection"):
        import time
        try:
            dropdown = self.wait.until(EC.element_to_be_clickable(self.dq_action_dropdown))
            dropdown.click()
            time.sleep(1)
            option_xpath = f"//*[normalize-space(text())='{action_name}' or contains(text(), '{action_name}') and not(self::script)]"
            self.wait.until(EC.presence_of_element_located((By.XPATH, option_xpath)))
            options = self.driver.find_elements(By.XPATH, option_xpath)
            if not options:
                pytest.fail(f"Option '{action_name}' not found in the DOM using permissive XPath.")
                
            self.driver.execute_script("arguments[0].click();", options[0])
            logger.info(f"Selected DQ Action: {action_name}")
        except Exception as e:
            pytest.fail(f"Failed to select DQ Action '{action_name}': {e}")

    def enable_notification(self):
        try:
            checkbox = self.wait.until(EC.presence_of_element_located(self.notification_checkbox))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
            # Ensure it's not already checked if it's an input, but the locator is a label.
            # Clicking the label toggles it.
            checkbox.click()
            logger.info("Enabled Notification checkbox.")
        except Exception as e:
            pytest.fail(f"Failed to enable Notification checkbox: {e}")

    def select_first_attribute(self):
        import time
        try:
            dropdown = self.wait.until(EC.element_to_be_clickable(self.attribute_dropdown))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
            dropdown.click()
            time.sleep(1)
            # Wait for at least one li to appear inside the animation container
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'k-animation-container')]//li")))
            options = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'k-animation-container')]//li")
            for opt in options:
                # We'll just click the first one that is rendered (even if Selenium thinks it's hidden due to animation)
                column_name = opt.get_attribute("innerText") or opt.text
                if column_name and column_name.strip() != "":
                    self.driver.execute_script("arguments[0].click();", opt)
                    logger.info(f"Selected first available attribute: {column_name}")
                    return column_name.strip()
            pytest.fail("Failed to find any attributes in the dropdown list.")
        except Exception as e:
            pytest.fail(f"Failed to select first attribute: {e}")

    def select_operator(self, operator="="):
        import time
        try:
            # wait for operators to load
            time.sleep(1)
            dropdowns = self.wait.until(EC.presence_of_all_elements_located(self.operator_dropdown))
            # There might be multiple k-input-buttons. We'll click the last one or try clicking it until popup opens
            for _ in range(3):
                try:
                    dropdowns = self.wait.until(EC.presence_of_all_elements_located(self.operator_dropdown))
                    clicked_any = False
                    for btn in dropdowns:
                        try:
                            if btn.is_displayed():
                                btn.click()
                                time.sleep(1)
                                # strictly match the exact operator using normalize-space to avoid matching >= or <= when looking for =
                                option_xpath = f"//*[contains(@class, 'popup') or contains(@class, 'list')]//*[normalize-space(text())='{operator}']"
                                self.wait.until(EC.presence_of_element_located((By.XPATH, option_xpath)))
                                options = self.driver.find_elements(By.XPATH, option_xpath)
                                if options:
                                    self.driver.execute_script("arguments[0].click();", options[-1]) # Click the most specific child node
                                    logger.info(f"Selected operator: {operator}")
                                    return
                        except Exception:
                            continue # Try next button or if stale, ignore
                except Exception:
                    time.sleep(1)
                    
            pytest.fail(f"Could not find or interact with operator dropdown to select '{operator}'.")
        except Exception as e:
            pytest.fail(f"Failed to select operator '{operator}': {e}")

    def enter_attribute_value(self, value):
        import time
        try:
            # sometimes entering values in Kendo inputs needs clear and keys
            input_field = self.wait.until(EC.element_to_be_clickable(self.attribute_value_input))
            input_field.clear()
            time.sleep(0.5)
            input_field.send_keys(str(value))
            logger.info(f"Entered attribute value: {value}")
        except Exception as e:
            pytest.fail(f"Failed to enter attribute value '{value}': {e}")

    def click_create_rule(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.create_rule_btn))
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            btn.click()
            logger.info("Clicked Create button for Business DQ rule.")
        except Exception as e:
            pytest.fail(f"Failed to click Create rule button: {e}")
    def click_next_button(self):
        import time
        try:
            time.sleep(1) # wait for any previous modals/spinners to start fading
            # Find all matching Next buttons, and click the visible one (or the last one if visibility is masked by UI overlays)
            next_btns = self.wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "button.primary_button.ml-2.h-8")))
            
            # Filter for displayed buttons
            visible_btns = [btn for btn in next_btns if btn.is_displayed()]
            target_btn = visible_btns[-1] if visible_btns else next_btns[-1]
            
            self.driver.execute_script("arguments[0].click();", target_btn)
            time.sleep(2) # wait for the next page to load
            logger.info("Clicked 'Next' button.")
        except Exception as e:
            pytest.fail(f"Failed to click 'Next' button: {e}")

    def select_business_key(self, column_name):
        import time
        import os
        try:
            # Wait for the Secure page grid to load completely
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'k-column-title') and contains(text(), 'Business Key')]")))
            
            # Proactively dump HTML for the secure page just in case we need to debug the grid structure later
            os.makedirs("reports/html_dumps", exist_ok=True)
            with open("reports/html_dumps/secure_page_grid.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
                
            # First, find the column index for "Business Key" in the grid headers
            # Kendo grid headers are in <th> elements
            headers = self.driver.find_elements(By.XPATH, "//th")
            bk_col_index = -1
            for i, header in enumerate(headers):
                # get_attribute textContent is safer if the element is not fully visible yet
                if "Business Key" in header.get_attribute("textContent"):
                    bk_col_index = i + 1 # XPath is 1-indexed
                    break
                    
            if bk_col_index == -1:
                pytest.fail("Could not find 'Business Key' column header in the grid.")
                
            col_lower = column_name.lower()
            
            # Find the row containing our dynamic column name, and get the specific <td> at the bk_col_index
            # Then find the k-checkbox inside it
            xpath = f"//tr[td[normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'))='{col_lower}']]//td[{bk_col_index}]//input[contains(@class, 'k-checkbox')]"
            
            self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            checkbox = self.driver.find_element(By.XPATH, xpath)
            
            # Use JS click to bypass visibility issues
            self.driver.execute_script("arguments[0].click();", checkbox)
            logger.info(f"Selected Business Key for column: {column_name} at grid column index {bk_col_index}")
        except Exception as e:
            pytest.fail(f"Failed to select Business Key for '{column_name}': {e}")

    def click_save_secure_page(self):
        import time
        try:
            # We use a permissive xpath for the save button since there might be multiple primary_buttons
            save_btn_xpath = "//button[contains(@class, 'primary_button') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save')]"
            save_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, save_btn_xpath)))
            self.driver.execute_script("arguments[0].click();", save_btn)
            time.sleep(2)
            logger.info("Clicked 'Save' button on Secure page.")
        except Exception as e:
            pytest.fail(f"Failed to click 'Save' button: {e}")

    def deploy_pipeline(self):
        import time
        try:
            # Click the Deploy Pipeline button
            deploy_btn_xpath = "//button[contains(@class, 'success_button') and (contains(@name, 'deploy') or contains(text(), 'Deploy Pipeline'))]"
            deploy_btn = self.wait.until(EC.presence_of_element_located((By.XPATH, deploy_btn_xpath)))
            self.driver.execute_script("arguments[0].click();", deploy_btn)
            logger.info("Clicked 'Deploy Pipeline' button. Waiting up to 15 minutes for deployment to finish...")
            
            # Start polling for success/error
            start_time = time.time()
            max_wait = 15 * 60 # 15 minutes max
            
            # Allow a few seconds for the initial "deployment started" toast to appear and clear
            time.sleep(5)
            
            while time.time() - start_time < max_wait:
                # Check for toast notifications and alert banners
                toasts = self.driver.find_elements(By.CSS_SELECTOR, ".Toastify__toast-body, .k-notification-content, .toast-message, div[role='alert']")
                for toast in toasts:
                    toast_text = toast.text.lower()
                    if "success" in toast_text and ("deploy" in toast_text or "complete" in toast_text):
                        logger.info(f"Deployment success notification found: {toast.text}")
                        return True
                    if "fail" in toast_text or "error" in toast_text:
                        if "deploy" in toast_text:
                            pytest.fail(f"Deployment error notification found: {toast.text}")
                
                # Check page body for broader status text (in case there's an inline status label rather than a toast)
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                if "deployment completed successfully" in page_text or "pipeline deployed successfully" in page_text:
                    logger.info("Deployment successful text found on page.")
                    return True
                if "deployment failed" in page_text or "failed to deploy" in page_text:
                    pytest.fail("Deployment failure text found on page.")
                    
                time.sleep(15) # Poll every 15 seconds
                
            pytest.fail("Deployment timed out after 15 minutes. Success/Error message was never detected.")
        except Exception as e:
            pytest.fail(f"Failed during deployment process: {e}")
