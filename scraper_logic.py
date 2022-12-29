from tqdm import tqdm
import time
import requests
from selenium import webdriver  # , WebDriverWait
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from datetime import datetime
from DB import columns
from gcloud_test import OCR, OCR1
from pyproj import Transformer
import logging
import tempfile
import uuid
import os
import random

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

trans_itm_to_wgs84 = Transformer.from_crs(2039, 4326)
trans_wgs84_itm = Transformer.from_crs(4326, 2039)
SLEEP_THROTTLE_TIME_SEC = 10 * 60  # was 12 check if 14 is better
WAIT_TIME_TIMEOUT = 120  # wait for load issues...
THROTTLE_LIMIT_BEFORE_SLEEP = 70  # 80

main_table_id = "ContentUsersPage_GridMultiD1"
back_id = "ContentUsersPage_btHazaraStart"

user_agents = [
    'Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
    'Mozilla/5.0 (Windows NT 6.1; WOWNT64; rv:54.0) Gecko/20100101 Firefox/54.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
    'Mozilla/5.0 (Windows NT 5.1; rv:36.0) Gecko/20100101 Firefox/36.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0',
    'Mozilla/5.0 (Windows NT 5.1; rv:33.0) Gecko/20100101 Firefox/33.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Rv:50.0) Gecko/20100101 Firefox/50.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:43.0) Gecko/20100101 Firefox/43.0',
    'Mozilla/5.0 (Windows NT 6.0; rv:34.0) Gecko/20100101 Firefox/34.0',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.7.12) Gecko/20050915 Firefox/1.0.7',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:17.0) Gecko/20100101 Firefox/17.0',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
]


def sleep(ts):
    # ts = 5
    for _ in tqdm(list(range(ts)), desc="Waiting...", position=0, leave=True):
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            logging.info("Oh! You have sent a Keyboard Interrupt to me.\nBye, Bye")
            break


def convert_itm_to_wgs84(x, y):
    return trans_itm_to_wgs84.transform(x, y)


def convert_wgs84_to_itm(lat, long):
    itm_cords = trans_wgs84_itm.transform(lat, long)
    return round(itm_cords[0]), round(itm_cords[1])


