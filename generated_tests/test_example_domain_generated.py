"""Generated automatically by the ARES framework."""

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


def test_example_domain_flow() -> None:
    options = ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    try:
        driver.get('https://example.com')

        # Action 1: click
        element = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a'))
        )
        element.click()

        # Generated assertion
        assert 'iana.org' in driver.current_url

    finally:
        driver.quit()


if __name__ == "__main__":
    test_example_domain_flow()
