#!/usr/bin/env python3
#encoding=utf-8
# seleniumwire not support python 2.x.
# if you want running under python 2.x, you need to assign driver_type = 'stealth'
import os
import pathlib
import sys
import platform
import json
import random

# for close tab.
from selenium.common.exceptions import NoSuchWindowException
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import WebDriverException
# for alert 2
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# for selenium 4
from selenium.webdriver.chrome.service import Service
# for wait #1
import time
# for error output
import logging
logging.basicConfig()
logger = logging.getLogger('logger')
# for check reg_info
import requests
import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore',InsecureRequestWarning)

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# ocr
import base64
try:
    import ddddocr
    #PS: python 3.11.1 raise PIL conflict.
    from NonBrowser import NonBrowser
except Exception as exc:
    pass

import argparse
import chromedriver_autoinstaller

CONST_APP_VERSION = "Max Interpark Bot (2023.08.01)"

CONST_MAXBOT_CONFIG_FILE = 'settings.json'
CONST_MAXBOT_LAST_URL_FILE = "MAXBOT_LAST_URL.txt"
CONST_MAXBOT_INT28_FILE = "MAXBOT_INT28_IDLE.txt"

CONST_HOMEPAGE_DEFAULT = "https://www.globalinterpark.com/"

CONST_CHROME_VERSION_NOT_MATCH_EN="Please download the WebDriver version to match your browser version."
CONST_CHROME_VERSION_NOT_MATCH_TW="請下載與您瀏覽器相同版本的WebDriver版本，或更新您的瀏覽器版本。"

CONST_WEBDRIVER_TYPE_SELENIUM = "selenium"
CONST_WEBDRIVER_TYPE_UC = "undetected_chromedriver"

def t_or_f(arg):
    ret = False
    ua = str(arg).upper()
    if 'TRUE'.startswith(ua):
        ret = True
    elif 'YES'.startswith(ua):
        ret = True
    return ret

def sx(s1):
    key=18
    return ''.join(chr(ord(a) ^ key) for a in s1)

def decryptMe(b):
    s=""
    if(len(b)>0):
        s=sx(base64.b64decode(b).decode("UTF-8"))
    return s

def encryptMe(s):
    data=""
    if(len(s)>0):
        data=base64.b64encode(sx(s).encode('UTF-8')).decode("UTF-8")
    return data

def get_app_root():
    # 讀取檔案裡的參數值
    basis = ""
    if hasattr(sys, 'frozen'):
        basis = sys.executable
    else:
        basis = sys.argv[0]
    app_root = os.path.dirname(basis)
    return app_root

def get_config_dict(args):
    app_root = get_app_root()
    config_filepath = os.path.join(app_root, CONST_MAXBOT_CONFIG_FILE)

    # allow assign config by command line.
    if not args.input is None:
        if len(args.input) > 0:
            config_filepath = args.input

    config_dict = None
    if os.path.isfile(config_filepath):
        with open(config_filepath) as json_data:
            config_dict = json.load(json_data)
    return config_dict

def write_last_url_to_file(url):
    outfile = None
    if platform.system() == 'Windows':
        outfile = open(CONST_MAXBOT_LAST_URL_FILE, 'w', encoding='UTF-8')
    else:
        outfile = open(CONST_MAXBOT_LAST_URL_FILE, 'w')

    if not outfile is None:
        outfile.write("%s" % url)

def read_last_url_from_file():
    ret = ""
    with open(CONST_MAXBOT_LAST_URL_FILE, "r") as text_file:
        ret = text_file.readline()
    return ret

def get_favoriate_extension_path(webdriver_path):
    print("webdriver_path:", webdriver_path)
    extension_list = []
    extension_list.append(os.path.join(webdriver_path,"Adblock_3.18.1.0.crx"))
    extension_list.append(os.path.join(webdriver_path,"Buster_2.0.1.0.crx"))
    extension_list.append(os.path.join(webdriver_path,"no_google_analytics_1.1.0.0.crx"))
    extension_list.append(os.path.join(webdriver_path,"proxy-switchyomega_2.5.21.0.crx"))
    extension_list.append(os.path.join(webdriver_path,"tampermonkey_4.19.0.0.crx"))
    return extension_list

