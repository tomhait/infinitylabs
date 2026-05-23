import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

REPORT_FILE_PATH = "unread_emails_report.txt"

class WallaMailScraper:
    def __init__(self, email, password, report_path):
        self.email = email
        self.password = password
        self.report_path = report_path
        self.driver = None
        self.wait = None

    def init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 15)

    def login(self):
        self.driver.get("https://friends.walla.co.il/")

        email_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='text']")))
        email_field.send_keys(self.email)
        self.driver.find_element(By.XPATH, "//*[contains(text(), 'המשך')]").click()

        password_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='password']")))
        password_field.send_keys(self.password)
        self.driver.find_element(By.XPATH, "//*[contains(text(), 'חברו אותי')]").click()
        time.sleep(3)

    def navigate_to_inbox(self):
        self.wait.until(EC.url_changes("https://friends.walla.co.il/"))
        self.driver.get("https://mail.walla.co.il/#/folder/inbox")
        time.sleep(8)

    def parse_unread_emails(self):
        print("Scanning inbox...")
        unread_rows = self.driver.find_elements(By.CSS_SELECTOR, "li.mail-list-item.unread")
        unread_emails = []

        for idx, row in enumerate(unread_rows, start=1):
            sender = row.find_element(By.CSS_SELECTOR, ".cell.sender").text.strip()
            subject = row.find_element(By.CSS_SELECTOR, ".cell.subject").text.strip()
            date = row.find_element(By.CSS_SELECTOR, ".cell.date").text.strip()
            unread_emails.append({
                "index": idx,
                "sender": sender,
                "subject": subject,
                "date": date
            })
        return unread_emails

    def save_report(self, unread_emails):
        print(f"Writing findings to {self.report_path}...")
        with open(self.report_path, "w") as f:
            if not unread_emails:
                f.write("No unread emails detected.\n")
                return

            f.write(f"Total Unread Found: {len(unread_emails)}\n\n")
            f.write("-" * 40 + "\n")
            for email in unread_emails:
                f.write(
                    f"[{email['index']}] From: {email['sender']}\n    Subject: {email['subject']}\n"
                    f"    Date: {email['date']}\n")
                f.write("-" * 40 + "\n")

    def start(self):
        try:
            self.init_driver()
            self.login()
            self.navigate_to_inbox()
            emails = self.parse_unread_emails()
            self.save_report(emails)
            print(f"Done! Saved {len(emails)} unread emails.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            if self.driver:
                self.driver.quit()

if __name__ == "__main__":
    WALLA_EMAIL = input("Enter your Email: ")
    WALLA_PASSWORD = input("Enter your password: ")
    scraper = WallaMailScraper(WALLA_EMAIL, WALLA_PASSWORD, REPORT_FILE_PATH)
    scraper.start()