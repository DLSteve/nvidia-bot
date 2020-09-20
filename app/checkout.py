import logging

import app.util as util
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains


def is_signed_in(driver):
    try:
        driver.find_element_by_id("dr_logout")
        logging.info('Already signed in.')
        return True
    except NoSuchElementException:
        return False


def sign_in(driver, url, username, password):
    logging.info('Signing in.')
    driver.get(url)
    util.wait_for_page(driver, 'NVIDIA Online Store - Checkout')

    if not is_signed_in(driver):
        email = util.wait_for_element(driver, "loginID")
        pwd = util.wait_for_element(driver, "loginPass")

        email.send_keys(username)
        pwd.send_keys(password)

        try:
            action = ActionChains(driver)
            button = util.wait_for_element(driver, 'dr_cc_login')
            action.move_to_element(button).click().perform()
            WebDriverWait(driver, 5).until(ec.staleness_of(button))
        except NoSuchElementException:
            logging.error('Error signing in.')


def add_shipping_payment(driver, code):
    util.wait_for_page(driver, 'NVIDIA Online Store - Checkout')
    logging.info('Selecting saved CC info.')
    try:
        util.wait_for_element(driver, 'cCard0', 5).click()
    except TimeoutException:
        util.wait_for_element(driver, 'cCard1').click()
    util.button_click_using_xpath(driver, "//div[@id='dr_siteButtons']/input[@value='continue']")
    logging.info('Entering security code.')
    security_code = util.wait_for_element(driver, "cardSecurityCode")
    security_code.send_keys(code)
    util.button_click_using_xpath(driver, "//div[@id='dr_siteButtons']/input[@value='continue']")
    try:
        util.wait_for_page(driver, 'NVIDIA Online Store - Address Validation Suggestion Page', 8)
        logging.info('Setting suggested shipping information.')
        util.wait_for_element(driver, 'billingAddressOptionRow1').click()
        util.button_click_using_xpath(driver, "//input[@id='selectionButton']")
    except TimeoutException:
        logging.error("No address Validation required.")

    util.wait_for_page(driver, 'NVIDIA Online Store - Verify Order')
    logging.info('Reached order validation page.')