def get_chromedriver_path(webdriver_path):
    chromedriver_path = os.path.join(webdriver_path,"chromedriver")
    if platform.system().lower()=="windows":
        chromedriver_path = os.path.join(webdriver_path,"chromedriver.exe")
    return chromedriver_path

def get_brave_bin_path():
    brave_path = ""
    if platform.system() == 'Windows':
        brave_path = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        if not os.path.exists(brave_path):
            brave_path = os.path.expanduser('~') + "\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        if not os.path.exists(brave_path):
            brave_path = "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
        if not os.path.exists(brave_path):
            brave_path = "D:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"

    if platform.system() == 'Linux':
        brave_path = "/usr/bin/brave-browser"

    if platform.system() == 'Darwin':
        brave_path = '/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'

    return brave_path

def get_chrome_options(webdriver_path, adblock_plus_enable, browser="chrome", headless = False):
    chrome_options = webdriver.ChromeOptions()
    if browser=="edge":
        chrome_options = webdriver.EdgeOptions()
    if browser=="safari":
        chrome_options = webdriver.SafariOptions()

    # some windows cause: timed out receiving message from renderer
    if adblock_plus_enable:
        # PS: this is ocx version.
        extension_list = get_favoriate_extension_path(webdriver_path)
        for ext in extension_list:
            if os.path.exists(ext):
                chrome_options.add_extension(ext)
    if headless:
        #chrome_options.add_argument('--headless')
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-features=TranslateUI')
    chrome_options.add_argument('--disable-translate')
    chrome_options.add_argument('--lang=zh-TW')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument("--no-sandbox");

    # for navigator.webdriver
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # Deprecated chrome option is ignored: useAutomationExtension
    #chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", {"credentials_enable_service": False, "profile.password_manager_enabled": False, "translate":{"enabled": False}})

    if browser=="brave":
        brave_path = get_brave_bin_path()
        if os.path.exists(brave_path):
            chrome_options.binary_location = brave_path

    chrome_options.page_load_strategy = 'eager'
    #chrome_options.page_load_strategy = 'none'
    chrome_options.unhandled_prompt_behavior = "accept"

    return chrome_options

def load_chromdriver_normal(config_dict, driver_type):
    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    driver = None

    Root_Dir = get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    chromedriver_path = get_chromedriver_path(webdriver_path)

    if not os.path.exists(webdriver_path):
        os.mkdir(webdriver_path)

    if not os.path.exists(chromedriver_path):
        print("WebDriver not exist, try to download...")
        chromedriver_autoinstaller.install(path="webdriver", make_version_dir=False)

    if not os.path.exists(chromedriver_path):
        print("Please download chromedriver and extract zip to webdriver folder from this url:")
        print("請下在面的網址下載與你chrome瀏覽器相同版本的chromedriver,解壓縮後放到webdriver目錄裡：")
        print(URL_CHROME_DRIVER)
    else:
        chrome_service = Service(chromedriver_path)
        chrome_options = get_chrome_options(webdriver_path, config_dict["advanced"]["adblock_plus_enable"], browser=config_dict["browser"], headless=config_dict["advanced"]["headless"])
        try:
            driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        except Exception as exc:
            error_message = str(exc)
            if show_debug_message:
                print(exc)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

            if "This version of ChromeDriver only supports Chrome version" in error_message:
                print(CONST_CHROME_VERSION_NOT_MATCH_EN)
                print(CONST_CHROME_VERSION_NOT_MATCH_TW)

                # remove exist download again.
                try:
                    os.unlink(chromedriver_path)
                except PermissionError:
                    pass
                except FileNotFoundError:
                    pass
                chromedriver_autoinstaller.install(path="webdriver", make_version_dir=False)
                chrome_service = Service(chromedriver_path)
                try:
                    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
                except Exception as exc2:
                    pass


    if driver_type=="stealth":
        from selenium_stealth import stealth
        # Selenium Stealth settings
        stealth(driver,
              languages=["zh-TW", "zh"],
              vendor="Google Inc.",
              platform="Win32",
              webgl_vendor="Intel Inc.",
              renderer="Intel Iris OpenGL Engine",
              fix_hairline=True,
          )
    #print("driver capabilities", driver.capabilities)

    return driver

