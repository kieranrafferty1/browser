import os
import sys
from PyQt5.QtGui import *
from PyQt5.QtWebChannel import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *

class MainWindow(QMainWindow):
    def __init__(self):
        self.events_list = list()

        super(MainWindow, self).__init__()
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://startpage.com"))
        self.setCentralWidget(self.browser)
        self.showNormal()
        self.browser.contextMenuEvent = self.context_menu_event
        self.print_details()

        navbar = QToolBar()
        self.addToolBar(navbar)

        back_btn = QAction("Back", self)
        back_btn.triggered.connect(self.browser.back)
        navbar.addAction(back_btn)

        forward_btn = QAction("Forward", self)
        forward_btn.triggered.connect(self.browser.forward)
        navbar.addAction(forward_btn)

        reload_btn = QAction("Reload", self)
        reload_btn.triggered.connect(self.browser.reload)
        navbar.addAction(reload_btn)

        home_btn = QAction("Home", self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        self.browser.urlChanged.connect(self.update_url)

        self.channel = QWebChannel()
        self.channel.registerObject('pywebchannel', self)
        self.browser.page().setWebChannel(self.channel)
    
    def navigate_home(self):
        self.browser.setUrl(QUrl("https://startpage.com"))
    
    def navigate_to_url(self):
        url = self.url_bar.text()
        self.browser.setUrl(QUrl(url))
    
    def update_url(self, q):
        self.url_bar.setText(q.toString())
    
    def context_menu_event(self, e):
        menu = QMenu(self)

        reload = QAction("Reload")
        reload.triggered.connect(self.browser.reload)
        menu.addAction(reload)

        emergency = QAction("EMERGENCY HIDE")
        emergency.triggered.connect(self.clear_history)
        menu.addAction(emergency)

        if self.is_secure_mode:
            disable = QAction("Disable Secure Mode")
            disable.triggered.connect(self.disable_secure_mode)
            menu.addAction(disable)
        else:
            enable = QAction("Enable Secure Mode")
            enable.triggered.connect(self.enable_secure_mode)
            menu.addAction(enable)

            scrape_menu = QMenu("Scrape Options")

            if not self.is_scraping_enabled:
                scrape_element = QAction("Enable Scraping")
                scrape_element.triggered.connect(self.enable_scraping)
                scrape_menu.addAction(scrape_element)
            else:
                scrape_click = QAction("Click")
                scrape_click.triggered.connect(self.click_element)
                scrape_menu.addAction(scrape_click)

                scrape_click_type = QAction("Click and Type")
                scrape_click_type.triggered.connect(self.click_type_element)
                scrape_menu.addAction(scrape_click_type)

                scrape_text = QAction("Text")
                scrape_text.triggered.connect(self.get_element_text)
                scrape_menu.addAction(scrape_text)

                scrape_save_image = QAction("Save image")
                scrape_save_image.triggered.connect(self.save_image_element)
                scrape_menu.addAction(scrape_save_image)

                scrape_navigate = QAction("Navigate to this URL")
                scrape_navigate.triggered.connect(self.scrape_navigate)
                scrape_menu.addAction(scrape_navigate)

                scrape_save_page = QAction("Save page as pdf")
                scrape_save_page.triggered.connect(self.save_page_pdf)
                scrape_menu.addAction(scrape_save_page)

                scrape_finish = QAction("Finish")
                scrape_finish.triggered.connect(self.finish_scrape)
                scrape_menu.addAction(scrape_finish)
            menu.addMenu(scrape_menu)

        mute = QAction("Toggle Mute")
        mute.triggered.connect(self.toggle_mute)
        menu.addAction(mute)

        menu.exec_(e.globalPos())
    
    def clear_history(self):
        self.browser.history().clear()
        self.navigate_home()
    
    def disable_secure_mode(self):
        for x in range(32):
            self.browser.settings().resetAttribute(x)
        self.is_secure_mode = False
        self.browser.reload()
    
    def enable_secure_mode(self):
        for x in range(32):
            self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute(x), False)
        self.is_secure_mode = True
        self.is_scraping_enabled = False
        self.browser.reload()
    
    def toggle_mute(self):
        if (self.browser.page().isAudioMuted()):
            self.browser.page().setAudioMuted(False)
            self.browser.page().javaScriptAlert(self.browser.page().url(), "Unmuted")
            print("Unmuted")
        else:
            self.browser.page().setAudioMuted(True)
            self.browser.page().javaScriptAlert(self.browser.page().url(), "Muted")
            print("Muted")

    def print_details(self):
        print(f"Audio muted -> {self.browser.page().isAudioMuted()}")

    def enable_scraping(self):
        self.is_scraping_enabled = True
    
    def disable_scraping(self):
        self.is_scraping_enabled = False
    
    def click_element(self):
        self.events_list.append("click")
        self.print_xpath()
    
    def click_type_element(self):
        self.events_list.append("type")
        self.print_xpath()
    
    def get_element_text(self):
        self.events_list.append("text")
        self.print_xpath()

    def save_image_element(self):
        # todo
        pass

    def scrape_navigate(self):
        self.events_list.append("navigate")
        self.events_list.append(self.browser.url().toString())

    def save_page_pdf(self):
        # todo
        pass

    def finish_scrape(self):
        convert_to_selenium(self.events_list)

    def print_xpath(self):
        qwebchannel_js = QFile(':/qtwebchannel/qwebchannel.js')
        if not qwebchannel_js.open(QIODevice.ReadOnly):
            raise SystemExit(
            'Failed to load qwebchannel.js with error: %s' %
            qwebchannel_js.errorString())
        qwebchannel_js = bytes(qwebchannel_js.readAll()).decode('utf-8')

        self.browser.page().runJavaScript(qwebchannel_js + """
            var pywebchannel;
            new QWebChannel(qt.webChannelTransport, function (channel) {
                pywebchannel = channel.objects.pywebchannel;
            });

            function getElementXPath(elt) {
                var path = "";
                for (; elt && elt.nodeType == 1; elt = elt.parentNode) {
                    var idx = getElementIdx(elt);
                    var xname = elt.tagName;
                    if (idx > 1) xname += "[" + idx + "]";
                    path = "/" + xname + path;
                }
                return path;
            }

            function getElementIdx(elt) {
                var count = 1;
                for (var sib = elt.previousSibling; sib; sib = sib.previousSibling) {
                    if (sib.nodeType == 1 && sib.tagName == elt.tagName) count++
                }
                return count;
            }

            function attachGetXPath() {
                document.addEventListener('contextmenu', function(event) {
                    var xpath = getElementXPath(event.target);
                    event.stopPropagation();
                    event.preventDefault();
                    pywebchannel.qtWebKitCallback(xpath);
                }, { once: true });
            }

            attachGetXPath();
        """)
    
    @pyqtSlot(str)
    def qtWebKitCallback(self, xpath):
        self.events_list.append(xpath)

