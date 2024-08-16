from flask import Flask, render_template, request, send_file
import csv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import io

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate_links', methods=['POST'])
def generate_links():
    ibo_number = request.form['ibo_number']
    links = scrape_links(ibo_number)

    # Create a CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Service', 'Enroll Now Link'])

    for link in links:
        service_name = link.split('/')[-2]  # Example to extract service name from the URL
        writer.writerow([service_name, link])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'{ibo_number}_enroll_links.csv'
    )


def scrape_links(ibo_number):
    options = Options()
    options.headless = True  # Run in headless mode (no browser window)

    driver = webdriver.Firefox(options=options)

    try:
        url = f'https://{ibo_number}.acnibo.com/us-en/services'
        driver.get(url)

        WebDriverWait(driver, 30).until(
            EC.title_contains("Services")
        )

        links = driver.execute_script("""
            return Array.from(document.querySelectorAll('a')).map(link => link.href);
        """)

        service_links = [link for link in links if '/home-services/' in link or '/business-services/' in link]

        enroll_now_links = []

        for service_link in service_links:
            driver.get(service_link)

            try:
                enroll_button = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH,
                                                    "/html/body/div[2]/div/div/section/div/div/div/div/div/div[5]/section/div/div/div/div[2]/a"))
                )

                enroll_now_url = enroll_button.get_attribute('href')
                enroll_now_links.append(enroll_now_url)

            except Exception as e:
                print(f"An error occurred on {service_link}: {e}")

        return enroll_now_links

    finally:
        driver.quit()


if __name__ == '__main__':
    app.run(debug=True)
