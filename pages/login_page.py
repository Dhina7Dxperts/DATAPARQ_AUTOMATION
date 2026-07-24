from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.config import Config
from utils.logger import get_logger
import pytest

logger = get_logger("LoginPage")

class LoginPage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)
        
        self.username_locator = (By.XPATH, "//input[@aria-label='Username' or @name='username' or @id='username']")
        self.password_locator = (By.XPATH, "//input[@aria-label='Password' or @name='password' or @id='password']")
        self.login_btn_locator = (By.XPATH, "//button[contains(translate(text(), 'SIGN IN', 'sign in'), 'sign in') or @type='submit']")
        self.dashboard_indicator = (By.XPATH, "//*[contains(text(), 'Welcome')]") # Indicator that dashboard is loaded

    def navigate(self):
        self.driver.get(Config.BASE_URL)

    def login(self):
        # 1. Wait for username and type
        username_field = self.wait.until(EC.visibility_of_element_located(self.username_locator))
        username_field.clear()
        username_field.send_keys(Config.USERNAME)
        
        # 2. Wait for password and type
        password_field = self.wait.until(EC.visibility_of_element_located(self.password_locator))
        password_field.clear()
        password_field.send_keys(Config.PASSWORD)
        
        # 3. Wait until button is clickable before attempting to click it
        login_button = self.wait.until(EC.element_to_be_clickable(self.login_btn_locator))
        login_button.click()
        
    def wait_for_dashboard(self):
        try:
            # 1. Wait for the login page to go away (Sign In button disappears)
            self.wait.until(EC.invisibility_of_element_located(self.login_btn_locator))
            # 2. Wait for the dashboard to load (look for "Dashboard" text instead of "Welcome", since "Welcome" is on the login page)
            dashboard_locator = (By.XPATH, "//*[contains(translate(text(), 'DASHBOARD', 'dashboard'), 'dashboard')]")
            self.wait.until(EC.visibility_of_element_located(dashboard_locator))
            # Verify login successful
            assert True
        except Exception as e:
            pytest.fail(f"FAIL: Dashboard did not load or login was unsuccessful. {e}")

    def is_already_logged_in(self) -> bool:
        """
        Check if the current browser session is already authenticated.
        Returns True ONLY if a known authenticated-app element is visible (sidebar nav).
        This avoids false positives when the login form hasn't rendered yet.
        """
        try:
            # Look for positive proof of authenticated app (left nav sidebar items)
            auth_indicators = [
                (By.XPATH, "//a[@href='/monitor']"),
                (By.XPATH, "//a[contains(@href, 'parq-your-data')]"),
                (By.XPATH, "//div[contains(@class, 'truncate') and normalize-space(text())='Monitor']"),
                (By.XPATH, "//span[normalize-space(text())='OBSERVE & ASK' or normalize-space(text())='OBSERVE &amp; ASK']"),
            ]
            for locator in auth_indicators:
                elements = self.driver.find_elements(*locator)
                if elements and elements[0].is_displayed():
                    return True
            return False
        except Exception:
            return False

    def login_if_needed(self):
        """
        Navigate to the app and login only if not already authenticated.
        Uses positive detection of authenticated sidebar elements to decide.
        Safe to call from any test case in a shared or standalone browser session.
        """
        import time

        # First check if we are already on the authenticated app (no navigation needed)
        if self.is_already_logged_in():
            logger.info("INFO - Session already active (authenticated app visible). Skipping login.")
            return

        # Navigate to the base URL and wait for the page to settle
        self.navigate()
        time.sleep(4)  # Allow SPA redirect to complete

        # Check again after navigation
        if self.is_already_logged_in():
            logger.info("INFO - Session already active after navigation. Skipping login.")
            return

        # Login form must be present — proceed with login
        logger.info("INFO - Not authenticated. Performing login.")
        self.login()
        self.wait_for_dashboard()
        logger.info("INFO - Login successful.")