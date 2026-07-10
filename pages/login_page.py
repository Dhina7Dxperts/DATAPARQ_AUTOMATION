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
            self.wait.until(EC.visibility_of_element_located(self.dashboard_indicator))
            # Verify login successful
            assert True
        except Exception as e:
            pytest.fail(f"FAIL: Dashboard did not load or login was unsuccessful. {e}")