import time
import json
import csv
import sys
from datetime import datetime

import requests
import pandas
import chromedriver_binary
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By



file_name = sys.argv[1]

_1st_list_items = [
    "CAIXA ECONOMICA FEDERAL",
    "BCO DO BRASIL S.A.",
    "BCO SANTANDER (BRASIL) S.A.",
    "BCO ITAUCARD S.A.",
    "BCO BRADESCO S.A.",
    "BANCO BRADESCARD",
    "NU FINANCEIRA S.A. CFI",
    "BANCO INTER",
    "BCO XP S.A.",
    "BCO C6 S.A.",
    "BANCO ORIGINAL"
]

_2nd_list_items = [
    "CAIXA ECONOMICA FEDERAL",
    "BCO DO BRASIL S.A.",
    "BCO SANTANDER (BRASIL) S.A.",
    "ITAÚ UNIBANCO S.A.",
    "BCO BRADESCO S.A.",
    "NU FINANCEIRA S.A. CFI",
    "BCO C6 S.A.",
    "BANCO PAN"
]

load_datetime = datetime.utcnow()

def find_specific(trs, item, mode, date):
    for tr in trs:
        if item in tr.text:
            tds = tr.find_all('td')
            if not len(tds)==4:
                continue
            dict_data = {
                "load_datetime": load_datetime,
                "Segment": "Physical person",
                "Mode": mode,
                "Order_Type": "Prefixed",
                "Initial_Period": date,
                "Institution": tds[1].text.strip(),
                "Interest_rate_am": float(tds[2].text.strip().replace(",", ".")),
                "Interest_rate_aa": float(tds[3].text.strip().replace(",", "."))
            }
            return dict_data
    return False


def get_all_dates(driver):
    driver.get("https://www.bcb.gov.br/estatisticas/reporttxjuroshistorico")
    time.sleep(5)
    time.sleep(30)
    driver.find_elements(By.XPATH, '//ng-select[@bindvalue="Value"]')[2].click()
    divs = driver.find_element(By.XPATH, '//div[@class="ng-dropdown-panel-items scroll-host"]').find_elements(By.XPATH, '//div[@class="ng-option"]')
    dates = []
    print(f"Getting {len(divs)} dates")
    for div in divs:
        if "10/2022" in div.text:
            break
        dates.append(div.text)
    driver.find_elements(By.XPATH, '//ng-select[@bindvalue="Value"]')[2].click()
    return dates


def find_and_make_dict_from_page(soup, items, mode, date):
    data = []
    time.sleep(10)
    trs = soup.find_all('tr', {'valign':"top"})
    for item in items:
        dict_data = find_specific(trs, item, mode, date)
        if dict_data:
            data.append(dict_data)
        else:
            print(f"Not found {item}")
    return data


all_scraped_data = []
mode1 = "Cartão de crédito - rotativo total"
mode2 = "Crédito pessoal não-consignado"
driver = webdriver.Chrome()
driver.maximize_window()
all_date = get_all_dates(driver)
driver.quit()
uzun = len(all_date)
print(f"SCRAPING {uzun} dates")
for date in all_date:
    try:
        time.sleep(60)
        splited1=date.split("a")
        splited = splited1[0].strip().split("/")
        splited3=splited1[-1].strip().split("/")
        part = splited[1].replace("0", "") if splited[1]!="10" else splited[1]
        prt2= splited3[1].replace("0", "") if splited[1]!="10" else splited[1]
        new_date = part +"/"+ splited[0] + "/" + splited3[2]+"&"+prt2 +"/"+ splited3[0] + "/" + splited3[2]
        print("new_date", new_date)
        url1 = f"https://www.bcb.gov.br/api/relatorio/pt-br/contaspub?path=conteudo/txcred/Reports/TaxasCredito-Consolidadas-porTaxasAnuais-Historico.rdl&parametros=tipoPessoa:1;modalidade:204;encargo:101;periodoInicial:{new_date} 12:00:00 AM;&exibeparametros=true"
        url2 = f"https://www.bcb.gov.br/api/relatorio/pt-br/contaspub?path=conteudo/txcred/Reports/TaxasCredito-Consolidadas-porTaxasAnuais-Historico.rdl&parametros=tipoPessoa:1;modalidade:221;encargo:101;periodoInicial:{new_date} 12:00:00 AM;&exibeparametros=true"
        re_1 = requests.get(url1)
        print(re_1.status_code)
        data1 = json.loads(re_1.text)
        soup_1 = BeautifulSoup(data1["conteudo"], 'html.parser')
        all_scraped_data.extend(find_and_make_dict_from_page(soup_1, _1st_list_items, mode1, date))
        time.sleep(60)
        re_2 = requests.get(url2)
        print(re_2.status_code)
        data2 = json.loads(re_2.text)
        soup_2 = BeautifulSoup(data2["conteudo"], 'html.parser')
        all_scraped_data.extend(find_and_make_dict_from_page(soup_2, _2nd_list_items, mode2, date))
        print("SCRAPED DATA LENGHT: ", len(all_scraped_data))
        ind = all_date.index(date)
        print(f"Done : {round(ind/uzun*100, 2)} Percent")
    except Exception as e:
        print("Exception", e.args[0])
        print("PAUSING FOR 5minutes")
        time.sleep(300)

df = pandas.DataFrame(data=all_scraped_data)
df.to_csv(
    file_name,
    encoding="utf-8",
    quotechar='"',
    quoting=csv.QUOTE_ALL,
    index=False
  )