def convert_to_selenium(events):
    code = "from selenium import webdriver\n"
    code += "from selenium.webdriver.common.keys import Keys\n"
    code += "from selenium.webdriver.common.by import By\n"
    code += "from selenium.webdriver.support.ui import WebDriverWait\n"
    code += "from selenium.webdriver.support import expected_conditions as EC\n\n"

    code += f"# Chrome webdriver options\n"
    code += "options = webdriver.ChromeOptions()\n"
    code += "options.add_argument(\"ignore-certificate-errors\")\n"
    code += "options.add_experimental_option(\"detach\", True)\n\n"

    code += f"# Load first page\n"
    code += "driver = webdriver.Chrome(\"webdriver.exe\", chrome_options=options)\n"
    code += "driver.get(\"https://startpage.com\") # Change me\n\n"

    for x in range(0, len(events), 2):
        counter = int(x/2+1)

        if events[x] == "navigate":
            code += f"# Change URL\n"
            code += f"driver.get(\"{events[x+1]}\")\n\n"
        else:
            code += create_new_element(events[x+1], counter)

            if events[x] == "click":
                code += f"element{counter}.click()\n\n"
            elif events[x] == "text":
                code += f"element{counter}_text = element{counter}.text\n"
                code += f"print(element{counter}_text)\n\n"
    
    code += "driver.close()\n"

    f = open(os.path.join(os.getcwd(), "scrape.py"), "w")
    f.write(code)
    f.close()
    print(code)
    print("\n\nWritten to scrape.py")

def create_new_element(xpath, counter):
    code = f"# Element {counter}\n"
    code += f"element{counter}_xpath = \"{xpath}\"\n"
    code += f"WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, element{counter}_xpath)))\n"
    code += f"element{counter} = driver.find_element(By.XPATH, element{counter}_xpath)\n"
    return code

app = QApplication(sys.argv)
QApplication.setApplicationName("Browser")
window = MainWindow()
app.exec_()