def clean_uc_exe_cache():
    is_cache_exist = False
    exe_name = "chromedriver%s"

    platform = sys.platform
    if platform.endswith("win32"):
        exe_name %= ".exe"
    if platform.endswith(("linux", "linux2")):
        exe_name %= ""
    if platform.endswith("darwin"):
        exe_name %= ""

    if platform.endswith("win32"):
        d = "~/appdata/roaming/undetected_chromedriver"
    elif "LAMBDA_TASK_ROOT" in os.environ:
        d = "/tmp/undetected_chromedriver"
    elif platform.startswith(("linux", "linux2")):
        d = "~/.local/share/undetected_chromedriver"
    elif platform.endswith("darwin"):
        d = "~/Library/Application Support/undetected_chromedriver"
    else:
        d = "~/.undetected_chromedriver"
    data_path = os.path.abspath(os.path.expanduser(d))

    p = pathlib.Path(data_path)
    files = list(p.rglob("*chromedriver*?"))
    for file in files:
        is_cache_exist = True
        try:
            os.unlink(str(file))
        except PermissionError:
            pass
        except FileNotFoundError:
            pass

    return is_cache_exist

def load_chromdriver_uc(config_dict):
    import undetected_chromedriver as uc

    show_debug_message = True       # debug.
    show_debug_message = False      # online

    if config_dict["advanced"]["verbose"]:
        show_debug_message = True

    Root_Dir = get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    chromedriver_path = get_chromedriver_path(webdriver_path)

    if not os.path.exists(webdriver_path):
        os.mkdir(webdriver_path)

    if not os.path.exists(chromedriver_path):
        print("WebDriver not exist, try to download...")
        chromedriver_autoinstaller.install(path="webdriver", make_version_dir=False)

    options = uc.ChromeOptions()
    options.page_load_strategy = 'eager'
    #options.page_load_strategy = 'none'
    options.unhandled_prompt_behavior = "accept"

    #print("strategy", options.page_load_strategy)

    if config_dict["advanced"]["adblock_plus_enable"]:
        load_extension_path = ""
        extension_list = get_favoriate_extension_path(webdriver_path)
        for ext in extension_list:
            ext = ext.replace('.crx','')
            if os.path.exists(ext):
                load_extension_path += ("," + os.path.abspath(ext))
        if len(load_extension_path) > 0:
            print('load-extension:', load_extension_path[1:])
            options.add_argument('--load-extension=' + load_extension_path[1:])

    if config_dict["advanced"]["headless"]:
        #options.add_argument('--headless')
        options.add_argument('--headless=new')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-translate')
    options.add_argument('--lang=zh-TW')
    options.add_argument('--disable-web-security')
    options.add_argument("--no-sandbox");

    options.add_argument("--password-store=basic")
    options.add_experimental_option("prefs", {"credentials_enable_service": False, "profile.password_manager_enabled": False, "translate":{"enabled": False}})

    if config_dict["browser"]=="brave":
        brave_path = get_brave_bin_path()
        if os.path.exists(brave_path):
            options.binary_location = brave_path

    driver = None
    if os.path.exists(chromedriver_path):
        # use chromedriver_autodownload instead of uc auto download.
        is_cache_exist = clean_uc_exe_cache()

        try:
            driver = uc.Chrome(driver_executable_path=chromedriver_path, options=options, headless=config_dict["advanced"]["headless"])
        except Exception as exc:
            print(exc)
            error_message = str(exc)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

            if "This version of ChromeDriver only supports Chrome version" in error_message:
                print(CONST_CHROME_VERSION_NOT_MATCH_EN)
                print(CONST_CHROME_VERSION_NOT_MATCH_TW)

            # remove exist chromedriver, download again.
            try:
                os.unlink(chromedriver_path)
            except PermissionError:
                pass
            except FileNotFoundError:
                pass

            chromedriver_autoinstaller.install(path="webdriver", make_version_dir=False)
            try:
                driver = uc.Chrome(driver_executable_path=chromedriver_path, options=options, headless=config_dict["advanced"]["headless"])
            except Exception as exc2:
                pass
    else:
        print("WebDriver not found at path:", chromedriver_path)

    if driver is None:
        print('WebDriver object is None..., try again..')
        try:
            driver = uc.Chrome(options=options, headless=config_dict["advanced"]["headless"])
        except Exception as exc:
            print(exc)
            error_message = str(exc)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

            if "This version of ChromeDriver only supports Chrome version" in error_message:
                print(CONST_CHROME_VERSION_NOT_MATCH_EN)
                print(CONST_CHROME_VERSION_NOT_MATCH_TW)
            pass

    if driver is None:
        print("create web drive object by undetected_chromedriver fail!")

        if os.path.exists(chromedriver_path):
            print("Unable to use undetected_chromedriver, ")
            print("try to use local chromedriver to launch chrome browser.")
            driver_type = "selenium"
            driver = load_chromdriver_normal(config_dict, driver_type)
        else:
            print("建議您自行下載 ChromeDriver 到 webdriver 的資料夾下")
            print("you need manually download ChromeDriver to webdriver folder.")

    return driver

