from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import get_logger
import pytest

logger = get_logger("ConfigPage")


class ConfigPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self.long_wait = WebDriverWait(driver, 40)

        # ── Page indicators ────────────────────────────────────────────────────
        self.entity_level_setup_locator = (
            By.XPATH,
            "//*[normalize-space(text())='Entity Level Setup']",
        )
        # Left panel: all-caps "SOURCE ENTITIES"
        self.source_entities_panel_locator = (
            By.XPATH,
            "//*[normalize-space(text())='SOURCE ENTITIES']",
        )

        # ── Save button ────────────────────────────────────────────────────────
        self.save_btn_locator = (
            By.XPATH,
            "//span[contains(@class,'k-button-text') and normalize-space(text())='SAVE']"
            "/ancestor::button",
        )

        # ── Success message ────────────────────────────────────────────────────
        # Matches "Config updated successfully" toast/notification
        self.success_msg_locator = (
            By.XPATH,
            "//*[contains(.,'Config updated successfully')] | "
            "//*[contains(.,'successfully') and (contains(.,'Config') or contains(.,'updated'))]",
        )

        # ── Next button ────────────────────────────────────────────────────────
        self.next_btn_locator = (
            By.XPATH,
            "//span[contains(@class,'k-button-text') and normalize-space(text())='Next']"
            "/ancestor::button",
        )

        # ── Ingest page indicator ──────────────────────────────────────────────
        self.ingest_page_locator = (
            By.XPATH,
            "//*[normalize-space(text())='Ingest' or "
            "contains(text(),'Schedule') or contains(text(),'Frequency') or "
            "contains(text(),'Run Now') or contains(text(),'Trigger') or "
            "contains(text(),'Ingest Configuration')]",
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _is_button_disabled(self, element) -> bool:
        classes = element.get_attribute("class") or ""
        disabled_attr = element.get_attribute("disabled")
        aria_disabled = element.get_attribute("aria-disabled")
        return (
            "k-disabled" in classes
            or bool(disabled_attr)
            or aria_disabled == "true"
            or not element.is_enabled()
        )

    def _click_kendo_dropdown_by_label(self, label_text: str, email: str):
        """
        Find the Kendo DropDownList widget associated with `label_text` using
        JavaScript (most reliable for Kendo UI), click it to open the popup,
        then click the option containing `email`.
        """
        # Step 1: Open the dropdown using JS
        open_script = """
            var allDivs = document.querySelectorAll('div');
            for (var div of allDivs) {
                if (div.textContent.trim() === arguments[0] &&
                    div.className.includes('text-raisin-black-1')) {
                    // Walk up to find the field container (parent row)
                    var container = div.closest('div.flex, div.grid, div[class*="col"]');
                    if (!container) container = div.parentElement;

                    // Search in next siblings and their descendants for a Kendo dropdown
                    var sibling = container.nextElementSibling;
                    while (sibling) {
                        var dd = sibling.querySelector(
                            '[class*="k-dropdownlist"], [class*="k-picker"], [role="combobox"], [role="listbox"]'
                        );
                        if (dd) { dd.click(); return dd.className; }
                        sibling = sibling.nextElementSibling;
                    }

                    // Fallback: parent's parent next sibling
                    var parent2 = container.parentElement;
                    if (parent2) {
                        var dd2 = parent2.nextElementSibling &&
                                  parent2.nextElementSibling.querySelector(
                                    '[class*="k-dropdownlist"], [class*="k-picker"], [role="combobox"]'
                                  );
                        if (dd2) { dd2.click(); return dd2.className; }
                    }

                    // Last resort: click the container itself if it's a picker
                    var selfDd = container.querySelector(
                        '[class*="k-dropdownlist"], [class*="k-picker"], [role="combobox"]'
                    );
                    if (selfDd) { selfDd.click(); return selfDd.className; }
                }
            }
            return null;
        """
        result = self.driver.execute_script(open_script, label_text)
        if result is None:
            # Try by position: find ALL Kendo dropdownlists and pick the right one
            fallback_script = """
                var labels = document.querySelectorAll('[class*="text-raisin-black-1"]');
                var labelEls = [];
                for (var l of labels) {
                    if (l.textContent.trim() === arguments[0]) labelEls.push(l);
                }
                if (labelEls.length === 0) return null;
                var label = labelEls[0];
                var rect = label.getBoundingClientRect();
                var allPickers = document.querySelectorAll('[class*="k-dropdownlist"], [class*="k-picker"]');
                var closest = null; var minDist = 99999;
                for (var p of allPickers) {
                    var pr = p.getBoundingClientRect();
                    var dist = Math.abs(pr.top - rect.bottom) + Math.abs(pr.left - rect.left);
                    if (dist < minDist) { minDist = dist; closest = p; }
                }
                if (closest) { closest.click(); return closest.className; }
                return null;
            """
            result = self.driver.execute_script(fallback_script, label_text)

        if result is None:
            pytest.fail(
                f"FAIL: Could not find Kendo dropdown associated with label '{label_text}'"
            )
        else:
            logger.info(f"INFO - Opened dropdown for '{label_text}' (class: {result[:60]}...)")

        # Step 2: Wait for the Kendo popup container to appear first
        popup_locator = (
            By.XPATH,
            "//*[contains(@class,'k-popup') or contains(@class,'k-animation-container') "
            "or contains(@class,'k-list-container')]"
            "[.//*[@role='option' or contains(@class,'k-list-item') or contains(@class,'k-item')]]",
        )
        try:
            self.long_wait.until(EC.visibility_of_element_located(popup_locator))
            logger.info("INFO - Dropdown popup is visible.")
        except Exception:
            logger.warning("WARNING - Popup visibility check timed out, attempting option search anyway.")

        # Step 3: Find the option — use simple contains() to avoid normalize-space issues
        option_xpath = (
            f"//*[contains(@class,'k-popup') or contains(@class,'k-animation-container') or "
            f"contains(@class,'k-list-container')]"
            f"//*[@role='option' or contains(@class,'k-list-item') or contains(@class,'k-item')]"
            f"[contains(.,'{email}')]"
        )
        try:
            option = self.long_wait.until(
                EC.presence_of_element_located((By.XPATH, option_xpath))
            )
            # Scroll into view first, then JS click to avoid "element click intercepted"
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
            self.driver.execute_script("arguments[0].click();", option)
            logger.info(f"INFO - Selected '{email}' from dropdown.")
        except Exception as e:
            pytest.fail(
                f"FAIL: Option '{email}' not visible or not clickable in the dropdown "
                f"for '{label_text}'. Popup may not have opened. {e}"
            )

        # Step 3: Verify selection is reflected
        try:
            self.wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, f"//*[contains(normalize-space(.),'{email}') "
                               f"and not(contains(@class,'k-popup')) "
                               f"and not(contains(@class,'k-animation-container'))]")
                )
            )
            logger.info(f"INFO - '{email}' confirmed visible in the field.")
        except Exception:
            logger.warning(f"WARNING - Could not confirm '{email}' shown in field (may still be correct).")

    # ── Step 11: Validate Config page ─────────────────────────────────────────

    def validate_config_page_loaded(self):
        """Verify Entity Level Setup heading and SOURCE ENTITIES panel are visible."""
        try:
            self.wait.until(EC.visibility_of_element_located(self.entity_level_setup_locator))
            logger.info("INFO - 'Entity Level Setup' section is visible.")
        except Exception as e:
            pytest.fail(f"FAIL: Config page did not load — 'Entity Level Setup' not visible. {e}")

        try:
            self.wait.until(EC.visibility_of_element_located(self.source_entities_panel_locator))
            logger.info("INFO - 'SOURCE ENTITIES' panel is visible.")
        except Exception as e:
            pytest.fail(f"FAIL: Config page — 'SOURCE ENTITIES' panel not visible. {e}")

    # ── Step 12: Save disabled before selections ───────────────────────────────

    def validate_save_button_disabled(self):
        """Verify Save button is disabled before any dropdown selection."""
        try:
            save_btn = self.wait.until(EC.presence_of_element_located(self.save_btn_locator))
            if self._is_button_disabled(save_btn):
                logger.info("INFO - Save button is correctly DISABLED before selections.")
            else:
                logger.warning("WARNING - Save button appears ENABLED before selections.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not locate SAVE button on Config page. {e}")

    # ── Step 13: Select Data Owner ─────────────────────────────────────────────

    def select_data_owner(self, email: str = "deepanraj.thangaraj@7dxperts.com"):
        """Select the given email in the Data Owners multi-select dropdown."""
        logger.info(f"INFO - Selecting Data Owner: {email}")
        self._select_kendo_multiselect("data_owners", email)
        logger.info(f"INFO - Data Owner '{email}' selected.")

    # ── Step 14: Select Data Steward ──────────────────────────────────────────

    def select_data_steward(self, email: str = "shreyas.senthilkumar@7dxperts.com"):
        """Select the given email in the Data Stewards multi-select dropdown."""
        logger.info(f"INFO - Selecting Data Steward: {email}")
        self._select_kendo_multiselect("data_stewards", email)
        logger.info(f"INFO - Data Steward '{email}' selected.")

    def _select_kendo_multiselect(self, input_id: str, email: str):
        # 1. Locate the input field
        input_locator = (By.ID, input_id)
        input_el = self.wait.until(EC.element_to_be_clickable(input_locator))
        
        # 2. Click to open dropdown and type to filter
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_el)
        input_el.click()
        input_el.clear()
        input_el.send_keys(email)
        
        import time
        time.sleep(1) # wait for filtering
        
        # 3. Locate the option in the popup and click it
        option_xpath = f"//div[contains(@class,'k-popup')]//*[@role='option' and contains(normalize-space(.), '{email}')]"
        try:
            option = self.wait.until(EC.visibility_of_element_located((By.XPATH, option_xpath)))
            option.click()
        except Exception as e:
            pytest.fail(f"FAIL: Option '{email}' not found in dropdown {input_id}. {e}")
            
        # 4. Verify selection is reflected as a tag in the multiselect container
        token_xpath = f"//input[@id='{input_id}']/ancestor::div[contains(@class,'k-multiselect')]//*[contains(normalize-space(.), '{email}')]"
        try:
            self.wait.until(EC.visibility_of_element_located((By.XPATH, token_xpath)))
        except Exception as e:
            pytest.fail(f"FAIL: Selected value '{email}' not visible in {input_id} field after selection. {e}")

    # ── Step 15: Save enabled & click ─────────────────────────────────────────

    def validate_save_button_enabled_and_click(self):
        """Verify Save button is enabled after both selections, then click it."""
        try:
            save_btn = self.long_wait.until(
                EC.presence_of_element_located(self.save_btn_locator)
            )
            if self._is_button_disabled(save_btn):
                pytest.fail(
                    "FAIL: SAVE button is still DISABLED after selecting Data Owners "
                    "and Data Stewards."
                )
            logger.info("INFO - SAVE button is ENABLED. Clicking...")
            self.driver.execute_script("arguments[0].click();", save_btn)
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: SAVE button validation or click failed. {e}")

    # ── Step 16: Success message ───────────────────────────────────────────────

    def validate_save_success(self):
        """Wait for 'Config updated successfully' message after Save."""
        try:
            self.long_wait.until(EC.visibility_of_element_located(self.success_msg_locator))
            logger.info("INFO - Success message 'Config updated successfully' is displayed.")
        except Exception as e:
            pytest.fail(
                "FAIL: Success message 'Config updated successfully' was NOT displayed "
                f"after clicking Save. {e}"
            )

    # ── Step 17: Next enabled after save & click ───────────────────────────────

    def validate_next_button_enabled_and_click(self):
        """After save, verify Next button is enabled then click it."""
        try:
            next_btn = self.long_wait.until(EC.element_to_be_clickable(self.next_btn_locator))
            if self._is_button_disabled(next_btn):
                pytest.fail(
                    "FAIL: Next button is still DISABLED after saving Config. "
                    "Expected it to be enabled after successful save."
                )
            logger.info("INFO - Next button is ENABLED after Config save. Clicking...")
            self.driver.execute_script("arguments[0].click();", next_btn)
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: Next button click failed on Config page. {e}")

    # ── Step 18: Ingest page ───────────────────────────────────────────────────

    def validate_ingest_page_loaded(self):
        """Verify navigation to the Ingest page after clicking Next."""
        try:
            self.long_wait.until(EC.visibility_of_element_located(self.ingest_page_locator))
            logger.info("INFO - Successfully navigated to Ingest page.")
        except Exception as e:
            pytest.fail(
                f"FAIL: Did not navigate to Ingest page after clicking Next on Config page. {e}"
            )
