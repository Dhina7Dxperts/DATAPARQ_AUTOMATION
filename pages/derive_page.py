import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import get_logger
import pytest

logger = get_logger("DerivePage")

class DerivePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self.long_wait = WebDriverWait(driver, 60)
        
        self.derive_menu_locator = (By.XPATH, "//div[normalize-space(text())='Derive'] | //span[normalize-space(text())='Derive'] | //a[contains(., 'Derive')]")
        self.search_box = (By.XPATH, "//input[@name='search' and @placeholder='Search...']")
        self.new_derive_btn = (By.XPATH, "//button[contains(normalize-space(.), 'New Derive')]")
        self.entity_name_input = (By.ID, "entity_name")
        self.add_new_source_btn = (By.XPATH, "//span[normalize-space(text())='ADD NEW SOURCE']")
        self.next_btn_modal = (By.XPATH, "//form//button[@type='submit' and contains(translate(normalize-space(.), 'NEXT', 'next'), 'next')]")
        self.ps_checkbox = (By.XPATH, "//input[@id='primary_source_1']")
        self.draw_diagram_btn = (By.XPATH, "//button[contains(translate(normalize-space(.), 'DRAW DIAGRAM', 'draw diagram'), 'draw diagram')]")

    def click_derive_module(self):
        try:
            time.sleep(2)
            el = self.wait.until(EC.element_to_be_clickable(self.derive_menu_locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            self.driver.execute_script("arguments[0].click();", el)
            logger.info("INFO - Clicked on Derive module in sidebar.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Derive module. {e}")

    def verify_derive_page_opened(self):
        try:
            self.wait.until(EC.visibility_of_element_located(self.search_box))
            logger.info("INFO - Derive page opened successfully.")
        except Exception as e:
            pytest.fail(f"FAIL: Derive page did not open. {e}")

    def search_workflow(self, workflow_name: str):
        try:
            sb = self.wait.until(EC.element_to_be_clickable(self.search_box))
            self.driver.execute_script("arguments[0].click(); arguments[0].value='';", sb)
            sb.clear()
            sb.send_keys(workflow_name)
            time.sleep(2)
            logger.info(f"INFO - Searched for workflow '{workflow_name}'.")
            
            # Wait for grid to update
            grid_item_xpath = f"//div[contains(@class, 'break-all') and normalize-space(text())='{workflow_name}']"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, grid_item_xpath)))
        except Exception as e:
            pytest.fail(f"FAIL: Could not search or find workflow '{workflow_name}'. {e}")

    def select_workflow_from_grid(self, workflow_name: str):
        try:
            grid_item_xpath = f"//a[.//div[normalize-space(text())='{workflow_name}']]"
            el = self.wait.until(EC.element_to_be_clickable((By.XPATH, grid_item_xpath)))
            self.driver.execute_script("arguments[0].click();", el)
            logger.info(f"INFO - Clicked workflow '{workflow_name}' from grid.")
        except Exception as e:
            pytest.fail(f"FAIL: No matching workflow found for '{workflow_name}'. {e}")
            
    def select_workflow_and_create_derive(self, workflow_name: str):
        import time
        from selenium.common.exceptions import TimeoutException
        
        # Locate the Workflow section on the left panel and click the existing workflow
        workflow_item_xpath = f"//div[contains(@class, 'truncate') and @title='{workflow_name}']"
        try:
            # Wait for the item to appear since the page might still be rendering after Step 3
            el = self.wait.until(EC.element_to_be_clickable((By.XPATH, workflow_item_xpath)))
            self.driver.execute_script("arguments[0].click();", el)
            logger.info(f"INFO - Clicked workflow '{workflow_name}' from the left panel.")
        except TimeoutException:
            pytest.fail("FAIL: No workflow is available to create a derived entity.")
        except Exception as e:
            pytest.fail(f"FAIL: No workflow is available to create a derived entity. {e}")
            
        # Wait until the workflow becomes selected/highlighted
        time.sleep(1.5)  # Allow UI to process selection
        
        # Verify that the '+ New Derive' button becomes enabled
        try:
            btn = self.wait.until(EC.presence_of_element_located(self.new_derive_btn))
            if btn.get_attribute("disabled"):
                pytest.fail("FAIL: New Derive button remains disabled after selecting workflow.")
            
            # Click the '+ New Derive' button
            self.wait.until(EC.element_to_be_clickable(self.new_derive_btn))
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("INFO - Clicked '+ New Derive' button.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not verify and click '+ New Derive' button. {e}")
            
    def verify_workflow_selected(self, workflow_name: str):
        try:
            selected_item_xpath = f"//div[contains(@class, 'truncate') and @title='{workflow_name}']"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, selected_item_xpath)))
            logger.info(f"INFO - Verified workflow '{workflow_name}' appears under selected workflow section.")
        except Exception as e:
            pytest.fail(f"FAIL: Selected workflow '{workflow_name}' not displayed in selected section. {e}")
            
    def click_new_derive(self):
        try:
            btn = self.wait.until(EC.presence_of_element_located(self.new_derive_btn))
            if btn.get_attribute("disabled"):
                pytest.fail("FAIL: New Derive button remains disabled after selecting workflow.")
            
            self.wait.until(EC.element_to_be_clickable(self.new_derive_btn))
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("INFO - Clicked 'New Derive' button.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not click 'New Derive' button. {e}")

    def enter_entity_name(self, entity_name: str):
        try:
            inp = self.wait.until(EC.element_to_be_clickable(self.entity_name_input))
            self.driver.execute_script("arguments[0].click(); arguments[0].value='';", inp)
            inp.clear()
            inp.send_keys(entity_name)
            logger.info(f"INFO - Entered entity name: {entity_name}")
        except Exception as e:
            pytest.fail(f"FAIL: Could not enter entity name. {e}")

    def click_add_new_source(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.add_new_source_btn))
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("INFO - Clicked 'Add New Source'.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not click 'Add New Source'. {e}")

    def select_domain_name_dropdown(self, domain_name: str):
        try:
            # Target the Domain Name dropdown using the specific label ID provided by the user
            self.driver.execute_script("""
                var label = document.querySelector('label#domain_name_label');
                if (label) {
                    var sibling = label.nextElementSibling;
                    if (sibling) {
                        var picker = sibling.querySelector('.k-dropdownlist, .k-picker, button, .k-input-button');
                        if (picker) { 
                            picker.scrollIntoView({block:'center'});
                            picker.click();
                        }
                    }
                }
            """)
            time.sleep(1.5)
            
            # Select the exact domain name from the popup list
            self.driver.execute_script(f"""
                var popups = document.querySelectorAll('.k-popup, .k-animation-container, .k-list-container');
                for (var popup of popups) {{
                    if (popup.style.display !== 'none' || popup.offsetParent !== null) {{
                        var items = popup.querySelectorAll('[role="option"], .k-item');
                        for (var item of items) {{
                            var text = item.textContent.trim().toLowerCase();
                            if (text === '{domain_name.lower()}') {{
                                item.scrollIntoView({{block:'center'}});
                                item.click();
                                return;
                            }}
                        }}
                    }}
                }}
            """)
            logger.info(f"INFO - Selected '{domain_name}' from the Domain Name dropdown successfully.")
            time.sleep(0.5)
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Domain Name from dropdown. {e}")

    def select_workflow_name_dropdown(self, workflow_name: str):
        try:
            # Target the Workflow Name dropdown using the specific label ID provided by the user
            self.driver.execute_script("""
                var label = document.querySelector('label#schedule_name_label');
                if (label) {
                    var sibling = label.nextElementSibling;
                    if (sibling) {
                        var picker = sibling.querySelector('.k-dropdownlist, .k-picker, button, .k-input-button');
                        if (picker) { 
                            picker.scrollIntoView({block:'center'});
                            picker.click();
                        }
                    }
                }
            """)
            time.sleep(1.5)
            
            # Select the exact workflow name from the popup list
            self.driver.execute_script(f"""
                var popups = document.querySelectorAll('.k-popup, .k-animation-container, .k-list-container');
                for (var popup of popups) {{
                    if (popup.style.display !== 'none' || popup.offsetParent !== null) {{
                        var items = popup.querySelectorAll('[role="option"], .k-item');
                        for (var item of items) {{
                            var text = item.textContent.trim().toLowerCase();
                            if (text === '{workflow_name.lower()}') {{
                                item.scrollIntoView({{block:'center'}});
                                item.click();
                                return;
                            }}
                        }}
                    }}
                }}
            """)
            logger.info(f"INFO - Selected '{workflow_name}' from the Workflow Name dropdown successfully.")
            time.sleep(0.5)
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Workflow Name from dropdown. {e}")

    def select_source_entity_dropdown(self):
        try:
            # Target the Source Entity dropdown using the specific label ID provided by the user
            self.driver.execute_script("""
                var label = document.querySelector('label#source_name_label');
                if (label) {
                    var sibling = label.nextElementSibling;
                    if (sibling) {
                        var picker = sibling.querySelector('.k-dropdownlist, .k-picker, button, .k-input-button');
                        if (picker) { 
                            picker.scrollIntoView({block:'center'});
                            picker.click();
                        }
                    }
                }
            """)
            time.sleep(1.5)
            
            # Select the first valid (non-placeholder) source entity option
            self.driver.execute_script("""
                var popups = document.querySelectorAll('.k-popup, .k-animation-container, .k-list-container');
                for (var popup of popups) {
                    if (popup.style.display !== 'none' || popup.offsetParent !== null) {
                        var items = popup.querySelectorAll('[role="option"], .k-item');
                        for (var item of items) {
                            var text = item.textContent.trim().toLowerCase();
                            if (text && !text.includes('please select')) {
                                item.scrollIntoView({block:'center'});
                                item.click();
                                return;
                            }
                        }
                    }
                }
            """)
            logger.info("INFO - Selected the available Source Entity from the dropdown successfully.")
            time.sleep(0.5)
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Source Entity from dropdown. {e}")

    def click_next_modal(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.next_btn_modal))
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("INFO - Clicked Next on Add Source modal.")
            time.sleep(1) 
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Next in modal. {e}")

    def enable_ps(self):
        try:
            cb = self.wait.until(EC.presence_of_element_located(self.ps_checkbox))
            if not cb.is_selected():
                self.driver.execute_script("arguments[0].click();", cb)
                logger.info("INFO - Checked PS checkbox.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not check PS checkbox. {e}")

    def click_draw_diagram(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.draw_diagram_btn))
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("INFO - Clicked Draw Diagram button.")
            time.sleep(5)
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Draw Diagram. {e}")

    def create_column_mapping(self, column_index, check_business_key=False, is_first=False):
        try:
            if not is_first:
                add_new = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(translate(normalize-space(.), 'ADD NEW', 'add new'), 'add new') and contains(@class, 'cursor-pointer')]")))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", add_new)
                time.sleep(1)

            # Select column dropdown
            self.driver.execute_script("""
                var pickers = document.querySelectorAll('span[id^="source_col_"] button.k-input-button, span[id^="source_col_"]');
                if (pickers.length > 0) {
                    pickers[pickers.length - 1].scrollIntoView({block:'center'});
                    pickers[pickers.length - 1].click();
                } else {
                    var fallbackPickers = document.querySelectorAll('.k-dropdownlist, .k-picker');
                    if (fallbackPickers.length > 0) {
                        fallbackPickers[fallbackPickers.length - 1].scrollIntoView({block:'center'});
                        fallbackPickers[fallbackPickers.length - 1].click();
                    }
                }
            """)
            time.sleep(1)

            result = self.driver.execute_script(f"""
                var popups = document.querySelectorAll('.k-popup, .k-animation-container, .k-list-container');
                for (var popup of popups) {{
                    if (popup.style.display !== 'none' || popup.offsetParent !== null) {{
                        var items = Array.from(popup.querySelectorAll('[role="option"], .k-item'));
                        items = items.filter(item => item.textContent.trim() !== 'Please Select ...' && item.textContent.trim() !== '');
                        if (items.length >= {column_index}) {{
                            items[{column_index} - 1].scrollIntoView({{block:'center'}});
                            items[{column_index} - 1].click();
                            return 'success';
                        }}
                    }}
                }}
                return 'not found';
            """)
            if result != 'success':
                logger.warning(f"WARNING - JS could not click option index {column_index}, it returned: {result}")
            
            time.sleep(1)

            # Handle Business Key
            bk_checkbox = self.wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='isBusinesskey']")))
            is_checked = self.driver.execute_script("return arguments[0].checked;", bk_checkbox)
            
            if check_business_key and not is_checked:
                self.driver.execute_script("arguments[0].click();", bk_checkbox)
            elif not check_business_key and is_checked:
                self.driver.execute_script("arguments[0].click();", bk_checkbox)

            # Click Create
            create_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(translate(normalize-space(.), 'CREATE', 'create'), 'create')]")))
            self.driver.execute_script("arguments[0].click();", create_btn)
            time.sleep(1)
            logger.info(f"INFO - Mapped Column index {column_index}, Business Key: {check_business_key}")
        except Exception as e:
            pytest.fail(f"FAIL: Could not create column mapping for Column index {column_index}. {e}")

    def save_changes(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(.), 'Save Changes')]")))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
            logger.info("INFO - Clicked Save Changes button.")
            
            success_msg = self.long_wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(translate(., 'SUCCESSFULLY', 'successfully'), 'successfully') or contains(translate(., 'SAVED', 'saved'), 'saved')]")))
            logger.info(f"INFO - Save success message displayed.")
            time.sleep(3)
        except Exception as e:
            pytest.fail(f"FAIL: Could not save changes. {e}")

    def deploy_pipeline(self):
        try:
            time.sleep(5)
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(normalize-space(.), 'Deploy Pipeline')]")))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
            logger.info("INFO - Clicked Deploy Pipeline button.")
            
            success_msg = self.long_wait.until(EC.visibility_of_element_located((By.XPATH, "//*[contains(translate(., 'SUCCESSFULLY', 'successfully'), 'successfully') or contains(translate(., 'DEPLOYED', 'deployed'), 'deployed')]")))
            logger.info(f"INFO - Deploy success message displayed.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not deploy pipeline. {e}")