def close_browser_tabs(driver):
    if not driver is None:
        try:
            window_handles_count = len(driver.window_handles)
            if window_handles_count > 1:
                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except Exception as excSwithFail:
            pass

def get_driver_by_config(config_dict):
    global driver

    # read config.
    homepage = config_dict["homepage"]

    if not config_dict is None:
        # output config:
        print("maxbot app version", CONST_APP_VERSION)
        print("python version", platform.python_version())
        print("homepage", config_dict["homepage"])
        
        homepage = config_dict["homepage"]

    # entry point
    if homepage is None:
        homepage = ""
    if len(homepage) == 0:
        homepage = CONST_HOMEPAGE_DEFAULT

    Root_Dir = get_app_root()
    webdriver_path = os.path.join(Root_Dir, "webdriver")
    print("platform.system().lower():", platform.system().lower())

    if config_dict["browser"] in ["chrome","brave"]:
        # method 6: Selenium Stealth
        if config_dict["webdriver_type"] != CONST_WEBDRIVER_TYPE_UC:
            driver = load_chromdriver_normal(config_dict, config_dict["webdriver_type"])
        else:
            # method 5: uc
            # multiprocessing not work bug.
            if platform.system().lower()=="windows":
                if hasattr(sys, 'frozen'):
                    from multiprocessing import freeze_support
                    freeze_support()
            driver = load_chromdriver_uc(config_dict)

    if config_dict["browser"] == "firefox":
        # default os is linux/mac
        # download url: https://github.com/mozilla/geckodriver/releases
        chromedriver_path = os.path.join(webdriver_path,"geckodriver")
        if platform.system().lower()=="windows":
            chromedriver_path = os.path.join(webdriver_path,"geckodriver.exe")

        if "macos" in platform.platform().lower():
            if "arm64" in platform.platform().lower():
                chromedriver_path = os.path.join(webdriver_path,"geckodriver_arm")

        webdriver_service = Service(chromedriver_path)
        driver = None
        try:
            from selenium.webdriver.firefox.options import Options
            options = Options()
            if config_dict["advanced"]["headless"]:
                options.add_argument('--headless')
                #options.add_argument('--headless=new')
            if platform.system().lower()=="windows":
                binary_path = "C:\\Program Files\\Mozilla Firefox\\firefox.exe"
                if not os.path.exists(binary_path):
                    binary_path = os.path.expanduser('~') + "\\AppData\\Local\\Mozilla Firefox\\firefox.exe"
                if not os.path.exists(binary_path):
                    binary_path = "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
                if not os.path.exists(binary_path):
                    binary_path = "D:\\Program Files\\Mozilla Firefox\\firefox.exe"
                options.binary_location = binary_path

            driver = webdriver.Firefox(service=webdriver_service, options=options)
        except Exception as exc:
            error_message = str(exc)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)
            else:
                print(exc)

    if config_dict["browser"] == "edge":
        # default os is linux/mac
        # download url: https://developer.microsoft.com/zh-tw/microsoft-edge/tools/webdriver/
        chromedriver_path = os.path.join(webdriver_path,"msedgedriver")
        if platform.system().lower()=="windows":
            chromedriver_path = os.path.join(webdriver_path,"msedgedriver.exe")

        webdriver_service = Service(chromedriver_path)
        chrome_options = get_chrome_options(webdriver_path, config_dict["advanced"]["adblock_plus_enable"], browser="edge", headless=config_dict["advanced"]["headless"])

        driver = None
        try:
            driver = webdriver.Edge(service=webdriver_service, options=chrome_options)
        except Exception as exc:
            error_message = str(exc)
            #print(error_message)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

    if config_dict["browser"] == "safari":
        driver = None
        try:
            driver = webdriver.Safari()
        except Exception as exc:
            error_message = str(exc)
            #print(error_message)
            left_part = None
            if "Stacktrace:" in error_message:
                left_part = error_message.split("Stacktrace:")[0]
                print(left_part)

    if driver is None:
        print("create web driver object fail @_@;")
    else:
        try:
            print("goto url:", homepage)
            driver.get(homepage)
            time.sleep(3.0)
        except WebDriverException as exce2:
            print('oh no not again, WebDriverException')
            print('WebDriverException:', exce2)
        except Exception as exce1:
            print('get URL Exception:', exce1)
            pass

    return driver

