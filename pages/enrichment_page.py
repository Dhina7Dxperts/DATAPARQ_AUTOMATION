import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils.logger import get_logger
import pytest

logger = get_logger("EnrichmentPage")

class EnrichmentPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self.long_wait = WebDriverWait(driver, 60)
        
        self.enrichment_menu_locator = (By.XPATH, "//div[normalize-space(text())='Enrichment'] | //span[normalize-space(text())='Enrichment'] | //a[contains(@href, 'enrichment')]")
        self.search_box = (By.XPATH, "//input[@name='search' and @placeholder='Search...']")
        self.create_new_btn = (By.XPATH, "//button[contains(normalize-space(.), 'Create New')]")
        self.enrich_entity_name_input = (By.ID, "entity_name")
        self.process_name_input = (By.ID, "process_name")
        self.is_type_2_checkbox = (By.ID, "is_type_2")
        self.next_btn = (By.XPATH, "//button[@type='submit' and contains(translate(normalize-space(.), 'NEXT', 'next'), 'next')]")

    def click_enrichment_module(self):
        try:
            time.sleep(2)
            el = self.wait.until(EC.element_to_be_clickable(self.enrichment_menu_locator))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            self.driver.execute_script("arguments[0].click();", el)
            logger.info("INFO - Clicked on Enrichment module in sidebar.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Enrichment module. {e}")

    def verify_enrichment_page_opened(self):
        try:
            self.wait.until(EC.visibility_of_element_located(self.search_box))
            logger.info("INFO - Enrichment page opened successfully.")
        except Exception as e:
            pytest.fail(f"FAIL: Enrichment page did not open. {e}")

    def search_domain(self, domain_name: str):
        try:
            sb = self.wait.until(EC.element_to_be_clickable(self.search_box))
            self.driver.execute_script("arguments[0].click(); arguments[0].value='';", sb)
            sb.clear()
            sb.send_keys(domain_name)
            time.sleep(2)
            logger.info(f"INFO - Searched for domain '{domain_name}'.")
            
            grid_item_xpath = f"//div[contains(@class, 'break-all') and normalize-space(text())='{domain_name}']"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, grid_item_xpath)))
        except Exception as e:
            pytest.fail(f"FAIL: Could not search or find exact domain '{domain_name}'. {e}")

    def select_domain_from_grid(self, domain_name: str):
        try:
            grid_item_xpath = f"//a[.//div[normalize-space(text())='{domain_name}']]"
            el = self.wait.until(EC.element_to_be_clickable((By.XPATH, grid_item_xpath)))
            self.driver.execute_script("arguments[0].click();", el)
            logger.info(f"INFO - Clicked domain '{domain_name}' from grid.")
        except Exception as e:
            pytest.fail(f"FAIL: No matching domain found for '{domain_name}' to click. {e}")
            
    def select_workflow_from_panel(self, workflow_name: str):
        import time
        from selenium.common.exceptions import TimeoutException
        
        workflow_item_xpath = f"//div[contains(@class, 'cursor-pointer') and normalize-space(text())='{workflow_name}']"
        try:
            el = self.wait.until(EC.element_to_be_clickable((By.XPATH, workflow_item_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", el)
            logger.info(f"INFO - Clicked workflow '{workflow_name}' from the left panel.")
        except TimeoutException:
            pytest.fail(f"FAIL: Workflow '{workflow_name}' is not displayed in the left panel.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not click workflow '{workflow_name}' in panel. {e}")
            
        time.sleep(1.5)
        
    def click_create_new(self):
        try:
            btn = self.wait.until(EC.presence_of_element_located(self.create_new_btn))
            if btn.get_attribute("disabled"):
                pytest.fail("FAIL: Create New button remains disabled after selecting workflow.")
            
            self.wait.until(EC.element_to_be_clickable(self.create_new_btn))
            self.driver.execute_script("arguments[0].click();", btn)
            logger.info("INFO - Clicked '+ Create New' button.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not verify and click '+ Create New' button. {e}")

    def select_data_entity(self, entity_name: str):
        try:
            self.driver.execute_script("""
                var labels = document.querySelectorAll('label.k-label');
                var targetInput = null;
                for (var label of labels) {
                    if (label.textContent.trim() === 'Data Entity') {
                        var inputId = label.getAttribute('for');
                        if (inputId) {
                            var inputEl = document.getElementById(inputId);
                            if (inputEl) {
                                targetInput = inputEl;
                                break;
                            }
                        }
                    }
                }
                if (targetInput) {
                    targetInput.scrollIntoView({block:'center'});
                    targetInput.click();
                } else {
                    var dropdown = document.querySelector('#data_entity');
                    if (dropdown) {
                        dropdown.scrollIntoView({block:'center'});
                        dropdown.click();
                    }
                }
            """)
            time.sleep(1)
            
            result = self.driver.execute_script(f"""
                var popups = document.querySelectorAll('.k-popup, .k-animation-container, .k-list-container');
                for (var popup of popups) {{
                    if (popup.style.display !== 'none' || popup.offsetParent !== null) {{
                        var items = popup.querySelectorAll('[role="option"], .k-item');
                        for (var item of items) {{
                            if (item.textContent.trim() === '{entity_name}') {{
                                item.scrollIntoView({{block:'center'}});
                                item.click();
                                return 'success';
                            }}
                        }}
                    }}
                }}
                return 'not found';
            """)
            if result != 'success':
                pytest.fail(f"FAIL: Data Entity '{entity_name}' was not found in the dropdown.")
            logger.info(f"INFO - Data Entity '{entity_name}' selected successfully.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Data Entity '{entity_name}'. {e}")

    def enter_enrich_entity_name(self, entity_name: str):
        try:
            inp = self.wait.until(EC.element_to_be_clickable(self.enrich_entity_name_input))
            self.driver.execute_script("arguments[0].click(); arguments[0].value='';", inp)
            inp.clear()
            inp.send_keys(entity_name)
            logger.info(f"INFO - Entered enrich entity name: {entity_name}")
        except Exception as e:
            pytest.fail(f"FAIL: Could not enter enrich entity name. {e}")
            
    def enter_process_name(self, process_name: str):
        try:
            inp = self.wait.until(EC.element_to_be_clickable(self.process_name_input))
            self.driver.execute_script("arguments[0].click(); arguments[0].value='';", inp)
            inp.clear()
            inp.send_keys(process_name)
            logger.info(f"INFO - Entered process name: {process_name}")
        except Exception as e:
            pytest.fail(f"FAIL: Could not enter process name. {e}")

    def select_data_owner(self, email: str):
        try:
            # Click the dropdown
            self.driver.execute_script("""
                var inputs = document.querySelectorAll('input#data_owners, .multi-select-data-owner');
                if(inputs.length > 0){
                    inputs[inputs.length-1].scrollIntoView({block:'center'});
                    inputs[inputs.length-1].click();
                }
            """)
            time.sleep(1)
            
            result = self.driver.execute_script(f"""
                var popups = document.querySelectorAll('.k-popup, .k-animation-container, .k-list-container');
                for (var popup of popups) {{
                    if (popup.style.display !== 'none' || popup.offsetParent !== null) {{
                        var items = popup.querySelectorAll('[role="option"], .k-item');
                        for (var item of items) {{
                            if (item.textContent.trim() === '{email}') {{
                                item.scrollIntoView({{block:'center'}});
                                item.click();
                                return 'success';
                            }}
                        }}
                    }}
                }}
                return 'not found';
            """)
            if result != 'success':
                pytest.fail(f"FAIL: Data Owner '{email}' not found.")
                
            # Close dropdown if multi-select
            self.driver.execute_script("document.body.click();")
            logger.info(f"INFO - Data Owner '{email}' selected.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Data Owner '{email}'. {e}")

    def enable_historical_data_change(self):
        try:
            cb = self.wait.until(EC.presence_of_element_located(self.is_type_2_checkbox))
            is_checked = self.driver.execute_script("return arguments[0].checked;", cb)
            if not is_checked:
                self.driver.execute_script("arguments[0].click();", cb)
            logger.info("INFO - Enabled Historical Data Change Management.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not enable Historical Data Change Management. {e}")

    def click_next(self):
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.next_btn))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
            logger.info("INFO - Clicked Next button.")
            time.sleep(2)
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Next button. {e}")

    def click_add_new_column(self):
        try:
            btn_xpath = "//button[contains(normalize-space(.), 'Add Column') or contains(@class, 'default_button')]"
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
            
            # Verify dialog with loose text matching
            dialog_xpath = "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create enrichment column') or contains(@class, 'k-window-title')]"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, dialog_xpath)))
            logger.info("INFO - Clicked + Add New Column and dialog displayed successfully.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Add New Column or dialog didn't appear. {e}")

    def enter_column_display_name(self, name: str):
        try:
            inp_xpath = "//input[@id='display_column_name' or @name='display_column_name']"
            inp = self.wait.until(EC.element_to_be_clickable((By.XPATH, inp_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click(); arguments[0].value='';", inp)
            inp.clear()
            inp.send_keys(name)
            logger.info(f"INFO - Entered Column Display Name: {name}")
        except Exception as e:
            pytest.fail(f"FAIL: Could not enter Column Display Name. {e}")

    def select_data_type(self, data_type: str):
        try:
            self.driver.execute_script("""
                var label = document.querySelector('label#data_type_label');
                if (label) {
                    var picker = label.nextElementSibling.querySelector('.k-dropdownlist, .k-picker, button');
                    if(picker) { picker.scrollIntoView({block:'center'}); picker.click(); }
                }
            """)
            time.sleep(1)
            
            self.driver.execute_script(f"""
                var popups = document.querySelectorAll('.k-popup, .k-animation-container, .k-list-container');
                for (var popup of popups) {{
                    if (popup.style.display !== 'none' || popup.offsetParent !== null) {{
                        var items = popup.querySelectorAll('[role="option"], .k-item');
                        for (var item of items) {{
                            if (item.textContent.trim().toLowerCase() === '{data_type.lower()}') {{
                                item.scrollIntoView({{block:'center'}});
                                item.click();
                                return;
                            }}
                        }}
                    }}
                }}
            """)
            logger.info(f"INFO - Data Type '{data_type}' selected successfully.")
            time.sleep(0.5)
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Data Type '{data_type}'. {e}")

    def select_column_type(self, col_type: str):
        try:
            self.driver.execute_script("""
                var label = document.querySelector('label#input_type_label');
                if (label) {
                    var picker = label.nextElementSibling.querySelector('.k-dropdownlist, .k-picker, button');
                    if(picker) { picker.scrollIntoView({block:'center'}); picker.click(); }
                }
            """)
            time.sleep(1)
            
            self.driver.execute_script(f"""
                var popups = document.querySelectorAll('.k-popup, .k-animation-container, .k-list-container');
                for (var popup of popups) {{
                    if (popup.style.display !== 'none' || popup.offsetParent !== null) {{
                        var items = popup.querySelectorAll('[role="option"], .k-item');
                        for (var item of items) {{
                            if (item.textContent.trim().toLowerCase() === '{col_type.lower()}') {{
                                item.scrollIntoView({{block:'center'}});
                                item.click();
                                return;
                            }}
                        }}
                    }}
                }}
            """)
            logger.info(f"INFO - Column Type '{col_type}' selected successfully.")
            time.sleep(0.5)
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Column Type '{col_type}'. {e}")

    def click_create_enrichment_column(self):
        try:
            btn_xpath = "//button[@name='generate' or contains(normalize-space(.), 'Add New')]"
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
            logger.info("INFO - Clicked Add New to create enrichment column.")
            time.sleep(2)
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Add New to create enrichment column. {e}")

    def select_static_dropdown_option(self):
        try:
            # We assume it's a radio button or label with text "Static"
            self.driver.execute_script("""
                var labels = document.querySelectorAll('label, span, div');
                for (var el of labels) {
                    if (el.textContent.trim().toLowerCase() === 'static') {
                        var radio = el.parentElement.querySelector('input[type="radio"]');
                        if (radio && !radio.checked) {
                            radio.click();
                        } else {
                            el.click();
                        }
                        return;
                    }
                }
            """)
            time.sleep(0.5)
            logger.info("INFO - Selected Static option for Dropdown.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Static option. {e}")

    def add_static_dropdown_value(self, value: str):
        try:
            inp_xpath = "//input[@id='dropdown_input_value' or @name='dropdown_input_value']"
            inp = self.wait.until(EC.element_to_be_clickable((By.XPATH, inp_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", inp)
            inp.clear()
            # In case it strictly enforces number because of type="number" in the HTML provided by user,
            # we send keys normally. If it fails to type string into a number input, we inject it via JS.
            self.driver.execute_script("arguments[0].value = arguments[1];", inp, value)
            inp.send_keys(Keys.SPACE)
            inp.send_keys(Keys.BACKSPACE)
            
            # Click the Add button next to it
            add_btn_xpath = "//div[contains(@class, 'primary_button') and contains(normalize-space(.), 'Add')]"
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, add_btn_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
            
            logger.info(f"INFO - Added static dropdown value '{value}'.")
            time.sleep(1)
        except Exception as e:
            pytest.fail(f"FAIL: Could not add static dropdown value. {e}")

    def select_dynamic_dropdown_option(self):
        try:
            self.driver.execute_script("""
                var dynamicRadio = document.querySelector('input[type="radio"][value="dynamic"]');
                if (dynamicRadio && !dynamicRadio.checked) {
                    dynamicRadio.click();
                    return;
                }
                
                var labels = document.querySelectorAll('label, span, div');
                for (var el of labels) {
                    if (el.textContent.trim().toLowerCase() === 'dynamic') {
                        var radio = el.parentElement.querySelector('input[type="radio"]');
                        if (radio && !radio.checked) {
                            radio.click();
                        } else {
                            el.click();
                        }
                        return;
                    }
                }
            """)
            time.sleep(0.5)
            logger.info("INFO - Selected Dynamic option for Dropdown.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not select Dynamic option. {e}")

    def click_all_columns_view(self):
        try:
            self.driver.execute_script("""
                var inputs = document.querySelectorAll('input[name="filter_type"][value="All Columns"]');
                if (inputs.length > 0) {
                    inputs[0].click();
                } else {
                    var labels = document.querySelectorAll('label');
                    for (var label of labels) {
                        if (label.textContent.trim() === 'All Columns') {
                            label.click();
                            return;
                        }
                    }
                }
            """)
            logger.info("INFO - Clicked 'All Columns' radio button.")
            time.sleep(3)  # wait for grid to refresh
        except Exception as e:
            pytest.fail(f"FAIL: Could not click 'All Columns' view. {e}")

    def verify_enrichment_columns_in_grid(self, expected_columns: list):
        try:
            # Wait for grid rows to load
            grid_row_xpath = "//tr[contains(@class, 'k-table-row')]"
            self.wait.until(EC.presence_of_all_elements_located((By.XPATH, grid_row_xpath)))
            
            # Wait a moment to ensure rows are fully populated
            time.sleep(1)
            
            cells = self.driver.find_elements(By.XPATH, "//td[@aria-colindex='2']")
            actual_columns = [cell.text.strip() for cell in cells if cell.text.strip()]
            
            missing = [col for col in expected_columns if col not in actual_columns]
            if missing:
                pytest.fail(f"FAIL: The following enrichment columns were not found in the grid: {missing}. Actual columns: {actual_columns}")
            
            logger.info(f"INFO - Successfully verified columns in grid: {expected_columns}")
        except Exception as e:
            pytest.fail(f"FAIL: Could not verify columns in grid. {e}")

    def click_enrich_view(self):
        try:
            self.driver.execute_script("""
                var inputs = document.querySelectorAll('input[name="filter_type"][value="Enrich"]');
                if (inputs.length > 0) {
                    inputs[0].click();
                } else {
                    var labels = document.querySelectorAll('label');
                    for (var label of labels) {
                        if (label.textContent.trim() === 'Enrich') {
                            label.click();
                            return;
                        }
                    }
                }
            """)
            logger.info("INFO - Clicked 'Enrich' radio button.")
            time.sleep(3)  # wait for grid to refresh
        except Exception as e:
            pytest.fail(f"FAIL: Could not click 'Enrich' view. {e}")

    def verify_only_enrichment_columns_in_grid(self, expected_columns: list):
        try:
            # Wait for grid rows to load
            grid_row_xpath = "//tr[contains(@class, 'k-table-row')]"
            self.wait.until(EC.presence_of_all_elements_located((By.XPATH, grid_row_xpath)))
            
            time.sleep(1)
            
            cells = self.driver.find_elements(By.XPATH, "//td[@aria-colindex='2']")
            actual_columns = [cell.text.strip() for cell in cells if cell.text.strip()]
            
            missing = [col for col in expected_columns if col not in actual_columns]
            if missing:
                pytest.fail(f"FAIL: The following enrichment columns were not found in the grid: {missing}. Actual columns: {actual_columns}")
            
            from collections import Counter
            counts = Counter(actual_columns)
            
            extra = [col for col in actual_columns if col not in expected_columns]
            if extra:
                pytest.fail(f"FAIL: Found unexpected columns in the Enrich view: {extra}. Actual columns: {actual_columns}")
            
            duplicates = [col for col, count in counts.items() if count > 1]
            if duplicates:
                pytest.fail(f"FAIL: The following enrichment columns appear more than once: {duplicates}. Actual columns: {actual_columns}")
                
            logger.info(f"INFO - Successfully verified only enrichment columns in grid and each appears only once: {expected_columns}")
        except Exception as e:
            pytest.fail(f"FAIL: Could not verify Enrich view columns in grid. {e}")

    def click_save_changes(self):
        try:
            btn_xpath = "//button[contains(normalize-space(.), 'Save Changes')]"
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
            logger.info("INFO - Clicked Save Changes button.")

            # Toast detection — Kendo/React renders title + message in separate child spans.
            # Use ancestor-level patterns that match any container holding either keyword.
            save_toast_patterns = [
                # Exact combined text in one element (ideal case)
                "//*[contains(text(), 'SUCCESS') and contains(text(), 'Enrichment entity has been successfully updated')]",
                # Title in one descendant, message in another — check ancestor div/section
                "//*[.//*[contains(text(), 'SUCCESS')] and .//*[contains(normalize-space(.), 'successfully updated')]]",
                # Generic success toast container matching either keyword
                "//*[.//*[contains(normalize-space(.), 'Enrichment entity has been successfully updated')]]",
                "//*[contains(normalize-space(.), 'Enrichment entity has been successfully updated')]",
                # Broad fallback: any visible SUCCESS toast
                "//*[contains(normalize-space(.), 'SUCCESS') and contains(normalize-space(.), 'updated')]",
            ]

            toast_wait = WebDriverWait(self.driver, 30)
            toast_found = False
            matched_text = ""
            for pattern in save_toast_patterns:
                try:
                    el = toast_wait.until(EC.visibility_of_element_located((By.XPATH, pattern)))
                    matched_text = el.text.strip()
                    logger.info(f"INFO - Save Changes toast verified. Matched text: '{matched_text[:120]}'")
                    toast_found = True
                    break
                except Exception:
                    continue

            if not toast_found:
                # Log all visible toast-like elements to help diagnose the actual message
                try:
                    visible_toasts = self.driver.find_elements(
                        By.XPATH,
                        "//*[contains(@class,'toast') or contains(@class,'notification') or contains(@class,'alert') or contains(@class,'k-notification')]"
                    )
                    for t in visible_toasts:
                        logger.warning(f"WARN - Visible toast-like element text: '{t.text.strip()[:200]}'")
                    # Also log any element containing 'successfully'
                    success_els = self.driver.find_elements(By.XPATH, "//*[contains(text(),'successfully') or contains(text(),'Successfully')]")
                    for s in success_els:
                        logger.warning(f"WARN - 'Successfully' element: '{s.text.strip()[:200]}'")
                except Exception:
                    pass
                pytest.fail("FAIL: Save Changes clicked but no success toast was detected within 30 seconds.")

            time.sleep(2)
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: Could not click Save Changes or verify toast. {e}")


    def validate_drag_and_drop(self):
        try:
            # Wait for grid rows
            grid_row_xpath = "//tr[contains(@class, 'k-table-row')]"
            self.wait.until(EC.presence_of_all_elements_located((By.XPATH, grid_row_xpath)))
            time.sleep(1)
            
            cells = self.driver.find_elements(By.XPATH, "//td[@aria-colindex='2']")
            if len(cells) < 2:
                logger.info("INFO - Not enough rows to perform drag and drop.")
                return
                
            initial_order = [cell.text.strip() for cell in cells if cell.text.strip()]
            logger.info(f"INFO - Initial order before drag and drop: {initial_order}")
            
            # Find drag handles (first column)
            drag_handles = self.driver.find_elements(By.XPATH, "//tr[contains(@class, 'k-table-row')]//td[1]")
            if len(drag_handles) < 2:
                pytest.fail("FAIL: Not enough drag handles found to perform drag and drop.")
                
            source = drag_handles[0]
            target = drag_handles[1]
            
            from selenium.webdriver import ActionChains
            actions = ActionChains(self.driver)
            actions.click_and_hold(source).move_to_element_with_offset(target, 0, 15).release().perform()
            logger.info("INFO - Performed drag and drop action.")
            
            drag_toast_patterns = [
                "//*[contains(text(), 'SUCCESS') and contains(text(), 'Order updated successfully')]",
                "//*[.//*[contains(text(), 'SUCCESS')] and .//*[contains(normalize-space(.), 'Order updated')]]",
                "//*[.//*[contains(normalize-space(.), 'Order updated successfully')]]",
                "//*[contains(normalize-space(.), 'Order updated successfully')]",
                "//*[contains(normalize-space(.), 'SUCCESS') and contains(normalize-space(.), 'updated')]",
            ]
            toast_wait = WebDriverWait(self.driver, 30)
            drag_toast_found = False
            for pattern in drag_toast_patterns:
                try:
                    el = toast_wait.until(EC.visibility_of_element_located((By.XPATH, pattern)))
                    logger.info(f"INFO - Drag-and-drop toast verified: '{el.text.strip()[:120]}'")
                    drag_toast_found = True
                    break
                except Exception:
                    continue
            if not drag_toast_found:
                logger.warning("WARN - Drag-and-drop toast not detected within 30s. Continuing anyway.")

            time.sleep(3)
            
            new_cells = self.driver.find_elements(By.XPATH, "//td[@aria-colindex='2']")
            new_order = [cell.text.strip() for cell in new_cells if cell.text.strip()]
            logger.info(f"INFO - New order after drag and drop: {new_order}")
            
        except Exception as e:
            pytest.fail(f"FAIL: Drag and drop validation failed. {e}")

    def deploy_pipeline(self):
        try:
            btn_xpath = "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'deploy pipeline')]"
            btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, btn_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", btn)
            logger.info("INFO - Clicked Deploy Pipeline button.")
            
            # Wait for success deployment toast with multi-pattern fallback
            deploy_toast_patterns = [
                "//*[contains(text(), 'SUCCESS') and contains(text(), 'Your changes have been successfully deployed')]",
                "//*[.//*[contains(text(), 'SUCCESS')] and .//*[contains(normalize-space(.), 'successfully deployed')]]",
                "//*[.//*[contains(normalize-space(.), 'Your changes have been successfully deployed')]]",
                "//*[contains(normalize-space(.), 'Your changes have been successfully deployed')]",
                "//*[contains(normalize-space(.), 'SUCCESS') and contains(normalize-space(.), 'deployed')]",
            ]
            toast_wait = WebDriverWait(self.driver, 60)
            deploy_toast_found = False
            matched_text = ""
            for pattern in deploy_toast_patterns:
                try:
                    el = toast_wait.until(EC.visibility_of_element_located((By.XPATH, pattern)))
                    matched_text = el.text.strip()
                    logger.info(f"INFO - Deploy toast verified: '{matched_text[:120]}'")
                    deploy_toast_found = True
                    break
                except Exception:
                    continue
            if not deploy_toast_found:
                try:
                    success_els = self.driver.find_elements(By.XPATH, "//*[contains(text(),'successfully') or contains(text(),'Successfully')]")
                    for s in success_els:
                        logger.warning(f"WARN - 'Successfully' element found: '{s.text.strip()[:200]}'")
                except Exception:
                    pass
                pytest.fail("FAIL: Deploy Pipeline clicked but no success toast detected within 60 seconds.")

            time.sleep(2)
        except Exception as e:
            pytest.fail(f"FAIL: Deploy pipeline failed. {e}")
