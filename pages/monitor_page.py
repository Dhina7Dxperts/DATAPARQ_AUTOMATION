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
        """
        Step 1: Navigate to the Monitor module.

        Logic (based on actual app HTML structure):
        ─────────────────────────────────────────
        Scenario 1 — Monitor menu already visible:
            The Monitor nav link (<a href="/monitor">) is already in the DOM
            and displayed. Click it directly without touching OBSERVE & ASK.

        Scenario 2 — Monitor menu hidden (OBSERVE & ASK collapsed):
            The OBSERVE & ASK section is collapsed (its child links are hidden).
            Click the OBSERVE & ASK toggle (span.text-dark-9 with text 'OBSERVE & ASK'
            inside the cursor-pointer div) to expand it, then click Monitor.

        Confirmation: URL contains '/monitor' OR the Domain Name grid column appears.
        """
        # ── Locators derived from the real HTML ───────────────────────────────
        # Monitor nav link:  <div class="flex-grow flex-1 truncate text-sm">Monitor</div>
        MONITOR_LINK_LOCATORS = [
            (By.XPATH, "//div[contains(@class, 'truncate') and normalize-space(text())='Monitor']"),
            (By.XPATH, "//*[normalize-space(text())='Monitor' and contains(@class, 'truncate')]"),
            (By.XPATH, "//div[normalize-space(text())='Monitor']"),
            (By.XPATH, "//a[@href='/monitor']"),
            (By.XPATH, "//a[contains(@href, '/monitor')]"),
            (By.XPATH, "//a[.//text()[contains(., 'Monitor')]]")
        ]

        # OBSERVE & ASK toggle:
        #   <div class="flex items-center justify-between cursor-pointer py-2 px-1">
        #       <span class="text-xs text-dark-9">OBSERVE & ASK</span>
        OBSERVE_ASK_LOCATORS = [
            (By.XPATH, "//span[contains(@class,'text-dark-9') and "
                       "normalize-space(text())='OBSERVE & ASK']"
                       "/ancestor::div[contains(@class,'cursor-pointer')]"),
            (By.XPATH, "//span[normalize-space(text())='OBSERVE & ASK']"
                       "/ancestor::div[contains(@class,'cursor-pointer')]"),
            (By.XPATH, "//div[contains(@class,'cursor-pointer') and "
                       ".//span[normalize-space(text())='OBSERVE & ASK']]"),
            # Fallback: the span itself
            (By.XPATH, "//span[normalize-space(text())='OBSERVE & ASK']"),
        ]

        try:
            # ── Check if already on Monitor page ──
            if "monitor" in self.driver.current_url.lower():
                logger.info("Already on Monitor page based on URL.")
                return
                
            # ── Find the Monitor Link in DOM ──
            monitor_link = None
            
            # Wait up to 10 seconds for the menu items to appear in the DOM
            import time
            end_time = time.time() + 10
            
            while time.time() < end_time:
                for loc in MONITOR_LINK_LOCATORS:
                    try:
                        candidates = self.driver.find_elements(*loc)
                        if candidates:
                            monitor_link = candidates[0]
                            break
                    except Exception:
                        continue
                        
                if monitor_link:
                    break
                time.sleep(1)

            if not monitor_link:
                pytest.fail("FAIL: Monitor link could not be found in the DOM.")

            # ── Click the Monitor nav link ─────────────────────────────────────
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", monitor_link)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", monitor_link)
            logger.info("Clicked Monitor nav link.")
            time.sleep(2)

            # ── Confirm navigation succeeded ──────────────────────────────────
            navigated = False

            # Check 1: URL
            for url_fragment in ["/monitor", "monitor"]:
                try:
                    self.wait.until(EC.url_contains(url_fragment))
                    navigated = True
                    logger.info(
                        f"URL confirmed Monitor navigation "
                        f"(contains '{url_fragment}')."
                    )
                    break
                except Exception:
                    continue

            # Check 2: Page content (grid column or header)
            if not navigated:
                content_locators = [
                    (By.XPATH,
                     "//span[contains(@class,'k-column-title') "
                     "and normalize-space(text())='Domain Name']"),
                    (By.XPATH,
                     "//*[normalize-space(text())='Monitor' "
                     "and contains(@class,'text-xl')]"),
                    (By.XPATH,
                     "//*[contains(@class,'k-grid')]"),
                ]
                for cloc in content_locators:
                    try:
                        self.wait.until(EC.presence_of_element_located(cloc))
                        navigated = True
                        logger.info(
                            f"Monitor page content confirmed via: {cloc}"
                        )
                        break
                    except Exception:
                        continue

            if not navigated:
                pytest.fail(
                    "FAIL: Clicked Monitor nav but page navigation could not "
                    "be confirmed via URL or page content."
                )

            logger.info("Successfully navigated to Monitor module.")

        except Exception as e:
            if "FAIL:" in str(e):
                raise
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
        """
        Search/filter the Monitor grid for the given domain name.

        Tries four strategies in order, stopping as soon as the domain row
        is visible in the grid:

        1. Kendo ComboBox: click the dropdown toggle, wait for list popup,
           select the matching item.
        2. Text filter via search box: clear → type → dispatch JS events →
           press Enter → wait for grid row.
        3. Direct grid scan: check if the row is already visible (no search
           needed), which can happen if the grid shows all rows by default.
        4. Scroll + pagination: scroll down through the grid to find the row.
        """
        from selenium.webdriver.common.keys import Keys

        domain_row_locator = (
            By.XPATH,
            f"//td[contains(translate(normalize-space(.), "
            f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
            f"'{domain_name.lower()}')]"
        )

        def _domain_visible():
            """Return True if the domain row is already visible in the grid."""
            try:
                elements = self.driver.find_elements(*domain_row_locator)
                return bool(elements and any(e.is_displayed() for e in elements))
            except Exception:
                return False

        try:
            # ── Wait for the grid column header to confirm grid is loaded ─────
            # Use a longer wait here (60s) because after creating a batch, the backend might take time to reload the grid.
            long_header_wait = WebDriverWait(self.driver, 60)
            long_header_wait.until(EC.visibility_of_element_located(self.domain_name_column))
            logger.info("Monitor grid loaded. Beginning domain search strategies.")

            # ── Strategy 3 (fast-path): domain already visible before search ──
            if _domain_visible():
                logger.info(f"Domain '{domain_name}' already visible in grid — no search needed.")
                return

            # ── Strategy 1: Kendo ComboBox toggle ─────────────────────────────
            logger.info("Strategy 1: Attempting Kendo ComboBox toggle approach.")
            try:
                toggle_locators = [
                    (By.XPATH, "//button[contains(@class,'k-input-button') or contains(@class,'k-select')]"),
                    (By.XPATH, "//*[@role='combobox']//button"),
                    (By.XPATH, "//span[contains(@class,'k-picker')]//button"),
                ]
                toggled = False
                for tloc in toggle_locators:
                    try:
                        toggle = self.driver.find_elements(*tloc)
                        if toggle:
                            self.driver.execute_script("arguments[0].click();", toggle[0])
                            time.sleep(1)
                            toggled = True
                            break
                    except Exception:
                        continue

                if toggled:
                    # Wait for the popup list and find our item
                    popup_item_locator = (
                        By.XPATH,
                        f"//li[contains(@class,'k-list-item') and "
                        f"contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
                        f"'{domain_name.lower()}')]"
                    )
                    short_wait = WebDriverWait(self.driver, 8)
                    option = short_wait.until(EC.element_to_be_clickable(popup_item_locator))
                    self.driver.execute_script("arguments[0].click();", option)
                    logger.info(f"Strategy 1 SUCCESS: Selected '{domain_name}' from Kendo ComboBox.")
                    time.sleep(2)
                    if _domain_visible():
                        return
            except Exception as s1e:
                logger.info(f"Strategy 1 failed: {s1e}")

            # ── Strategy 2: text filter search box + JS events + Enter ─────────
            logger.info("Strategy 2: Text filter search box approach.")
            try:
                search_box_locators = [
                    self.search_input_locator,
                    (By.XPATH, "//input[@placeholder='Search' or @placeholder='search']"),
                    (By.XPATH, "//input[contains(@class,'k-input-inner')]"),
                    (By.XPATH, "//input[@type='search']"),
                    (By.XPATH, "//input[@type='text'][contains(@class,'k-input')]"),
                ]
                search_box = None
                for sloc in search_box_locators:
                    try:
                        candidates = self.driver.find_elements(*sloc)
                        visible = [c for c in candidates if c.is_displayed()]
                        if visible:
                            search_box = visible[0]
                            break
                    except Exception:
                        continue

                if search_box:
                    # Clear, type, dispatch events, wait
                    self.driver.execute_script("arguments[0].click();", search_box)
                    self.driver.execute_script("arguments[0].value = '';", search_box)
                    search_box.clear()
                    search_box.send_keys(domain_name)
                    self.driver.execute_script(
                        "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                        "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                        search_box
                    )
                    time.sleep(2)

                    # Try popup first
                    popup_item_locator = (
                        By.XPATH,
                        f"//li[contains(@class,'k-list-item') and "
                        f"contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
                        f"'{domain_name.lower()}')]"
                    )
                    try:
                        popup_wait = WebDriverWait(self.driver, 5)
                        opt = popup_wait.until(EC.element_to_be_clickable(popup_item_locator))
                        self.driver.execute_script("arguments[0].click();", opt)
                        logger.info(f"Strategy 2a SUCCESS: Selected from popup after typing.")
                    except Exception:
                        # No popup — press Enter
                        search_box.send_keys(Keys.ENTER)
                        logger.info("No popup after typing — pressed Enter.")

                    # Wait up to 30s for the grid row to appear
                    long_grid_wait = WebDriverWait(self.driver, 30)
                    long_grid_wait.until(EC.visibility_of_element_located(domain_row_locator))
                    logger.info(f"Strategy 2 SUCCESS: '{domain_name}' visible in grid after search.")
                    return
            except Exception as s2e:
                logger.info(f"Strategy 2 failed: {s2e}")

            # ── Strategy 3: Direct grid scan (no search at all) ───────────────
            logger.info("Strategy 3: Direct grid row scan (no search).")
            try:
                long_grid_wait = WebDriverWait(self.driver, 15)
                long_grid_wait.until(EC.visibility_of_element_located(domain_row_locator))
                logger.info(f"Strategy 3 SUCCESS: '{domain_name}' found in unfiltered grid.")
                return
            except Exception as s3e:
                logger.info(f"Strategy 3 failed: {s3e}")

            # ── All strategies failed ─────────────────────────────────────────
            pytest.fail(
                f"FAIL: Domain '{domain_name}' could not be found in Monitor grid "
                f"after exhausting all search strategies (ComboBox toggle, text filter, direct scan)."
            )

        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: Could not search/filter domain '{domain_name}' in Monitor module. {e}")

    def search_domain_via_column_filter(self, domain_name):
        try:
            # According to provided HTML, the input is placed near the "Domain Name" column title.
            # <span class="k-column-title">Domain Name</span></span>
            # <input autocomplete="off" id=":rcm:" type="text" placeholder="Search" class="k-input-inner"...
            input_xpath = "//input[@placeholder='Search' and contains(@class, 'k-input-inner')]"
            
            # Since there could be multiple search boxes, we try to locate the correct one.
            search_inputs = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, input_xpath)))
            target_input = search_inputs[0] if search_inputs else None
            
            # Check for the one nearest to "Domain Name" text or simply use the first visible one
            for inp in search_inputs:
                if inp.is_displayed():
                    target_input = inp
                    # If there are multiple visible, try to refine (we'll just use the first visible one for now)
                    break
                    
            if not target_input:
                pytest.fail("FAIL: Domain Name search textbox could not be found.")

            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].click(); arguments[0].value='';", target_input)
            target_input.clear()
            target_input.send_keys(domain_name)
            
            import time
            time.sleep(2)
            
            from selenium.webdriver.common.keys import Keys
            target_input.send_keys(Keys.ENTER)
            
            # Wait for grid to update
            time.sleep(3)
            logger.info(f"Searched domain via column filter for: {domain_name}")
        except Exception as e:
            pytest.fail(f"FAIL: Could not search using domain column filter for '{domain_name}'. {e}")

    def validate_domain_presence(self, domain_name):
        try:
            domain_lower = domain_name.lower()
            time.sleep(2)
            row_xpath = (
                f"//tr[td["
                f"translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')="
                f"'{domain_lower}'"
                f"]]"
            )
            self.wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
            logger.info(f"Domain '{domain_name}' successfully found in the Monitor grid results.")
            return True
        except TimeoutException:
            logger.error(f"Domain '{domain_name}' was NOT found in the Monitor grid results after search.")
            pytest.fail(f"FAIL: Domain '{domain_name}' was not found in the Monitor results grid.")

    def validate_domain_and_workflow_presence(self, domain_name, workflow_name):
        try:
            domain_lower = domain_name.lower()
            workflow_lower = workflow_name.lower()
            time.sleep(2)
            
            # Find rows that contain both the domain and workflow names (case insensitive)
            row_xpath = (
                f"//tr["
                f"td[translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{domain_lower}'] "
                f"and td[translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{workflow_lower}']"
                f"]"
            )
            self.wait.until(EC.presence_of_element_located((By.XPATH, row_xpath)))
            logger.info(f"Domain '{domain_name}' and Workflow '{workflow_name}' successfully found in the Monitor grid results.")
            return True
        except TimeoutException:
            logger.error(f"Domain '{domain_name}' or Workflow '{workflow_name}' was NOT found in the Monitor grid results.")
            pytest.fail(f"FAIL: Row with Domain '{domain_name}' and Workflow '{workflow_name}' was not found in the Monitor results grid.")

    def click_create_batch(self, domain_name):
        try:
            domain_lower = domain_name.lower()
            row_xpath = (
                f"//tr[td["
                f"translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')="
                f"'{domain_lower}'"
                f"]]"
            )
            
            # Broaden cell locator
            action_cell_xpath = f"{row_xpath}//td[contains(@class, 'action') or contains(@class, 'command') or position()=last()]"
            self.wait.until(EC.presence_of_element_located((By.XPATH, action_cell_xpath)))
            
            buttons = self.driver.find_elements(By.XPATH, f"{action_cell_xpath}//button | {action_cell_xpath}//a")
            
            target_button = None
            for btn in buttons:
                html = (btn.get_attribute("outerHTML") or "").lower()
                if "m47.768" in html or "create" in html or "batch" in html or "plus" in html:
                    target_button = btn
                    break
                    
            if not target_button:
                if buttons:
                    target_button = buttons[0]
                else:
                    pytest.fail(f"FAIL: No action buttons found in the row for domain '{domain_name}'.")
                    
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", target_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", target_button)
            logger.info(f"Clicked the Create Batch icon for workflow '{domain_name}'.")
            
            # Verify confirmation dialog with looser text matching
            dialog_xpath = "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'new batch')]"
            self.wait.until(EC.visibility_of_element_located((By.XPATH, dialog_xpath)))
            logger.info("Confirmation dialog 'Do you want to create a new batch?' appeared.")
            
        except Exception as e:
            pytest.fail(f"FAIL: Could not click the Create Batch (+) icon or dialog didn't appear for workflow '{domain_name}'. {e}")

    def confirm_batch_creation(self):
        try:
            dialog_xpath = "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'new batch')]"
            yes_btn_xpath = "//button[contains(@class, 'primary_button') and normalize-space(text())='Yes']"
            yes_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, yes_btn_xpath)))
            self.driver.execute_script("arguments[0].click();", yes_btn)
            logger.info("Clicked 'Yes' in the Create Batch confirmation dialog.")
            
            self.wait.until(EC.invisibility_of_element_located((By.XPATH, dialog_xpath)))
            
            try:
                spinner_xpath = "//*[contains(@class, 'k-loading-mask') or contains(@class, 'spinner') or contains(@class, 'loader')]"
                WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.XPATH, spinner_xpath)))
                WebDriverWait(self.driver, 60).until(EC.invisibility_of_element_located((By.XPATH, spinner_xpath)))
                logger.info("Loading spinner cleared after batch creation.")
            except Exception:
                pass
                
            time.sleep(5)
        except Exception as e:
            pytest.fail(f"FAIL: Confirmation dialog Yes button not found or action was not accepted. {e}")

    def click_task_button(self, domain_name, workflow_name=None):
        try:
            domain_lower = domain_name.lower()
            if workflow_name:
                workflow_lower = workflow_name.lower()
                row_xpath = (
                    f"//tr["
                    f"td[translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{domain_lower}'] "
                    f"and td[translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{workflow_lower}']"
                    f"]"
                )
            else:
                row_xpath = (
                    f"//tr[td["
                    f"translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{domain_lower}'"
                    f"]]"
                )
            
            action_cell_xpath = f"{row_xpath}//td[contains(@class, 'action') or contains(@class, 'command') or position()=last()]"
            
            self.wait.until(EC.presence_of_element_located((By.XPATH, action_cell_xpath)))
            
            buttons = self.driver.find_elements(By.XPATH, f"{action_cell_xpath}//button | {action_cell_xpath}//a")
            
            if not buttons:
                pytest.fail(f"FAIL: No action buttons found in the row for domain '{domain_name}'.")
                
            target_button = None
            for btn in buttons:
                html = (btn.get_attribute("outerHTML") or "").lower()
                if "task" in html or "detail" in html or "monitor" in html or "eye" in html or "12.8168" in html:
                    target_button = btn
                    break
                    
            if not target_button:
                target_button = buttons[2] if len(buttons) >= 3 else buttons[-1]
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", target_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", target_button)
            
            logger.info(f"Clicked the Task button for domain '{domain_name}' and workflow '{workflow_name}'.")
            time.sleep(2)
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

    def select_derived_view_or_fallback(self):
        try:
            derived_radio = self.driver.find_elements(By.XPATH, "//label[contains(@class, 'k-radio-label') and (contains(@aria-label, 'Derived') or contains(text(), 'Derived'))]")
            if derived_radio:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", derived_radio[0])
                self.driver.execute_script("arguments[0].click();", derived_radio[0])
                logger.info("Clicked Derived radio button.")
                time.sleep(2)
            else:
                logger.info("Derived radio button not found. Falling back to Data Lakehouse view.")
                self.select_data_lakehouse_view()
        except Exception as e:
            logger.warning(f"Could not select Derived view: {e}")
            self.select_data_lakehouse_view()

    def validate_task_status_with_flow(self, layer_name="derived", max_wait=1800, poll_interval=15, screenshot_manager=None, step_num=6):
        import time
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'k-column-title') and contains(text(), 'Layer Name')]")))
            
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
                
            start_time = time.time()
            logger.info(f"Starting {max_wait//60}-minute polling for layer '{layer_name}'.")
            
            row_xpath = f"//tr[td[{layer_idx}][contains(normalize-space(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')), '{layer_name.lower()}')]]"
            
            last_status = None

            while time.time() - start_time < max_wait:
                # ── Try to click grid refresh button if it exists ──
                try:
                    refresh_btn = self.driver.find_element(By.XPATH, "//*[contains(@class, 'k-pager-refresh')] | //button[@title='Refresh'] | //button[contains(@class, 'k-pager-refresh')]")
                    if refresh_btn.is_displayed() and refresh_btn.is_enabled():
                        self.driver.execute_script("arguments[0].click();", refresh_btn)
                        time.sleep(1) # short wait for refresh to process
                except Exception:
                    pass

                try:
                    status_cell = self.driver.find_element(By.XPATH, f"{row_xpath}//td[{status_idx}]")
                    status_text = status_cell.text.strip().lower()
                    
                    if status_text != last_status:
                        logger.info(f"Layer '{layer_name}' status changed to: {status_text}")
                        if screenshot_manager:
                            screenshot_manager.capture(step_number=step_num, description=f"Layer {layer_name} status changed to {status_text}")
                        last_status = status_text
                    
                    if status_text in ["failed", "error", "stopped", "cancelled", "aborted"]:
                        pytest.fail(f"FAIL: Task for layer '{layer_name}' encountered terminal status: {status_text}")
                    elif status_text == "completed":
                        logger.info(f"Task for layer '{layer_name}' is Completed successfully!")
                        return True
                        
                except Exception:
                    status_text = "not_found_yet"

                # Log current state to avoid silent polling
                elapsed_mins = int((time.time() - start_time) // 60)
                elapsed_secs = int((time.time() - start_time) % 60)
                logger.info(f"─── Poll at {elapsed_mins}m {elapsed_secs}s ───")
                logger.info(f"  Layer '{layer_name}': {status_text}")
                    
                time.sleep(poll_interval)
                
            pytest.fail(f"Timeout reached: Task for layer '{layer_name}' did not complete within {max_wait//60} minutes.")
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"Failed to validate task status: {e}")

    def validate_multiple_layers_status_with_flow(self, target_layers, max_wait=1800, poll_interval=15, screenshot_manager=None, step_num=6):
        import time
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'k-column-title') and contains(text(), 'Layer Name')]")))
            
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
                
            start_time = time.time()
            logger.info(f"Starting {max_wait//60}-minute polling for layers: {target_layers}.")
            
            last_statuses = {layer: None for layer in target_layers}
            completed_layers = set()
            
            # Wait for rows to render
            time.sleep(2)
            
            while time.time() - start_time < max_wait:
                # ── Try to click grid refresh button if it exists ──
                try:
                    refresh_btn = self.driver.find_element(By.XPATH, "//*[contains(@class, 'k-pager-refresh')] | //button[@title='Refresh'] | //button[contains(@class, 'k-pager-refresh')]")
                    if refresh_btn.is_displayed() and refresh_btn.is_enabled():
                        self.driver.execute_script("arguments[0].click();", refresh_btn)
                        time.sleep(1) # short wait for refresh to process
                except Exception:
                    pass
                    
                rows = self.driver.find_elements(By.XPATH, "//tr[td]")
                
                current_poll_statuses = {}
                for row in rows:
                    try:
                        layer_name_cell = row.find_element(By.XPATH, f"./td[{layer_idx}]")
                        actual_layer_name = layer_name_cell.text.strip().lower()
                        
                        matched_layer = None
                        for target in target_layers:
                            # Remove spaces and convert to lower case for comparison to handle "Data Quality" vs "dataquality"
                            t_clean = target.lower().replace(" ", "")
                            a_clean = actual_layer_name.replace(" ", "")
                            if t_clean == a_clean:
                                matched_layer = target
                                break
                                
                        if not matched_layer:
                            continue # Ignore layers not in target_layers
                            
                        status_cell = row.find_element(By.XPATH, f"./td[{status_idx}]")
                        status_text = status_cell.text.strip().lower()
                        current_poll_statuses[matched_layer] = status_text
                        
                        if status_text != last_statuses[matched_layer]:
                            logger.info(f"Layer '{matched_layer}' status changed to: {status_text}")
                            if screenshot_manager:
                                screenshot_manager.capture(step_number=step_num, description=f"Layer {matched_layer} status changed to {status_text}")
                            last_statuses[matched_layer] = status_text
                            
                        if status_text in ["failed", "error", "stopped", "cancelled", "aborted"]:
                            pytest.fail(f"FAIL: Task for layer '{matched_layer}' encountered terminal status: {status_text}")
                        elif status_text == "completed":
                            completed_layers.add(matched_layer)
                            
                    except Exception:
                        pass
                
                # Log current state to avoid silent polling
                elapsed_mins = int((time.time() - start_time) // 60)
                elapsed_secs = int((time.time() - start_time) % 60)
                logger.info(f"─── Poll at {elapsed_mins}m {elapsed_secs}s ───")
                for target in target_layers:
                    st = current_poll_statuses.get(target, 'not_found_yet')
                    logger.info(f"  Layer '{target}': {st}")
                        
                if len(completed_layers) == len(target_layers):
                    logger.info(f"All target layers ({target_layers}) completed successfully!")
                    return True
                    
                time.sleep(poll_interval)
                
            pytest.fail(f"Timeout reached: Target layers {target_layers} did not complete within {max_wait//60} minutes.")
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"Failed to validate data quality and lake status: {e}")

    def validate_multiple_enrich_tasks_status(self, max_wait=1800, poll_interval=15, screenshot_manager=None, step_num=35):
        import time
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'k-column-title') and contains(text(), 'Layer Name')]")))
            
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
                
            start_time = time.time()
            logger.info(f"Starting {max_wait//60}-minute polling for exactly two 'Enrich' tasks.")
            
            # Wait for rows to render
            time.sleep(2)
            
            while time.time() - start_time < max_wait:
                # Try to click grid refresh button if it exists
                try:
                    refresh_btn = self.driver.find_element(By.XPATH, "//*[contains(@class, 'k-pager-refresh')] | //button[@title='Refresh'] | //button[contains(@class, 'k-pager-refresh')]")
                    if refresh_btn.is_displayed() and refresh_btn.is_enabled():
                        self.driver.execute_script("arguments[0].click();", refresh_btn)
                        time.sleep(1) # short wait for refresh to process
                except Exception:
                    pass
                    
                rows = self.driver.find_elements(By.XPATH, "//tr[td]")
                
                enrich_task_statuses = []
                for row in rows:
                    try:
                        layer_name_cell = row.find_element(By.XPATH, f"./td[{layer_idx}]")
                        actual_layer_name = layer_name_cell.text.strip().lower()
                        
                        if actual_layer_name == "enrich":
                            status_cell = row.find_element(By.XPATH, f"./td[{status_idx}]")
                            status_text = status_cell.text.strip().lower()
                            enrich_task_statuses.append(status_text)
                    except Exception:
                        pass
                
                if len(enrich_task_statuses) != 2:
                    if len(enrich_task_statuses) == 0:
                        logger.info("No Enrich tasks found yet. Continuing to poll...")
                    else:
                        pytest.fail(f"FAIL: Expected exactly two 'Enrich' tasks, but found {len(enrich_task_statuses)}.")
                else:
                    # Log current state
                    elapsed_mins = int((time.time() - start_time) // 60)
                    elapsed_secs = int((time.time() - start_time) % 60)
                    logger.info(f"─── Poll at {elapsed_mins}m {elapsed_secs}s ───")
                    logger.info(f"  Enrich Task 1: {enrich_task_statuses[0]}")
                    logger.info(f"  Enrich Task 2: {enrich_task_statuses[1]}")
                    
                    if screenshot_manager and (elapsed_secs % 60 < poll_interval): # Take screenshot roughly every minute
                        screenshot_manager.capture(step_number=step_num, description=f"Enrich tasks statuses: {enrich_task_statuses[0]}, {enrich_task_statuses[1]}")

                    for status_text in enrich_task_statuses:
                        if status_text in ["failed", "error", "stopped", "cancelled", "aborted"]:
                            pytest.fail(f"FAIL: An Enrich task encountered terminal status: {status_text}")
                            
                    if all(status == "completed" for status in enrich_task_statuses):
                        logger.info("Both Enrich tasks completed successfully!")
                        if screenshot_manager:
                            screenshot_manager.capture(step_number=step_num, description="Both Enrich tasks completed successfully")
                        return True
                        
                time.sleep(poll_interval)
                
            pytest.fail(f"Timeout reached: Enrich tasks did not complete within {max_wait//60} minutes.")
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"Failed to validate Enrich tasks status: {e}")

    def validate_layer_record_counts(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'k-column-title') and contains(text(), 'Layer Name')]")))
            
            headers = self.driver.find_elements(By.XPATH, "//th")
            layer_idx = -1
            count_idx = -1
            for i, header in enumerate(headers):
                text = header.get_attribute("textContent").strip()
                if "Layer Name" in text:
                    layer_idx = i + 1
                elif "Record Count" in text:
                    count_idx = i + 1
                    
            if layer_idx == -1 or count_idx == -1:
                pytest.fail("FAIL: Could not find 'Layer Name' or 'Record Count' column in the task details grid.")
                
            rows = self.driver.find_elements(By.XPATH, "//tr[contains(@class, 'k-master-row')]")
            
            counts = {}
            for row in rows:
                try:
                    layer_name = row.find_element(By.XPATH, f"./td[{layer_idx}]").text.strip().lower()
                    
                    if "staging" in layer_name:
                        key = "staging"
                    elif "data quality" in layer_name or "dataquality" in layer_name:
                        key = "data quality"
                    elif "data lake" in layer_name or "datalake" in layer_name:
                        key = "data lake"
                    else:
                        continue
                        
                    count_text = row.find_element(By.XPATH, f"./td[{count_idx}]").text.strip()
                    count_val = int(count_text.replace(",", ""))
                    counts[key] = count_val
                except Exception:
                    pass
                    
            if "staging" not in counts:
                pytest.fail("FAIL: Staging layer not found in the grid to get record count.")
            if "data quality" not in counts:
                pytest.fail("FAIL: Data Quality layer not found in the grid to get record count.")
            if "data lake" not in counts:
                pytest.fail("FAIL: Data Lake layer not found in the grid to get record count.")
                
            staging_count = counts["staging"]
            dq_count = counts["data quality"]
            lake_count = counts["data lake"]
            
            logger.info(f"Staging Count      : {staging_count}")
            logger.info(f"Data Quality Count : {dq_count}")
            logger.info(f"Data Lake Count    : {lake_count}")
            
            if dq_count >= staging_count:
                pytest.fail(f"FAIL: Data Quality count ({dq_count}) is not less than the Staging count ({staging_count}).")
                
            if lake_count >= staging_count:
                pytest.fail(f"FAIL: Data Lake count ({lake_count}) is not less than the Staging count ({staging_count}).")
                
            logger.info("Record counts successfully validated! Data Quality and Data Lake counts are strictly less than Staging count.")
            return True
            
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: Error during record count validation: {e}")