def get_current_url(driver):
    DISCONNECTED_MSG = ': target window already closed'

    url = ""
    is_quit_bot = False

    try:
        url = driver.current_url
    except NoSuchWindowException:
        print('NoSuchWindowException at this url:', url )
        #print("last_url:", last_url)
        #print("get_log:", driver.get_log('driver'))
        window_handles_count = 0
        try:
            window_handles_count = len(driver.window_handles)
            #print("window_handles_count:", window_handles_count)
            if window_handles_count >= 1:
                driver.switch_to.window(driver.window_handles[0])
                driver.switch_to.default_content()
                time.sleep(0.2)
        except Exception as excSwithFail:
            #print("excSwithFail:", excSwithFail)
            pass
        if window_handles_count==0:
            try:
                driver_log = driver.get_log('driver')[-1]['message']
                print("get_log:", driver_log)
                if DISCONNECTED_MSG in driver_log:
                    print('quit bot by NoSuchWindowException')
                    is_quit_bot = True
                    driver.quit()
                    sys.exit()
            except Exception as excGetDriverMessageFail:
                #print("excGetDriverMessageFail:", excGetDriverMessageFail)
                except_string = str(excGetDriverMessageFail)
                if 'HTTP method not allowed' in except_string:
                    print('quit bot by close browser')
                    is_quit_bot = True
                    driver.quit()
                    sys.exit()

    except UnexpectedAlertPresentException as exc1:
        print('UnexpectedAlertPresentException at this url:', url )
        # PS: do nothing...
        # PS: current chrome-driver + chrome call current_url cause alert/prompt dialog disappear!
        # raise exception at selenium/webdriver/remote/errorhandler.py
        # after dialog disappear new excpetion: unhandled inspector error: Not attached to an active page
        is_pass_alert = False
        is_pass_alert = True
        if is_pass_alert:
            try:
                driver.switch_to.alert.accept()
            except Exception as exc:
                pass

    except Exception as exc:
        logger.error('Maxbot URL Exception')
        logger.error(exc, exc_info=True)

        #UnicodeEncodeError: 'ascii' codec can't encode characters in position 63-72: ordinal not in range(128)
        str_exc = ""
        try:
            str_exc = str(exc)
        except Exception as exc2:
            pass

        if len(str_exc)==0:
            str_exc = repr(exc)

        exit_bot_error_strings = ['Max retries exceeded'
        , 'chrome not reachable'
        , 'unable to connect to renderer'
        , 'failed to check if window was closed'
        , 'Failed to establish a new connection'
        , 'Connection refused'
        , 'disconnected'
        , 'without establishing a connection'
        , 'web view not found'
        , 'invalid session id'
        ]
        for each_error_string in exit_bot_error_strings:
            if isinstance(str_exc, str):
                if each_error_string in str_exc:
                    print('quit bot by error:', each_error_string)
                    is_quit_bot = True
                    driver.quit()
                    sys.exit()

        # not is above case, print exception.
        print("Exception:", str_exc)
        pass

    return url, is_quit_bot

