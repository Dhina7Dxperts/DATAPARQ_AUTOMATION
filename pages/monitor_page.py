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
        # Monitor nav link:  <a href="/monitor"> ... <svg path ...> ... </a>
        MONITOR_LINK_LOCATORS = [
            (By.XPATH, "//a[@href='/monitor']"),
            (By.XPATH, "//a[contains(@href, '/monitor')]"),
            (By.XPATH, "//a[contains(@href, 'monitor')]"),
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
            # ── Scenario 1: Check if Monitor link is already visible ──────────
            monitor_link = None
            for loc in MONITOR_LINK_LOCATORS:
                try:
                    candidates = self.driver.find_elements(*loc)
                    visible = [el for el in candidates if el.is_displayed()]
                    if visible:
                        monitor_link = visible[0]
                        logger.info(
                            f"Scenario 1: Monitor menu is already visible. "
                            f"Locator used: {loc}"
                        )
                        break
                except Exception:
                    continue

            # ── Scenario 2: Monitor hidden — expand OBSERVE & ASK first ───────
            if monitor_link is None:
                logger.info(
                    "Scenario 2: Monitor menu not visible. "
                    "Expanding 'OBSERVE & ASK' section..."
                )
                observe_ask_el = None
                for loc in OBSERVE_ASK_LOCATORS:
                    try:
                        observe_ask_el = self.wait.until(
                            EC.element_to_be_clickable(loc)
                        )
                        break
                    except Exception:
                        continue

                if observe_ask_el is None:
                    pytest.fail(
                        "FAIL: Could not locate the 'OBSERVE & ASK' toggle "
                        "to expand it. Monitor menu is also not visible."
                    )

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    observe_ask_el
                )
                self.driver.execute_script("arguments[0].click();", observe_ask_el)
                logger.info("Clicked 'OBSERVE & ASK' to expand the section.")
                time.sleep(1.5)

                # Now locate Monitor link (it should be visible after expand)
                for loc in MONITOR_LINK_LOCATORS:
                    try:
                        monitor_link = self.wait.until(EC.element_to_be_clickable(loc))
                        logger.info(
                            f"Monitor menu appeared after expanding OBSERVE & ASK. "
                            f"Locator: {loc}"
                        )
                        break
                    except Exception:
                        continue

                if monitor_link is None:
                    pytest.fail(
                        "FAIL: Clicked 'OBSERVE & ASK' but Monitor menu "
                        "still did not appear."
                    )

            # ── Click the Monitor nav link ─────────────────────────────────────
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", monitor_link
            )
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
            self.wait.until(EC.visibility_of_element_located(self.domain_name_column))
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

    def validate_domain_presence(self, domain_name):
        try:
            # Case-insensitive search to handle any casing variation in the grid
            domain_lower = domain_name.lower()
            domain_cell = (
                By.XPATH,
                f"//td[contains("
                f"translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
                f"'{domain_lower}')]"
            )
            self.long_wait.until(EC.visibility_of_element_located(domain_cell))
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
            domain_lower = domain_name.lower()
            row_xpath = (
                f"//tr[td[contains("
                f"translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),"
                f"'{domain_lower}')]]"
            )
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
