"""Execute browser actions for ARES."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ActionExecutor:

    def __init__(self, browser):
        self.browser = browser

    @property
    def driver(self):
        return self.browser.driver

    def click_css(self, selector, timeout=10):
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        )
        element.click()

    def type_css(self, selector, text, timeout=10):
        element = WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
        )
        element.clear()
        element.send_keys(text)

    def click_xpath(self, xpath, timeout=10):
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()

    def wait(self, seconds):
        self.driver.implicitly_wait(seconds)