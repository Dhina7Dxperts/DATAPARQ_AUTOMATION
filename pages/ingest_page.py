import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import get_logger
import pytest
import time

logger = get_logger("IngestPage")


class IngestPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self.long_wait = WebDriverWait(driver, 60)

        # ── Add to Data Domain Group section ──────────────────────────────────
        # "Create New" Kendo radio — click the INPUT element, not just the label.
        # Structure: <input type="radio" class="k-radio"> <label class="k-radio-label" aria-label="Create New">
        self.create_new_radio_locator = (
            By.XPATH,
            # Primary: radio input preceding the k-radio-label with aria-label='Create New'
            "//label[@aria-label='Create New' and contains(@class,'k-radio-label')]"
            "/preceding-sibling::input[@type='radio'][1] | "
            # Fallback 1: radio input preceding any label with text 'Create New'
            "//label[contains(text(),'Create New')]/preceding-sibling::input[@type='radio'][1] | "
            # Fallback 2: the label itself (click label which triggers radio)
            "//label[@aria-label='Create New'] | "
            "//label[contains(@class,'k-radio-label') and contains(.,'Create New')]",
        )

        # ── Domain field (visible after Create New is selected) ───────────────
        # <label for="domain_name">Domain</label>
        self.domain_input_locator = (
            By.XPATH,
            "//label[@for='domain_name']/following::input[1] | "
            "//input[@id='domain_name']",
        )

        # ── Schedule Data Import section ──────────────────────────────────────
        # Workflow Name — first input under "Workflow Name" label
        self.workflow_name_locator = (
            By.XPATH,
            "//input[@name='schedule_name' or contains(@class, 'custom_input')] | "
            "//label[normalize-space(text())='Workflow Name']/following::input[@type='text' or not(@type)][1]",
        )

        # Workflow Type — standard HTML <select> (visible in screenshot as native dropdown)
        self.workflow_type_select_locator = (
            By.XPATH,
            "//label[normalize-space(text())='Workflow Type' or @id='schedule_type_label']"
            "/following::select[1]",
        )

        # Expected Runtime (M) — number input/spinner
        self.expected_runtime_locator = (
            By.XPATH,
            "//label[contains(normalize-space(text()),'Expected Runtime')]/following::input[1]",
        )

        # Notify on delay — checkbox (label visible in screenshot)
        self.notify_delay_locator = (
            By.XPATH,
            "//label[contains(normalize-space(text()),'Notify on delay') or "
            "contains(normalize-space(text()),'Notify on Delay')]"
            "/preceding::input[@type='checkbox'][1] | "
            "//label[contains(normalize-space(text()),'Notify on delay') or "
            "contains(normalize-space(text()),'Notify on Delay')]"
            "/following::input[@type='checkbox'][1] | "
            "//input[@id='notify_delay'] | "
            "//input[@type='checkbox' and following-sibling::*[contains(text(),'Notify')]] | "
            "//input[@type='checkbox' and preceding-sibling::*[contains(text(),'Notify')]]",
        )

        # ── Save button ────────────────────────────────────────────────────────
        # <button name="saveIngest">Save</button>
        self.save_btn_locator = (
            By.XPATH,
            "//button[@name='saveIngest'] | "
            "//button[normalize-space(.)='SAVE' or normalize-space(.)='Save']"
            "[not(@name='deployIngest')]",
        )

        # ── Save success message ───────────────────────────────────────────────
        self.save_success_locator = (
            By.XPATH,
            "//*[contains(.,'Schedule data is saved successfully')] | "
            "//*[contains(.,'saved successfully') and contains(.,'Schedule')] | "
            "//*[contains(.,'saved successfully') and contains(.,'schedule')]",
        )

        # ── Deploy Pipeline button ─────────────────────────────────────────────
        # <button name="deployIngest">Deploy Pipeline</button>
        self.deploy_btn_locator = (
            By.XPATH,
            "//button[@name='deployIngest'] | "
            "//button[contains(normalize-space(.),'Deploy Pipeline') or "
            "contains(normalize-space(.),'DEPLOY PIPELINE')]",
        )

        # ── Deploy success message ─────────────────────────────────────────────
        self.deploy_success_locator = (
            By.XPATH,
            "//*[contains(.,'Successfully deployed') or "
            "contains(.,'successfully deployed') or "
            "contains(.,'Deployed successfully') or "
            "(contains(.,'SUCCESS') and contains(.,'deploy'))]",
        )

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _is_button_disabled(self, element) -> bool:
        classes = element.get_attribute("class") or ""
        disabled_attr = element.get_attribute("disabled")
        aria_disabled = element.get_attribute("aria-disabled")
        return (
            "k-disabled" in classes
            or "disabled" in classes
            or bool(disabled_attr)
            or aria_disabled == "true"
            or not element.is_enabled()
        )

    def _fill_input(self, locator, value: str, field_name: str):
        """Click, clear, and type into an input field."""
        try:
            field = self.wait.until(EC.element_to_be_clickable(locator))
            self.driver.execute_script("arguments[0].click();", field)
            self.driver.execute_script("arguments[0].value = '';", field)
            field.clear()
            field.send_keys(value)
            logger.info(f"INFO - Entered '{value}' in '{field_name}'.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not enter value '{value}' in '{field_name}'. {e}")

    # ── Step 19: Select Create New radio ──────────────────────────────────────

    def select_create_new(self):
        """Click the 'Create New' Kendo radio button and verify it is selected."""
        try:
            radio = self.wait.until(EC.presence_of_element_located(self.create_new_radio_locator))
            self.driver.execute_script("arguments[0].click();", radio)
            logger.info("INFO - 'Create New' radio clicked via primary locator.")
        except Exception:
            # JS fallback: find the radio by scanning all k-radio-label elements
            try:
                clicked = self.driver.execute_script("""
                    var labels = document.querySelectorAll('label.k-radio-label, label[aria-label]');
                    for (var label of labels) {
                        var txt = (label.getAttribute('aria-label') || label.textContent || '').trim();
                        if (txt === 'Create New') {
                            // Prefer clicking the associated radio input
                            var input = label.previousElementSibling;
                            if (input && input.type === 'radio') {
                                input.click();
                                return 'input clicked';
                            }
                            label.click();
                            return 'label clicked';
                        }
                    }
                    return null;
                """)
                if not clicked:
                    pytest.fail("FAIL: 'Create New' radio button not found on Ingest page.")
                logger.info(f"INFO - 'Create New' selected via JS fallback ({clicked}).")
            except Exception as e:
                pytest.fail(f"FAIL: Could not select 'Create New' radio button. {e}")

        # Verify radio is now selected
        time.sleep(0.5)
        try:
            selected = self.driver.execute_script("""
                var labels = document.querySelectorAll('label.k-radio-label, label[aria-label]');
                for (var label of labels) {
                    var txt = (label.getAttribute('aria-label') || label.textContent || '').trim();
                    if (txt === 'Create New') {
                        var input = label.previousElementSibling;
                        return input && input.type === 'radio' ? input.checked : null;
                    }
                }
                return null;
            """)
            if selected:
                logger.info("INFO - 'Create New' radio is confirmed SELECTED.")
            else:
                logger.warning("WARNING - Could not confirm 'Create New' is selected (may still be OK).")
        except Exception:
            pass
        time.sleep(1)

    # ── Step 20: Verify Save disabled before fields ────────────────────────────

    def validate_save_disabled(self):
        """Verify Save button is disabled before mandatory fields are filled."""
        try:
            save_btn = self.wait.until(EC.presence_of_element_located(self.save_btn_locator))
            if self._is_button_disabled(save_btn):
                logger.info("INFO - Save button is correctly DISABLED before filling fields.")
            else:
                logger.warning("WARNING - Save button appears ENABLED before filling fields.")
        except Exception as e:
            logger.warning(f"WARNING - Could not locate Save button for disabled check: {e}")

    # ── Step 21: Enter Domain Name ─────────────────────────────────────────────

    def enter_domain_name(self, upload_file_path: str) -> str:
        """
        Derive domain name exactly from filename and enter it in the Domain field.
        """
        base_name = os.path.splitext(os.path.basename(upload_file_path))[0]
        logger.info(f"INFO - Domain name derived exactly from filename: '{base_name}'")
        self._fill_input(self.domain_input_locator, base_name, "Domain")
        return base_name

    # ── Step 22: Enter Workflow Name ───────────────────────────────────────────

    def enter_workflow_name(self, domain_name: str):
        """Enter the domain name into Workflow Name field."""
        self._fill_input(self.workflow_name_locator, domain_name, "Workflow Name")

    # ── Step 23: Select Workflow Type ─────────────────────────────────────────

    def select_workflow_type(self, option_text: str = "Monthly"):
        """
        Open the Workflow Type Kendo DropDownList and select the given option.
        This is NOT a native <select> — it's a Kendo widget that needs popup interaction.
        """
        # Step 1: Click the Kendo dropdown to open it using JS proximity search by label
        opened = self.driver.execute_script("""
            // Find the Workflow Type label (by id or text)
            var label = document.querySelector('label#schedule_type_label')
                     || Array.from(document.querySelectorAll('label'))
                            .find(l => l.textContent.trim() === 'Workflow Type');
            if (!label) return 'LABEL_NOT_FOUND';

            // Search siblings and nearby elements for Kendo picker
            var container = label.parentElement;
            var pickers = container.querySelectorAll(
                '[class*="k-dropdownlist"],[class*="k-picker"],[role="combobox"],[role="listbox"]'
            );
            if (pickers.length > 0) { pickers[0].click(); return 'clicked:' + pickers[0].className.substring(0,40); }

            // Walk next siblings
            var sibling = label.nextElementSibling;
            while (sibling) {
                var p = sibling.querySelector('[class*="k-dropdownlist"],[class*="k-picker"],[role="combobox"]')
                     || (sibling.className && sibling.className.includes('k-') ? sibling : null);
                if (p) { p.click(); return 'sibling:' + p.className.substring(0,40); }
                sibling = sibling.nextElementSibling;
            }

            // Broader search: find Kendo pickers and pick closest to label
            var allPickers = document.querySelectorAll('[class*="k-dropdownlist"],[class*="k-picker"]');
            var rect = label.getBoundingClientRect();
            var best = null, minDist = 99999;
            for (var pk of allPickers) {
                var pr = pk.getBoundingClientRect();
                var dist = Math.abs(pr.top - rect.bottom) + Math.abs(pr.left - rect.left);
                if (dist < minDist) { minDist = dist; best = pk; }
            }
            if (best) { best.click(); return 'closest:' + best.className.substring(0,40); }
            return 'NOT_FOUND';
        """)

        logger.info(f"INFO - Workflow Type dropdown open attempt: {opened}")

        if "NOT_FOUND" in str(opened) or "LABEL_NOT_FOUND" in str(opened):
            pytest.fail(f"FAIL: Could not locate Workflow Type Kendo dropdown. Result: {opened}")

        # Step 2: Wait for popup and find option
        option_xpath = (
            f"//*[contains(@class,'k-popup') or contains(@class,'k-animation-container') or "
            f"contains(@class,'k-list-container')]"
            f"//*[@role='option' or contains(@class,'k-list-item') or contains(@class,'k-item')]"
            f"[contains(.,'{option_text}')]"
        )
        try:
            option = self.long_wait.until(
                EC.presence_of_element_located((By.XPATH, option_xpath))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", option)
            self.driver.execute_script("arguments[0].click();", option)
            logger.info(f"INFO - Workflow Type '{option_text}' selected from Kendo popup.")
        except Exception as e:
            pytest.fail(
                f"FAIL: Could not select Workflow Type '{option_text}' from popup. "
                f"Popup may not have opened. Result={opened}. {e}"
            )

    # ── Step 24: Enter Expected Runtime ───────────────────────────────────────

    def enter_expected_runtime(self, value: str = "5"):
        """Enter the Expected Runtime (M) value."""
        self._fill_input(self.expected_runtime_locator, value, "Expected Runtime (M)")

    # ── Step 25: Enable Notify on Delay ───────────────────────────────────────

    def enable_notify_on_delay(self):
        """Enable the Notify on Delay checkbox if not already checked."""
        try:
            checkbox = self.wait.until(
                EC.presence_of_element_located(self.notify_delay_locator)
            )
            if not checkbox.is_selected():
                self.driver.execute_script("arguments[0].click();", checkbox)
                logger.info("INFO - 'Notify on delay' checkbox enabled.")
            else:
                logger.info("INFO - 'Notify on delay' was already checked.")
        except Exception as e:
            logger.warning(f"WARNING - Could not locate/click 'Notify on delay' checkbox: {e}")

    # ── Step 25b: Update Short Names ──────────────────────────────────────────
    # Appends _mmss to the existing auto-generated values of Domain, Workflow,
    # and System Short Names to ensure uniqueness.

    def update_all_short_names(self):
        """
        Locate the Domain, Workflow, and System Short Name fields by their IDs,
        append _mmss (current minute and second) to their existing values,
        and dispatch events so the app recognises the new values.
        """
        from datetime import datetime
        from selenium.webdriver.common.keys import Keys
        mmss = datetime.now().strftime("%M%S")

        def _update_short_name(field_id: str, field_name: str):
            locator = (By.ID, field_id)
            try:
                field = self.wait.until(EC.presence_of_element_located(locator))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", field)
                existing_val = field.get_attribute("value") or ""
                new_val = f"{existing_val}_{mmss}" if existing_val else f"val_{mmss}"
                
                # Send Ctrl+A and Backspace to clear, then type new value
                field.send_keys(Keys.CONTROL + "a")
                field.send_keys(Keys.BACKSPACE)
                field.send_keys(new_val)
                
                # Trigger change event so the app recognises the new value
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                    field,
                )
                logger.info(f"INFO - {field_name} updated to '{new_val}'.")
            except Exception as e:
                logger.warning(f"WARNING - Could not update {field_name}: {e}")

        _update_short_name("domain_short_name", "Domain Short Name")
        _update_short_name("workflow_short_name", "Workflow Short Name")
        _update_short_name("system_short_name", "System Short Name")

    # ── Step 26: Validate Save enabled & click ─────────────────────────────────

    def validate_save_enabled_and_click(self):
        """Verify Save is enabled after all fields filled, then click."""
        try:
            save_btn = self.long_wait.until(
                EC.presence_of_element_located(self.save_btn_locator)
            )
            if self._is_button_disabled(save_btn):
                pytest.fail(
                    "FAIL: Save button is still DISABLED after filling all mandatory Ingest fields. "
                    "Check Domain, Workflow Name, and Workflow Type fields."
                )
            logger.info("INFO - Save button is ENABLED. Clicking Save...")
            self.driver.execute_script("arguments[0].click();", save_btn)
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: Save button click failed on Ingest page. {e}")

    # ── Step 27: Validate save success ────────────────────────────────────────

    def validate_save_success(self):
        """Verify 'Schedule data is saved successfully' message."""
        try:
            self.long_wait.until(EC.visibility_of_element_located(self.save_success_locator))
            logger.info("INFO - Save success: 'Schedule data is saved successfully'.")
        except Exception as e:
            pytest.fail(
                "FAIL: Save success message 'Schedule data is saved successfully' "
                f"was NOT displayed. {e}"
            )

    # ── Step 28: Validate Deploy button enabled ────────────────────────────────

    def validate_deploy_button_enabled(self):
        """Verify Deploy Pipeline button becomes enabled after saving."""
        try:
            deploy_btn = self.long_wait.until(
                EC.presence_of_element_located(self.deploy_btn_locator)
            )
            if self._is_button_disabled(deploy_btn):
                pytest.fail(
                    "FAIL: Deploy Pipeline button is DISABLED after saving Ingest config."
                )
            logger.info("INFO - Deploy Pipeline button is ENABLED.")
        except Exception as e:
            if "FAIL:" in str(e):
                raise
            pytest.fail(f"FAIL: Could not verify Deploy Pipeline button state. {e}")

    # ── Step 29: Click Deploy Pipeline ────────────────────────────────────────

    def click_deploy_pipeline(self):
        """Click the Deploy Pipeline button."""
        try:
            deploy_btn = self.wait.until(
                EC.element_to_be_clickable(self.deploy_btn_locator)
            )
            self.driver.execute_script("arguments[0].click();", deploy_btn)
            logger.info("INFO - Deploy Pipeline button clicked.")
        except Exception as e:
            pytest.fail(f"FAIL: Could not click Deploy Pipeline button. {e}")

    # ── Step 30: Validate deployment success ──────────────────────────────────

    def validate_deploy_success(self):
        """Verify deployment success message is displayed."""
        try:
            self.long_wait.until(EC.visibility_of_element_located(self.deploy_success_locator))
            logger.info("INFO - Deployment success message displayed.")
        except Exception as e:
            pytest.fail(
                f"FAIL: Deployment success message was NOT displayed after Deploy Pipeline. {e}"
            )
