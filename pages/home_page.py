from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import get_logger
import pytest

logger = get_logger("HomePage")

class HomePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 15)
        self.parq_module_locator = (By.XPATH, "//*[contains(translate(text(), 'PARQ YOUR DATA', 'parq your data'), 'parq your data')]")
        self.data_lakehouse_locator = (By.XPATH, "//*[contains(translate(text(), 'LAKEHOUSE', 'lakehouse'), 'lakehouse')]")
        self.create_new_locator = (By.XPATH, "//div[.//h4[normalize-space(text())='Data Lakehouse']]//button[.//span[normalize-space(text())='Create New']] | //*[normalize-space(text())='Data Lakehouse']/following::button[.//span[normalize-space(text())='Create New']][1]")

    def open_parq_module(self):
        module_btn = self.wait.until(EC.element_to_be_clickable(self.parq_module_locator))
        module_btn.click()
        
    def verify_parq_module_loaded(self):
        try:
            # Verify "Data Lakehouse" and "Create New" are visible
            self.wait.until(EC.visibility_of_element_located(self.data_lakehouse_locator))
            # wait a bit for elements to load
            self.wait.until(EC.visibility_of_element_located(self.create_new_locator))
        except Exception as e:
            pytest.fail(f"FAIL: ParQ Your Data page failed to load properly. Data Lakehouse or Create New missing. {e}")