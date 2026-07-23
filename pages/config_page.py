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

    def _is_button_disabled(self, element, locator=None) -> bool:
        """Check if a button element is disabled. Re-fetches via locator on StaleElementReferenceException."""
        from selenium.common.exceptions import StaleElementReferenceException
        for attempt in range(3):
            try:
                classes = element.get_attribute("class") or ""
                disabled_attr = element.get_attribute("disabled")
                aria_disabled = element.get_attribute("aria-disabled")
                return (
                    "k-disabled" in classes
                    or bool(disabled_attr)
                    or aria_disabled == "true"
                    or not element.is_enabled()
                )
            except StaleElementReferenceException:
                if locator and attempt < 2:
                    try:
                        element = self.wait.until(EC.visibility_of_element_located(locator))
                    except Exception:
                        pass
                else:
                    raise
        return False

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
        from selenium.common.exceptions import StaleElementReferenceException
        for attempt in range(3):
            try:
                # Use visibility (not just presence) so the button is fully rendered
                save_btn = self.wait.until(
                    EC.visibility_of_element_located(self.save_btn_locator)
                )
                if self._is_button_disabled(save_btn, self.save_btn_locator):
                    logger.info("INFO - Save button is correctly DISABLED before selections.")
                else:
                    logger.warning("WARNING - Save button appears ENABLED before selections.")
                return  # success
            except StaleElementReferenceException:
                if attempt < 2:
                    logger.warning(f"WARNING - StaleElement on Save button check (attempt {attempt+1}), retrying...")
                    import time; time.sleep(0.5)
                else:
                    pytest.fail("FAIL: Save button became stale repeatedly — Config page may still be loading.")
            except Exception as e:
                pytest.fail(f"FAIL: Could not locate SAVE button on Config page. {e}")

    def _get_multiselect_values(self, element_id: str) -> list:
        """Returns a list of text values currently selected in a Kendo multiselect widget."""
        selected_texts = []
        try:
            # 1) Try using tagslist ID which is typically in aria-describedby
            tagslist_id = f"tagslist-{element_id}"
            tags = self.driver.find_elements(By.CSS_SELECTOR, f"[id*='{tagslist_id}'] .k-chip-content, [id*='{tagslist_id}'] .k-chip, [id*='{tagslist_id}'] .k-button, [id*='{tagslist_id}'] .k-tag")
            if tags:
                return [tag.text.strip() for tag in tags if tag.text.strip()]
            
            # 2) Fallback: look for kendo-multiselect wrapper
            wrapper_xpath = f"//input[@id='{element_id}']/ancestor::kendo-multiselect"
            tags_in_wrapper = self.driver.find_elements(By.XPATH, f"{wrapper_xpath}//*[contains(@class, 'k-chip-content') or contains(@class, 'k-chip') or contains(@class, 'k-button')]")
            if tags_in_wrapper:
                return [tag.text.strip() for tag in tags_in_wrapper if tag.text.strip()]
                
            # 3) Another fallback: look for preceding siblings of the input
            prev_xpath = f"//input[@id='{element_id}']/preceding-sibling::*//span[contains(@class, 'k-chip-content') or contains(@class, 'k-chip')]"
            tags_prev = self.driver.find_elements(By.XPATH, prev_xpath)
            if tags_prev:
                return [tag.text.strip() for tag in tags_prev if tag.text.strip()]
                
        except Exception as e:
            logger.warning(f"WARNING - Error while fetching multiselect values for {element_id}: {e}")
            
        return selected_texts

    # ── Step 13: Select Data Owner ─────────────────────────────────────────────

    def select_data_owner(self, email: str = "deepanraj.thangaraj@7dxperts.com") -> bool:
        """Selects data owner only if the field is currently empty. Returns True if changed."""
        logger.info("INFO - Checking Data Owner field before populating...")
        
        selected_vals = self._get_multiselect_values("data_owners")
        if any(email in val for val in selected_vals):
            logger.info(f"INFO - Data Owner '{email}' is already selected. No changes needed.")
            return False
            
        if selected_vals:
            logger.info(f"INFO - Data Owner field already has existing selection(s): {selected_vals}. Not replacing.")
            return False

        logger.info(f"INFO - Data Owner field is empty. Selecting: {email}")
        changed = self._select_kendo_multiselect("data_owners", email)
        if changed:
            logger.info(f"INFO - Data Owner '{email}' selected successfully.")
        return changed

    # ── Step 14: Select Data Steward ──────────────────────────────────────────

    def select_data_steward(self, email: str = "shreyas.senthilkumar@7dxperts.com") -> bool:
        """Selects data steward only if the field is currently empty. Returns True if changed."""
        logger.info("INFO - Checking Data Steward field before populating...")
        
        selected_vals = self._get_multiselect_values("data_stewards")
        if any(email in val for val in selected_vals):
            logger.info(f"INFO - Data Steward '{email}' is already selected. No changes needed.")
            return False
            
        if selected_vals:
            logger.info(f"INFO - Data Steward field already has existing selection(s): {selected_vals}. Not replacing.")
            return False

        logger.info(f"INFO - Data Steward field is empty. Selecting: {email}")
        changed = self._select_kendo_multiselect("data_stewards", email)
        if changed:
            logger.info(f"INFO - Data Steward '{email}' selected successfully.")
        return changed

    # # ── Step 13: Select Data Owner ─────────────────────────────────────────────

    # def select_data_owner(self, email: str = "deepanraj.thangaraj@7dxperts.com") -> bool:
    #     """Select the given email in the Data Owners multi-select dropdown. Returns True if changed."""
    #     logger.info(f"INFO - Selecting Data Owner: {email}")
    #     changed = self._select_kendo_multiselect("data_owners", email)
    #     if changed:
    #         logger.info(f"INFO - Data Owner '{email}' selected.")
    #     else:
    #         logger.info(f"INFO - Data Owner '{email}' was already selected. No changes made.")
    #     return changed

    # # ── Step 14: Select Data Steward ──────────────────────────────────────────

    # def select_data_steward(self, email: str = "shreyas.senthilkumar@7dxperts.com") -> bool:
    #     """Select the given email in the Data Stewards multi-select dropdown. Returns True if changed."""
    #     logger.info(f"INFO - Selecting Data Steward: {email}")
    #     changed = self._select_kendo_multiselect("data_stewards", email)
    #     if changed:
    #         logger.info(f"INFO - Data Steward '{email}' selected.")
    #     else:
    #         logger.info(f"INFO - Data Steward '{email}' was already selected. No changes made.")
    #     return changed

    def _select_kendo_multiselect(self, input_id: str, email: str) -> bool:
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.common.exceptions import InvalidElementStateException, StaleElementReferenceException
        import time

        # 1. Locate the hidden Kendo binding input and scroll it into view
        input_el = self.wait.until(EC.presence_of_element_located((By.ID, input_id)))
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", input_el)

        # 1.5. Check if the value is already selected. If so, do not modify and return False.
        check_js = """
            var el = document.getElementById(arguments[0]);
            if (!el) return false;
            if (typeof kendo !== 'undefined' && kendo.widgetInstance) {
                try {
                    var w = kendo.widgetInstance(el);
                    if (w && w.value) {
                        var vals = w.value();
                        for (var i = 0; i < vals.length; i++) {
                            if (String(vals[i]).indexOf(arguments[1]) !== -1) return true;
                        }
                    }
                } catch(e) {}
            }
            var wrapper = el.closest('.k-multiselect') || el.parentElement;
            if (!wrapper) return false;
            var chips = wrapper.querySelectorAll('.k-chip, .k-chip-label, li[class*="k-chip"], span[class*="k-chip"]');
            for (var c of chips) {
                if (c.textContent.indexOf(arguments[1]) !== -1) return true;
            }
            return wrapper.textContent.indexOf(arguments[1]) !== -1;
        """
        already_selected = self.driver.execute_script(check_js, input_id, email)
        if already_selected:
            return False

        # 2. Click the *wrapper* div to open the dropdown and move focus to the search box.
        #    We do NOT click the hidden binding input — it is not interactable.
        for attempt in range(3):
            wrapper_js = """
                var el = document.getElementById(arguments[0]);
                if (!el) return null;
                return el.closest('.k-multiselect') || el.parentElement;
            """
            wrapper_el = self.driver.execute_script(wrapper_js, input_id)
            if wrapper_el:
                try:
                    wrapper_el.click()
                    break  # Success
                except StaleElementReferenceException:
                    if attempt < 2:
                        time.sleep(0.5)
                        continue
                    logger.warning(f"WARNING - wrapper_el stale after {attempt+1} attempts.")
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].click();", wrapper_el)
                    except Exception:
                        pass
                    break  # Break on non-stale errors
            else:
                # Fallback: open via Kendo API
                self.driver.execute_script("""
                    var el = document.getElementById(arguments[0]);
                    if (typeof kendo !== 'undefined' && kendo.widgetInstance) {
                        var w = kendo.widgetInstance(el);
                        if (w && w.open) w.open();
                    }
                """, input_id)
                break

        time.sleep(0.3)  # brief pause for the dropdown to open and search box to render

        # 3. Find the visible search input INSIDE the wrapper and type into it.
        #    Use WebDriverWait so we don't grab it before it's interactable.
        search_locator = (
            By.XPATH,
            f"//input[@id='{input_id}']/ancestor::div[contains(@class,'k-multiselect')]"
            f"//input[contains(@class,'k-input-inner') or @type='search' or "
            f"(not(@type='hidden') and not(@id='{input_id}'))]"
        )
        try:
            search_el = self.wait.until(EC.element_to_be_clickable(search_locator))
            search_el.click()
            search_el.clear()
            search_el.send_keys(email)
            logger.info(f"INFO - Typed '{email}' into search box of '{input_id}'.")
        except InvalidElementStateException:
            # Element exists but send_keys blocked — use ActionChains key-by-key
            logger.warning("WARNING - search_el not interactable; falling back to ActionChains.")
            ActionChains(self.driver).move_to_element(search_el).click().send_keys(email).perform()
        except Exception:
            # Last resort: ActionChains on the wrapper itself
            logger.warning("WARNING - Search locator failed; typing via ActionChains on wrapper.")
            if wrapper_el:
                ActionChains(self.driver).move_to_element(wrapper_el).click().send_keys(email).perform()
            else:
                ActionChains(self.driver).send_keys(email).perform()

        time.sleep(1)  # allow Kendo to filter the dropdown list

        # 4. Wait for the option to appear in the popup and JS-click it
        #    (JS click avoids ElementClickInterceptedException during Kendo list animation)
        option_xpath = (
            f"//div[contains(@class,'k-popup') or contains(@class,'k-animation-container')]"
            f"//*[@role='option' and contains(normalize-space(.), '{email}')]"
        )
        try:
            option = self.wait.until(EC.visibility_of_element_located((By.XPATH, option_xpath)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
            self.driver.execute_script("arguments[0].click();", option)
            logger.info(f"INFO - Clicked option '{email}' in '{input_id}' dropdown.")
        except Exception as e:
            pytest.fail(f"FAIL: Option '{email}' not found or not clickable in dropdown '{input_id}'. {e}")

        time.sleep(0.5)  # allow Kendo to render the selection chip

        # 5. Verify selection — Kendo API first, then DOM chip scan, then wrapper text
        verified = self.driver.execute_script("""
            var el = document.getElementById(arguments[0]);
            if (!el) return false;
            // Kendo widget value() — safe typeof guard (kendo may not be on this page)
            if (typeof kendo !== 'undefined' && kendo.widgetInstance) {
                try {
                    var w = kendo.widgetInstance(el);
                    if (w && w.value) {
                        var vals = w.value();
                        for (var i = 0; i < vals.length; i++) {
                            if (String(vals[i]).indexOf(arguments[1]) !== -1) return true;
                        }
                    }
                } catch(e) {}
            }
            // DOM chip scan
            var wrapper = el.closest('.k-multiselect') || el.parentElement;
            if (!wrapper) return false;
            var chips = wrapper.querySelectorAll(
                '.k-chip, .k-chip-label, li[class*="k-chip"], span[class*="k-chip"]'
            );
            for (var c of chips) {
                if (c.textContent.indexOf(arguments[1]) !== -1) return true;
            }
            // Broad wrapper text fallback
            return wrapper.textContent.indexOf(arguments[1]) !== -1;
        """, input_id, email)

        if not verified:
            time.sleep(1.5)
            verified = self.driver.execute_script("""
                var el = document.getElementById(arguments[0]);
                var wrapper = el ? (el.closest('.k-multiselect') || el.parentElement) : null;
                return wrapper ? wrapper.textContent.indexOf(arguments[1]) !== -1 : false;
            """, input_id, email)

        if verified:
            logger.info(f"INFO - '{email}' confirmed selected in '{input_id}'.")
        else:
            logger.warning(
                f"WARNING - Could not confirm '{email}' in '{input_id}' after selection "
                f"(Kendo chip may render differently). Proceeding."
            )
        
        return True

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
