from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
import time

# change 'ip:port' with your proxy's ip and port
proxies = open(r"proxy\working_proxies.csv", 'r').read().split('\n')

# proxy_ip_port = '80.48.119.28:8080'

for proxy_ip_port in proxies:
    proxy = Proxy()
    proxy.proxy_type = ProxyType.MANUAL
    proxy.http_proxy = proxy_ip_port
    proxy.ssl_proxy = proxy_ip_port

    capabilities = webdriver.DesiredCapabilities.FIREFOX
    # capabilities = webdriver.DesiredCapabilities.CHROME
    proxy.add_to_capabilities(capabilities)

    # replace 'your_absolute_path' with your chrome binary absolute path
    PATH= "geckodriver.exe"
    driver = webdriver.Firefox(executable_path=PATH, desired_capabilities=capabilities)
    # driver = webdriver.Chrome('your_absolute_path', desired_capabilities=capabilities)

    driver.get('http://whatismyipaddress.com')

    time.sleep(3)

    driver.quit()