def facebook_login(driver, account, password):
    ret = False
    el_email = None
    try:
        el_email = driver.find_element(By.CSS_SELECTOR, '#email')
    except Exception as exc:
        pass

    is_visible = False
    if el_email is not None:
        try:
            if el_email.is_enabled():
                is_visible = True
        except Exception as exc:
            pass

    is_email_sent = False
    if is_visible:
        try:
            inputed_text = el_email.get_attribute('value')
            if inputed_text is not None:
                if len(inputed_text) == 0:
                    el_email.send_keys(account)
                    is_email_sent = True
                else:
                    if inputed_text == account:
                        is_email_sent = True
        except Exception as exc:
            pass

    el_pass = None
    if is_email_sent:
        try:
            el_pass = driver.find_element(By.CSS_SELECTOR, '#pass')
        except Exception as exc:
            pass

    is_password_sent = False
    if el_pass is not None:
        try:
            if el_pass.is_enabled():
                inputed_text = el_pass.get_attribute('value')
                if inputed_text is not None:
                    if len(inputed_text) == 0:
                        el_pass.click()
                        if(len(password)>0):
                            el_pass.send_keys(password)
                            el_pass.send_keys(Keys.ENTER)
                            is_password_sent = True
                        time.sleep(0.1)
        except Exception as exc:
            print(exc)
            pass

    ret = is_password_sent

    return ret

def interpark_get_local_code(locale_title):
    code = "en"
    if locale_title == "locale":
        code = "ko"
    if locale_title == "中文":
        code = "zh-cn"
    if locale_title == "日本語":
        code = "ja"
    return code

def interpark_change_locale(driver, config_dict):
    el_locale = None
    try:
        el_locale = driver.find_element(By.CSS_SELECTOR, '#lang_title')
        current_locale = el_locale.text
        if len(current_locale) > 0:
            if config_dict["locale"] != current_locale:
                local_code = interpark_get_local_code(config_dict["locale"])
                js = "fnc_changeLocale('%s');" % (local_code)
                driver.set_script_timeout(1)
                driver.execute_script(js)
                time.sleep(0.2)
    except Exception as exc:
        print(exc)
        pass

def interpark_main(driver, config_dict, url):
    try:
        window_handles_count = len(driver.window_handles)
        if window_handles_count > 1:
            driver.switch_to.window(driver.window_handles[0])
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(0.2)
    except Exception as excSwithFail:
        pass


    if "globalinterpark.com/main/main" in url:
        interpark_change_locale(driver, config_dict)

def main(args):
    config_dict = get_config_dict(args)

    driver = None
    if not config_dict is None:
        driver = get_driver_by_config(config_dict)
    else:
        print("Load config error!")

    # internal variable. 說明：這是一個內部變數，請略過。
    url = ""
    last_url = ""

    ocr = None
    try:
        if config_dict["ocr_captcha"]["enable"]:
            ocr = ddddocr.DdddOcr(show_ad=False, beta=config_dict["ocr_captcha"]["beta"])
    except Exception as exc:
        print(exc)
        pass

    while True:
        time.sleep(0.05)

        # pass if driver not loaded.
        if driver is None:
            print("web driver not accessible!")
            break

        url, is_quit_bot = get_current_url(driver)
        if is_quit_bot:
            break

        if url is None:
            continue
        else:
            if len(url) == 0:
                continue

        is_maxbot_paused = False
        if os.path.exists(CONST_MAXBOT_INT28_FILE):
            is_maxbot_paused = True

        if len(url) > 0 :
            if url != last_url:
                print(url)
                write_last_url_to_file(url)
                if is_maxbot_paused:
                    print("MAXBOT Paused.")
            last_url = url

        if is_maxbot_paused:
            time.sleep(0.2)
            continue

        if len(url) > 0 :
            if url != last_url:
                print(url)
            last_url = url

        if "globalinterpark.com" in url:
            interpark_main(driver, config_dict, url)

        # for facebook
        facebook_login_url = 'https://www.facebook.com/login.php?'
        if url[:len(facebook_login_url)]==facebook_login_url:
            facebook_account = config_dict["advanced"]["facebook_account"].strip()
            if len(facebook_account) > 4:
                facebook_login(driver, facebook_account, decryptMe(config_dict["advanced"]["facebook_password"]))

def cli():
    parser = argparse.ArgumentParser(
            description="MaxBot Aggument Parser")

    parser.add_argument("--input",
        help="config file path",
        type=str)

    parser.add_argument("--homepage",
        help="overwrite homepage setting",
        type=str)

    args = parser.parse_args()
    main(args)

if __name__ == "__main__":
    cli()