class Scraper:
    def __init__(self, proxy_ip=None, silent=None):
        PATH = "geckodriver.exe"
        self.proxy_ip = proxy_ip
        profile = webdriver.FirefoxProfile()
        if proxy_ip:
            webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
                "httpProxy": proxy_ip,
                # "ftpProxy": proxy_ip,
                "sslProxy": proxy_ip,
                "proxyType": "MANUAL",

            }
        ### HEADLESS OPTION
        firefox_options = webdriver.FirefoxOptions()
        if silent:
            firefox_options.headless = True
            # firefox_options.add_argument("-s")
        import random
        # old = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
        profile.set_preference("general.useragent.override", f"{random.choice(user_agents)} {str(uuid.uuid4())}")
        self.driver = webdriver.Firefox(executable_path=PATH, options=firefox_options)  # , firefox_profile=profile
        self.ocr = OCR1()
        self.url = "https://nadlan.taxes.gov.il/svinfonadlan2010/startpageNadlanNewDesign.aspx"
        # FIND GUSH HELKA: https://www.gov.il/apps/mapi/parcel_address/parcel_address.html
        # self.url = "https://mylocation.org/"
        # self.driver.set_page_load_timeout(5)
        # self.driver.get(self.url)
        # NoSuchWindowException - oocures when the website stalls the crawler        self.throttle_total_fetched = 0
        self._from_gush = None
        self._to_gush = None
        self._date = None
        self._from_room = None
        self._to_room = None
        self._from_year = None
        self._to_year = None
        self._past_ocr_text = ""
        self.throttle_total_fetched = 0

    def close(self):
        self.driver.close()
        self.driver.quit()
    def get_page(self, timeout=20):
        self.driver.set_page_load_timeout(timeout)
        self.driver.get(self.url)
        logging.info(self.driver.title)

    def restart_page(self, reset_details=True):
        self.driver.get(self.url)
        if reset_details:
            self.reset_details()
        logging.info("Restarted page")

    def change_proxy(self, proxy):
        self.proxy_ip = proxy
        # curr_url = self.driver.current_url
        self.driver.get("about:config")
        host = proxy.split(':')[0]
        port = proxy.split(':')[1]
        user_agent = f"{random.choice(user_agents)} {str(uuid.uuid4())}"
        setupScript = f"""var
            prefs = Components.classes["@mozilla.org/preferences-service;1"].getService(Components.interfaces.nsIPrefBranch);
            prefs.setIntPref("network.proxy.type", 1);
            prefs.setCharPref("network.proxy.http", "{host}");
            prefs.setIntPref("network.proxy.http_port", "{port}");
            prefs.setCharPref("network.proxy.ssl", "{host}");
            prefs.setIntPref("network.proxy.ssl_port", "{port}");
            prefs.setCharPref("network.proxy.ftp", "{host}");
            prefs.setIntPref("network.proxy.ftp_port", "{port}");
            prefs.setCharPref("general.useragent.override", "{user_agent}");
            """
        self.driver.execute_script(setupScript)
        time.sleep(.5)
        self.throttle_total_fetched = 0
        # self.driver.get(curr_url)

    # // running
    # script
    # below
    # driver.executeScript(setupScript);
    def fill_details(self, from_gush, to_gush, from_helka=None, to_helka=None):
        # TODO: I think that  rewriting the text here raises some flag, maybe try to first check if equal and edit if needed only.
        self.wait_for_id("rbMegush", WAIT_TIME_TIMEOUT)
        try:
            self.driver.find_element("id", "rbMegush").click()
            self.throttle()
            self.driver.find_element("id", "txtmegusha").clear()
            self.driver.find_element("id", "txtmegusha").send_keys(from_gush)
            self.driver.find_element("id", "txtadGush").clear()
            self.driver.find_element("id", "txtadGush").send_keys(to_gush)
            if from_helka and to_helka:
                self.driver.find_element("id", "txthelka").send_keys(from_helka)
                self.driver.find_element("id", "txtadHelka").send_keys(to_helka)
            # choose deal
            type_property1 = "ContentUsersPage_DDLTypeNehes"
            select = Select(self.driver.find_element("id", type_property1))
            select.select_by_value('1')  # דירת מגורים
            type_property2 = "ContentUsersPage_DDLMahutIska"
            time.sleep(2)
            # self.wait_for_id(type_property2, WAIT_TIME_TIMEOUT)
            select = Select(self.driver.find_element("id", type_property2))
            select.select_by_value('999')  # every type of property
        except Exception as e:
            from telegram_config import send_msg, bot_id, telegram_tom_channel
            # send_msg("CHECK CODE", telegram_tom_channel, bot_id)
            # sleep(120)
            # TODO: Fix for doing this with bots
            raise e

    def fill_range(self, range_str):
        type_property3 = "ContentUsersPage_DDLDateType"
        select = Select(self.driver.find_element("id", type_property3))
        select.select_by_value(range_str)
        # ContentUsersPage_DDLDateType
        # value="2" 3 months, 3 => 6 months, 4=>12 months, 5 => 36 months

    def fill_exact_range(self, from_date, to_date):
        select = Select(self.driver.find_element("id", "ContentUsersPage_DDLDateType"))
        select.select_by_value("1")  # custom option
        self.driver.find_element("id", "ctl00_ContentUsersPage_txtyomMechira_dateInput").send_keys(from_date)
        self.driver.find_element("id", "ctl00_ContentUsersPage_txtadYomMechira_dateInput").send_keys(to_date)

    def fill_rooms(self, from_room, to_room):
        self.driver.find_element("id", "txtHadarimMe").clear()
        self.driver.find_element("id", "txtHadarimAd").clear()
        self.driver.find_element("id", "txtHadarimMe").send_keys(from_room)
        self.driver.find_element("id", "txtHadarimAd").send_keys(to_room)

    def fill_year_built(self, from_year, to_year):
        self.driver.find_element("id", "txtShnatBniyaMe").clear()
        self.driver.find_element("id", "txtShnatBniyaAd").clear()
        self.driver.find_element("id", "txtShnatBniyaMe").send_keys(from_year)
        self.driver.find_element("id", "txtShnatBniyaAd").send_keys(to_year)

    def parse_info_page(self):
        ezor = self.driver.find_element("id", "ContentUsersPage_lblEzor").text
        gush = self.driver.find_element("id", "ContentUsersPage_lblGush").text
        tarIska = self.driver.find_element("id", "ContentUsersPage_lblTarIska").text  # date idiots
        yeshuv = self.driver.find_element("id", "ContentUsersPage_lblYeshuv").text
        rechov = self.driver.find_element("id", "ContentUsersPage_lblRechov").text
        bayit = self.driver.find_element("id", "ContentUsersPage_lblBayit").text
        knisa = self.driver.find_element("id", "ContentUsersPage_lblKnisa").text
        dira = self.driver.find_element("id", "ContentUsersPage_lblDira").text
        mcirMozhar = self.driver.find_element("id", "ContentUsersPage_lblMcirMozhar").text
        mcirMorach = self.driver.find_element("id", "ContentUsersPage_lblMcirMorach").text
        shetachBruto = self.driver.find_element("id", "ContentUsersPage_lblShetachBruto").text
        shetachNeto = self.driver.find_element("id", "ContentUsersPage_lblShetachNeto").text
        shnatBniya = self.driver.find_element("id", "ContentUsersPage_lblShnatBniya").text
        misHadarim = self.driver.find_element("id", "ContentUsersPage_lblMisHadarim").text
        lblKoma = self.driver.find_element("id", "ContentUsersPage_lblKoma").text
        misKomot = self.driver.find_element("id", "ContentUsersPage_lblMisKomot").text
        dirotBnyn = self.driver.find_element("id", "ContentUsersPage_lblDirotBnyn").text
        hanaya = self.driver.find_element("id", "ContentUsersPage_lblHanaya").text
        malit = self.driver.find_element("id", "ContentUsersPage_lblMalit").text
        #
        sugIska = self.driver.find_element("id", "ContentUsersPage_lblSugIska").text
        tifkudBnyn = self.driver.find_element("id", "ContentUsersPage_lblTifkudBnyn").text
        tifkudYchida = self.driver.find_element("id", "ContentUsersPage_lblTifkudYchida").text
        shumaHalakim = self.driver.find_element("id", "ContentUsersPage_lblShumaHalakim").text
        #
        mofaGush = self.driver.find_element("id", "ContentUsersPage_lblMofaGush").text
        tava = self.driver.find_element("id", "ContentUsersPage_lblTava").text
        mahutZchut = self.driver.find_element("id", "ContentUsersPage_lblMahutZchut").text

        info = dict(
            ezor=ezor,
            gush=gush,
            tarIska=tarIska,
            yeshuv=yeshuv,
            rechov=rechov,
            bayit=bayit,
            knisa=knisa,
            dira=dira,
            mcirMozhar=mcirMozhar,
            mcirMorach=mcirMorach,
            shetachBruto=shetachBruto,
            shetachNeto=shetachNeto,
            shnatBniya=shnatBniya,
            misHadarim=misHadarim,
            lblKoma=lblKoma,
            misKomot=misKomot,
            dirotBnyn=dirotBnyn,
            hanaya=hanaya,
            malit=malit,
            sugIska=sugIska,
            tifkudBnyn=tifkudBnyn,
            tifkudYchida=tifkudYchida,
            shumaHalakim=shumaHalakim,
            mofaGush=mofaGush,
            tava=tava,
            mahutZchut=mahutZchut,
        )
        return info

    def go_over_dira_links(self):
        results = []
        id_get_log = "ContentUsersPage_GridMultiD1_LogShow_{}"
        id_get_logs = [id_get_log.format(n) for n in range(0, 13)]
        for id_link_log in id_get_logs:
            try:
                link_button = self.driver.find_element("id", id_link_log)
            except NoSuchElementException:
                continue
            try:
                tries = 5
                for tried in range(tries):
                    link_button.click()
                    # wait for next page to load after click
                    if self.wait_for_id('ContentUsersPage_lblMcirMozhar', WAIT_TIME_TIMEOUT):
                        break
                    logging.warning(f"Retrying to click on link {id_link_log} again ({tried + 1}/{tries})")

                info = self.parse_info_page()
                logging.info(f"Parsed element - {id_link_log} - {info['gush']} ({self.throttle_total_fetched})")
                results.append(info)
                self.driver.find_element("id", "ContentUsersPage_btHazara").click()
                self.wait_for_id(main_table_id, WAIT_TIME_TIMEOUT)
                self.throttle()
            except Exception as e:
                logging.error(f"WARNING Check this issue {id_link_log}, {type(e)}")
        df = pd.DataFrame(results)
        return df

    def _extract_cords(self, df_all):
        url_points = "https://nadlan.taxes.gov.il/svinfonadlan2010/InfoNadlanPerutWithMap.aspx/GetPoints"
        headers = {"User-Agent": "PostmanRuntime/4.9.2",
                   "Host": "nadlan.taxes.gov.il",
                   "Content-Length": "0",
                   "Content-Type": "application/json;charset=utf-8"}
        cookies = {x['name']: x['value'] for x in self.driver.get_cookies()}
        # no need to add cookies to header, just send them like below
        proxies = {'http': self.proxy_ip, 'https': self.proxy_ip} if self.proxy_ip else None
        res = requests.post(url_points, headers=headers, cookies=cookies, proxies=proxies).json()
        res = pd.DataFrame.from_dict(res['d'])
        res.columns = [c[1:] for c in res.columns]
        res = res[['gushHelka', 'helekNimkar', 'corX', 'corY']]
        df_all = df_all.merge(res, left_on='gush', right_on='gushHelka',
                              how='left').drop(columns='gushHelka')
        return df_all
        # list of :
        # {'_map': False, '_gushHelka': '010926-0003-014-00', '_dateSell': '08/12/2022', '_dateSellTemp': 20221208, '_mutzhar': '1,290,000', '_mutzharTemp': 1290000, '_shovi': '1,290,000', '_shoviTemp': 1290000, '_mahut': 'דירה בבית קומות', '_helekNimkar': '1.000', '_city': 'חיפה', '_year': 1970, '_shetah': 83, '_roms': 3, '_corX': 199209, '_corY': 746190, '_isn': 3649849, '_crmn': 1, '_SugNehes': 1, '_moreGushim': ''}

        # requests.post(url_points, headers={"Content-Type": "application/json;charset=utf-8"},
        #               cookies={c_session: asp_net_value}).json()

    def throttle(self):  # at 70 starts heavy throttling
        self.throttle_total_fetched += 1
        if self.throttle_total_fetched > THROTTLE_LIMIT_BEFORE_SLEEP:
            logging.info(f"Passed limit of {THROTTLE_LIMIT_BEFORE_SLEEP}, sleeping for a while...")
            sleep(SLEEP_THROTTLE_TIME_SEC)
            self.throttle_total_fetched = 0
            # can implement this as number of total requests to server, add this to wait func/ and then use it for every fetch

    def parse_and_get_next(self):
        curr_page = 1
        n_deals_found = self.driver.find_element("id", "lblresh").text.strip().split(' ')[1]
        logging.info(f"Found {n_deals_found} deals in query")

        # TODO: Add number of deals with id 'lblresh':  נמצאו: 35 רשומות
        def get_links(curr_page):
            main_table_id = "ContentUsersPage_GridMultiD1"
            table = self.driver.find_element("id", main_table_id)  # try to find first table
            links = [x for x in table.find_elements("tag name", "a")]
            next_page_links = [x for x in links if x.text.isdigit() or x.text == '...']  # need to reget links
            three_dot_fix = lambda x: 11 if x == '...' else int(x)
            next_page_links = [x for x in next_page_links if
                               curr_page < three_dot_fix(x.text)]  # TODO: Link can be over 10, need to add this.
            # IF ... link exists, need to click on it when page 10 has been reached. # TODO:
            logging.info([x.text for x in next_page_links])
            return next_page_links

        df_all = self.go_over_dira_links()
        next_page_links = get_links(curr_page)

        if len(next_page_links) and len(df_all) < 12:
            logging.warning('Warning - parse table missing rows')
        while len(next_page_links) > 0:
            link = next_page_links[0]
            # print(link.text)
            link.click()
            df = self.go_over_dira_links()
            df_all = pd.concat([df_all, df], axis=0)
            curr_page += 1
            next_page_links = get_links(curr_page)
        df_all = self._extract_cords(df_all)

        self.driver.find_element("id", back_id).click()
        self.throttle()
        return df_all.reset_index(drop=True)

    def wait_for_id(self, element_id, wait_time_sec=5, raise_exception=False):
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        try:
            WebDriverWait(self.driver, wait_time_sec).until(
                EC.presence_of_element_located((By.ID, element_id)))
            return True
        except TimeoutException:
            logging.warning("Too much time took to load, ERR")
            return False

    def solve_captcha_once(self, digits=4):
        click_btn_start = "ContentUsersPage_btnHipus"
        try:
            self.driver.find_element("id", click_btn_start).click()
        except Exception as e:
            logging.error("FATAL ERROR IN clicking button, trying to sleep and retry again...")
            logging.info(e)
        captcha_id = "ContentUsersPage_RadCaptcha1_CaptchaImageUP"
        time.sleep(3)  # wait for caphta to refresh
        self.wait_for_id("ContentUsersPage_RadCaptcha1_CaptchaImageUP", WAIT_TIME_TIMEOUT)
        img = self.driver.find_element("id", captcha_id)
        tempfile.gettempdir()
        path = f'{os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))}.png'
        img.screenshot(path)
        ocr_text = self.ocr.detect_text(path)
        if len(ocr_text) != digits or not ocr_text.isdigit():
            return None, False
        captcha_insert_id = "ContentUsersPage_RadCaptcha1_CaptchaTextBox"
        captcha_send_id = "ContentUsersPage_btnIshur"
        self.driver.find_element("id", captcha_insert_id).send_keys(ocr_text)
        # Wait to page to load or failure to do so.
        # time.sleep(3)
        self.driver.find_element("id", captcha_send_id).click()
        return ocr_text

    def fill_selling_time(self, from_dt, to_dt):
        self.driver.find_element("id", "ctl00_ContentUsersPage_txtyomMechira_dateInput").clear()
        self.driver.find_element("id", "ctl00_ContentUsersPage_txtyomMechira_dateInput").send_keys(from_dt)
        self.driver.find_element("id", "ctl00_ContentUsersPage_txtadYomMechira_dateInput").clear()
        self.driver.find_element("id", "ctl00_ContentUsersPage_txtadYomMechira_dateInput").send_keys(to_dt)

    def validate_after_captcha_try(self, ocr_text):
        # same captcha could indicate that there was a problem in the server such that it does no longer sends a captcha
        #         self._past_ocr_text = text
        if ocr_text == self._past_ocr_text:
            return "stuck_restart"

        try:
            self.driver.find_element("id", main_table_id)
            return "found_table"
        except NoSuchElementException as e:
            pass
        try:
            not_found_id = 'ContentUsersPage_lblerrDanger'
            value = "לא נמצאו נתונים לחתך המבוקש"
            if self.driver.find_element("id", not_found_id).text == value:
                logging.info('not found deals in criteria')
                return "no_deals"
        except NoSuchElementException as e:
            pass
        try:
            not_found_id = 'ContentUsersPage_lblerrDanger'
            valuse_too_many = "יש יותר מ-150 עסקאות נא למקד את החיפוש בעזרת חתך משני"
            if self.driver.find_element("id", not_found_id).text == valuse_too_many:
                logging.info('too many deals in criteria')
                return "too_many_deals"
        except NoSuchElementException as e:
            pass
        return "captcha_fail"

    def reset_details(self):
        self._from_gush = None
        self._to_gush = None
        self._date = None
        self._from_room = None
        self._to_room = None
        self._from_year = None
        self._to_year = None

    def check_if_request_rejected(self):
        # New error, could it be because of the autofill of the buttons? or because I got targeted. need to check with a vpn
        txt = "The requested URL was rejected. Please consult with your administrator."
        return True if self.driver.title == "Request Rejected" else False

    def solve_captcha_get_data(self):
        n_tries = 10
        for tries in range(n_tries):
            self.fill_details(self._from_gush, self._to_gush)
            self.fill_exact_range(from_date=self._date, to_date=self._date)
            if self._from_room or self._to_room:
                self.fill_rooms(self._from_room, self._to_room)
            if self._from_year or self._to_year:
                self.fill_year_built(self._from_year, self._to_year)

            ocr_text = self.solve_captcha_once()
            result = self.validate_after_captcha_try(ocr_text)
            if result == "found_table":
                try:
                    df_all = self.parse_and_get_next()
                    df_all['insertionDate'] = datetime.today()
                    return df_all, 0
                except Exception as e:
                    logging.warning("GOT AN EXCEPTION, restarting from same position using saved details")
                    logging.info(e)
                    if self.check_if_request_rejected():
                        logging.info("Got Rejected !, sleeping and restarting")
                        sleep(WAIT_TIME_TIMEOUT)
                        logging.info("Finished Sleeping, Refreshing")
                        self.driver.refresh()
                        # self.restart_page(reset_details=False)
            elif result == "no_deals":
                return pd.DataFrame({}, columns=columns), -1
            elif result == "too_many_deals":
                return None, -2
            elif result == "stuck_restart":
                logging.warning("stuck_restart - sleep and restart fetch")
                sleep(WAIT_TIME_TIMEOUT)
            logging.info(f"solve_captcha_get_data - {result} ({tries}/{n_tries})")
        return None, -10  # should  be result "captcha_fail"

    def generate_dates(self, since='2020-01-01'):
        from datetime import datetime
        today = datetime.now()
        dates = pd.date_range(since, today, freq='90D')
        search_dates = []
        for idx in range(len(dates) - 1):
            search_dates.append((dates[idx].strftime('%d/%m/%Y'), dates[idx + 1].strftime('%d/%m/%Y')))
        search_dates.append((dates[-1].strftime('%d/%m/%Y'), pd.to_datetime(today).strftime('%d/%m/%Y')))
        return search_dates

    def get_history(self, from_gush, to_gush=None, since='2020-01-01'):
        if to_gush is None:
            to_gush = from_gush
        #  value="2" 3 months, 3 => 6 months, 4=>12 months, 5 => 36 months
        # Can run it multiple times until we are ok to go, just need to return error_code from fetch
        self.fill_details(from_gush, to_gush)
        _df_all = pd.DataFrame()
        self.fill_range("1")
        search_dates = self.generate_dates(since)
        for from_dt, to_dt in search_dates:
            # try:
            # PR_CONNECT_RESET_ERROR
            self.fill_selling_time(from_dt, to_dt)
            df_all, status_code = self.solve_captcha_get_data()
            if status_code == 0:  # okay
                logging.info(f'{from_dt},{to_dt},{len(df_all)}')
                _df_all = pd.concat([_df_all, df_all], axis=0)
            if status_code == -1:  # no deals
                continue
            if status_code == -2:  # too many deals
                continue
            if status_code == -3:  # error, try with less..
                continue
            # if failed to load, can refresh...
            time.sleep(3)
        self.driver.quit()
        return _df_all

    #  value="2" 3 months, 3 => 6 months, 4=>12 months, 5 => 36 months
    def get_months(self, from_gush, to_gush=None, value_months="2"):
        self.fill_details(from_gush, to_gush)
        self.fill_range(value_months)
        df_all, status_code = self.solve_captcha_get_data()
        return df_all

    def get_daily(self, from_gush, to_gush, date):
        self._from_gush = from_gush
        self._to_gush = to_gush
        self._date = date
        # self.fill_details(from_gush, to_gush)
        # self.fill_exact_range(from_date=date, to_date=date)
        df_all, status_code = self.solve_captcha_get_data()
        if status_code == -2:
            df_all, status_code = self._get_daily_with_rooms(from_gush, to_gush, date)
        return df_all, status_code

    def _get_daily_with_rooms(self, from_gush, to_gush, date):
        room_ranges = [
            ["1", "2.5"],
            ["3", "3.5"],
            ["4", "4.5"],
            ["5", "5.5"],
            ["6", ""]
        ]
        status_code = -1
        df = pd.DataFrame()
        for room_range in room_ranges:
            self._from_room = room_range[0]
            self._to_room = room_range[1]
            logging.info(f"Fetching data for ({from_gush}, {to_gush}, {date}), for rooms in range {room_range}")
            df_all, status_code = self.solve_captcha_get_data()
            # TODO: Consider about saving this dataframe instead of waiting for whole day to finish, could lose some data instead of going again....
            if status_code == 0:
                df = pd.concat([df, df_all], axis=0)
            elif status_code == -2:
                logging.info(f"Failed to fetch for range {room_range} rooms. ({from_gush}, {to_gush}, {date}) "
                             f"too many deals. Taking in portions by splitting by years built")
                # year_ranges = [
                #     ["1800", "1970"],
                #     ["1971", "1980"],
                #     ["1981", "1990"],
                #     ["1991", "2000"],
                #     ["2001", "2010"],
                #     ["2011", "2100"]]
                year_ranges = [
                    ["1800", "1970"],
                    ["1971", "1980"],
                    ["1981", "1985"],
                    ["1986", "1990"],
                    ["1991", "1995"],
                    ["1996", "2000"],
                    ["2001", "2010"],
                    ["2011", "2015"],
                    ["2016", "2100"]]
                for year_range in year_ranges:
                    self._from_year = year_range[0]
                    self._to_year = year_range[1]
                    logging.info(f"Fetching data for ({from_gush}, {to_gush}, {date}),"
                                 f"for rooms in range {room_range}, year in range {year_range}")
                    self.fill_year_built(year_range[0], year_range[1])
                    df_all, status_code = self.solve_captcha_get_data()
                    if status_code == 0:
                        df = pd.concat([df, df_all], axis=0)
                    elif status_code == -2:
                        logging.error(f"FAILED TO GET EVEN WITH YEAR BUILT, RE THINK HOW TO SOLVE THIS MADDNESS")
                    # TODO: TRY to throttle when going over pages instead of watiting to finish,
                    #  if we are limitd to about 100, limit at 80 per 11 min

                    sleep(SLEEP_THROTTLE_TIME_SEC)
                    self.throttle_total_fetched = 0
            sleep(SLEEP_THROTTLE_TIME_SEC)
            self.throttle_total_fetched = 0
        return df, status_code

# LOOK HOW TO SOLVE THIS ISSUE WITH URL.
# The requested URL was rejected. Please consult with your administrator.
