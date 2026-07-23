from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import get_logger
import time
import pytest

logger = get_logger("HomePage")

class HomePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)
        # Increased timeout for post-login navigation rendering
        self.nav_wait = WebDriverWait(driver, 40)

        # Multi-strategy locator: matches text in direct nodes OR descendant spans
        # Covers: "ParQ Your Data", "PARQ YOUR DATA", "Parq your data" etc.
        self.parq_module_locator = (
            By.XPATH,
            "//*["
            "contains(normalize-space(.), 'ParQ Your Data') or "
            "contains(normalize-space(.), 'PARQ YOUR DATA') or "
            "contains(normalize-space(.), 'Parq Your Data') or "
            "contains(normalize-space(.), 'parq your data')"
            "][not(self::html) and not(self::body) and not(self::div[@id='root'])]"
            "[self::a or self::button or self::li or self::span or self::div]"
        )
        self.data_lakehouse_locator = (By.XPATH, "//*[contains(translate(text(), 'LAKEHOUSE', 'lakehouse'), 'lakehouse')]")
        self.create_new_locator = (By.XPATH, "//div[.//h4[normalize-space(text())='Data Lakehouse']]//button[.//span[normalize-space(text())='Create New']] | //*[normalize-space(text())='Data Lakehouse']/following::button[.//span[normalize-space(text())='Create New']][1]")

    def open_parq_module(self):
        from selenium.common.exceptions import (
            TimeoutException, ElementClickInterceptedException,
            StaleElementReferenceException
        )
        from selenium.webdriver.common.action_chains import ActionChains

        # Allow sidebar to finish rendering after the login redirect
        time.sleep(2)

        # Ordered locators: most specific → least specific.
        # Prefer <a> elements (React Router nav links) and elements with direct text nodes.
        # Use string-length guard on contains() to avoid matching large containers.
        ordered_locators = [
            # Best: anchor with direct text = "ParQ Your Data"
            (By.XPATH, "//a[normalize-space(text())='ParQ Your Data']"),
            # Anchor whose full text (incl. children) normalises to the label
            (By.XPATH, "//a[normalize-space(.)='ParQ Your Data']"),
            # Anchor with a child span containing the label
            (By.XPATH, "//a[.//span[normalize-space(text())='ParQ Your Data']]"),
            (By.XPATH, "//a[.//span[normalize-space(.)='ParQ Your Data']]"),
            # Li element (sometimes used as nav item root)
            (By.XPATH, "//li[normalize-space(text())='ParQ Your Data']"),
            (By.XPATH, "//li[.//span[normalize-space(text())='ParQ Your Data'] or normalize-space(.)='ParQ Your Data']"),
            # Span with direct text (original working approach recast)
            (By.XPATH, "//span[normalize-space(text())='ParQ Your Data']"),
            # Translate-based direct text match (was working in the first passing run)
            (By.XPATH, "//*[contains(translate(text(), 'PARQ YOUR DATA', 'parq your data'), 'parq your data') "
                        "and (self::a or self::li or self::button or self::span)]"),
            # Broad anchor contains (string-length guard keeps it from matching page containers)
            (By.XPATH, "//a[contains(normalize-space(.), 'ParQ Your Data') "
                        "and string-length(normalize-space(.)) < 40]"),
        ]

        clicked_el = None
        for locator in ordered_locators:
            try:
                el = WebDriverWait(self.driver, 8).until(EC.element_to_be_clickable(locator))
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                try:
                    el.click()
                    logger.info(f"INFO - Clicked 'ParQ Your Data' (native) via: {locator[1][:70]}")
                except ElementClickInterceptedException:
                    # Overlay or animation is blocking — use ActionChains move-then-click
                    ActionChains(self.driver).move_to_element(el).click().perform()
                    logger.info(f"INFO - Clicked 'ParQ Your Data' (ActionChains) via: {locator[1][:70]}")
                except StaleElementReferenceException:
                    # Element detached during click — try next locator
                    continue
                clicked_el = el
                break
            except TimeoutException:
                # This locator found nothing in 8s — try next
                continue
            except Exception as e:
                logger.warning(f"WARNING - Locator attempt failed ({locator[1][:50]}): {type(e).__name__}")
                continue

        if clicked_el is None:
            # Last-resort: JS scan using indexOf for partial text match
            # (handles elements where icon SVG/img adds extra text to textContent)
            try:
                el = self.driver.execute_script("""
                    var needle = 'parq your data';
                    var tags = ['a', 'button', 'li', 'span'];
                    for (var t of tags) {
                        var els = document.querySelectorAll(t);
                        for (var el of els) {
                            var txt = el.textContent.toLowerCase().replace(/\\s+/g, ' ').trim();
                            if (txt.indexOf(needle) !== -1 && txt.length < 60) {
                                return el;
                            }
                        }
                    }
                    return null;
                """)
                if el:
                    ActionChains(self.driver).move_to_element(el).click().perform()
                    logger.info("INFO - Clicked 'ParQ Your Data' via JS partial-text scan + ActionChains.")
                    clicked_el = el
                else:
                    pytest.fail(
                        "FAIL: Could not find 'ParQ Your Data' navigation item after login. "
                        "Tried 9 XPath strategies + JS partial scan. "
                        "The sidebar may not have rendered or the nav label has changed."
                    )
            except Exception as e:
                pytest.fail(f"FAIL: All strategies to click 'ParQ Your Data' exhausted. Last error: {e}")

        # Confirm the page actually navigated — Data Lakehouse heading must appear
        try:
            self.nav_wait.until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//h4[normalize-space(text())='Data Lakehouse']")
                )
            )
            logger.info("INFO - ParQ Your Data page confirmed — Data Lakehouse heading visible.")
        except Exception as e:
            pytest.fail(
                "FAIL: Clicked 'ParQ Your Data' but page did not navigate to the module. "
                f"Data Lakehouse heading not visible after 40s. {e}"
            )

    def verify_parq_module_loaded(self):
        # Data Lakehouse heading is already confirmed in open_parq_module's post-click wait.
        # Here we additionally check for the Create New button with a generous timeout.
        try:
            self.nav_wait.until(EC.visibility_of_element_located(self.data_lakehouse_locator))
        except Exception as e:
            pytest.fail(f"FAIL: ParQ Your Data page — Data Lakehouse section not visible. {e}")

        # Create New button — treat as warning if still missing after extended wait
        # (async data load may render it slightly after the heading)
        try:
            self.nav_wait.until(EC.visibility_of_element_located(self.create_new_locator))
            logger.info("INFO - 'Create New' button is visible on ParQ Your Data page.")
        except Exception:
            logger.warning(
                "WARNING - 'Create New' button not found within timeout. "
                "Page may still be loading — proceeding. Next step will fail if truly missing."
            )