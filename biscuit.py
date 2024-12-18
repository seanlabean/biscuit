#
# Written by Sean Lewis (slewis.wiki) - 2024
# Buscuit is a bite-sized web browser using PyQt5, BeautifulSoup,
# and an optional connection to the OpenAI API.
#
# Any and all of this code may be used by anyone for any purpose.
# I prefer if you give credit if you believe it is due :)
#
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QWidget, QLineEdit, QPushButton, QLabel, 
                             QTextBrowser, QAction, QFileDialog, 
                             QMessageBox, QComboBox)
from PyQt5.QtGui import QIcon

import openai
from bs4 import BeautifulSoup
import yaml

import requests
from time import time
import os
os.environ["XDG_SESSION_TYPE"] = "xcb"

class Browser(QMainWindow):
    def __init__(self):
        """
        Build the app window, functionality, and welcome message.
        """
        super().__init__()
        self.setWindowTitle("BISCUIT")

        # Set up the window layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Create the components: URL bar, Go button, and page display
        self.url_bar = QLineEdit()
        self.layout.addWidget(self.url_bar)

        # Go button and actions
        self.go_button = QPushButton("Go To URL")
        self.aiprompts = QComboBox()
        self.aiprompts.addItem('Summarize')
        self.aiprompts.addItem('Poetify')
        self.aiprompts.addItem('Roast')
        self.aiprompts.addItem('Praise')
        self.prompt_button = QPushButton("AI Shenanigans")

        self.layout.addWidget(self.go_button)
        self.go_button.clicked.connect(self.load_page)
        self.layout.addWidget(self.aiprompts)
        self.layout.addWidget(self.prompt_button)
        self.prompt_button.clicked.connect(self.prompt_html)

        # Init page display and welcome message
        self.page_display = QTextBrowser()
        self.page_display.setReadOnly(True)
        self.page_display.setOpenExternalLinks(False)
        self.page_display.anchorClicked.connect(self.handle_clicked_link)
        self.layout.addWidget(self.page_display)
        self.welcome_page = """
        <html><head></head><body><p>Welcome to <code>BISCUIT</code> ;)</p>
        <p>You are now using a free and open source tool. Feel free to contribute to or repurpose.</p>
        <p>You may save the HTML content of any page you visit via the menu bar.</p>
        <p>Happy Browsing!</p><p>Written by S. C. Lewis</p></body></html>
        """
        self.page_display.setHtml(self.welcome_page)

        # Data info label
        self.info_label = QLabel()
        self.layout.addWidget(self.info_label)

        # Menu bar options
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        save_action = QAction("Save Page As", self)
        save_action.triggered.connect(self.save_page)
        file_menu.addAction(save_action)

        settings_menu = menu_bar.addMenu("Settings")
        theme_action = QAction("Change Theme", self)
        theme_action.triggered.connect(self.change_theme)
        settings_menu.addAction(theme_action)

        dark_theme = """
        QWidget {
        background-color: #2e2e2e;
        color: #ffffff;
        }
        QTextGBrowser {
        background-color: #1e1e1e;
        color: #ffffff;
        }"""
        self.central_widget.setStyleSheet(dark_theme)
        self.page_display.setStyleSheet(dark_theme)
        self.info_label.setStyleSheet(dark_theme)

    def load_page(self):
        """
        Load the web page content from the URL using the BeautifulSoup html parser.
        """
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "https://" + url
        tock = time()
        try:
            response = requests.get(url)
        except:
            fail_text = f"<p>{url} did not respond.</p><br><p>A typo, perhaps?</p>"
            self.handle_failure(fail_text)
            return
        content_length = len(response.content)/1000

        soup = BeautifulSoup(response.content, "html.parser")
        # Remove <figure> and <img> tags
        for tag in soup(["figure", "img"]):
            tag.decompose()

        self.page_display.setHtml(soup.prettify())
        tick = time()

        self.info_label.setText(f"Loaded {content_length:.2f} kB in {tick-tock:.2f} s")

        self.url_bar.setText(url)

    def handle_clicked_link(self, url):
        """
        When a link is clicked, format it to be loaded, and call load_page()
        on the result.
        """
        current_url_text = self.url_bar.text()
        inc_url_text = url.toString()
        if "https" in inc_url_text or "http" in inc_url_text:
            url_str =inc_url_text
        else:
            url_str = ""
            for ext in current_url_text.split('/')[2:]:
                if ext != current_url_text.split('/')[-1] or len(current_url_text.split('/')) == 3:
                    url_str += ext+"/"
            url_str += inc_url_text
        self.url_bar.setText(url_str)
        self.load_page()

    def prompt_html(self):
        """
        Using OpenAI credientials query ChatGPT with an engineered prompt.
        Format and display the response. 
        """
        with open("config.yaml") as stream:
            try:
                config = yaml.safe_load(stream)
                openai_organization_key = config["openai-org"]
                openai_project_key = config["openai-proj"]
            except yaml.YAMLError as exc:
                print(exc)

        current_url_text = self.url_bar.text()
        html_text = self.page_display.toPlainText()
        prompt = f"{html_text[:2000]}"  # Limiting to 2000 characters
        task = self.aiprompts.currentText()

        tock = time()
        try:
            client = openai.OpenAI(
                organization=openai_organization_key,
                project=openai_project_key
            )
        except openai.OpenAIError as e:
            fail_text = f"<p>OpenAI failed to connect. Did you put your OpenAI keys in <code>config.yaml</code>? How about setting the OPENAI_API_KEY env var?</p><p><a href={current_url_text}>Click to go back.</a></p>"
            self.handle_failure(fail_text)
            return
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are helpful assistant."},
                {
                    "role": "user",
                    "content": f"{task} the following webpage in a short, bite-sized response. \
                            Format your response with HTML elements for headers and paragraphs, do not include any \
                            Markdown styling. Ignore any header, footer, and nav elements. \
                            Here is the webpage to {task}: {prompt}"
                }
            ]
        )
        tick=time()
        self.page_display.setHtml(f"<p><a href={current_url_text}>Click to go back.</a></p>" + completion.choices[0].message.content.strip())
        self.info_label.setText(f"{task}: generated in {tick-tock:.2f} s")

    def handle_failure(self, text):
        self.page_display.setHtml(text)
        self.info_label.setText(f"Content failed to load.")
        return

    def save_page(self):
        """
        Open a save dialog to prompt user to save window contents as an
        HTML local file.
        """
        filename, _ = QFileDialog.getSaveFileName(self, "Save Page As", "", "HTML Files (*.html);;All Files (*)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(self.page_display.toHtml())
                QMessageBox.information(self, "Success", f"Page saved successfully to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save page: {str(e)}")
    
    def change_theme(self):
        """
        Swap out the current stylesheet with the other option.
        """
        current_theme = self.central_widget.styleSheet()
        if current_theme:
            theme_out = ""
        else:
            theme_out = """
            QWidget {
            background-color: #2e2e2e;
            color: #ffffff;
            }
            QTextGBrowser {
            background-color: #1e1e1e;
            color: #ffffff;
            }"""
        self.central_widget.setStyleSheet(theme_out)
        self.page_display.setStyleSheet(theme_out)
        self.info_label.setStyleSheet(theme_out)

if __name__ == "__main__":
    app = QApplication([])
    window = Browser()
    window.show()
    app.setWindowIcon(QIcon("biscuit.png"))
    app.exec_()
