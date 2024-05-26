import re
import json
import time
import random
import threading
from queue import Queue
from typing import Tuple, Optional

import requests
import pandas as pd
from bs4 import BeautifulSoup

from utils import ProxyHandler

requests.packages.urllib3.disable_warnings()

proxy_handler = ProxyHandler()

QUEUE = Queue()

CRAWLED = []

HEADERS = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'en-US,en;q=0.9',
    'dnt': '1',
    'priority': 'u=1, i',
    'referer': 'https://www.cannabiscreditscores.com/explore_clasic',
    'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

PARAMS = {
    'mylisting-ajax': '1',
    'action': 'get_listings',
    'security': '72cca04302',
    'form_data[page]': '0',
    'form_data[preserve_page]': 'false',
    'form_data[search_keywords]': '',
    'form_data[category]': '',
    'form_data[license-number]': '',
    'form_data[credit-score]': '',
    'form_data[address]': '',
    'form_data[business-status]': '',
    'form_data[sort]': 'latest',
    'listing_type': 'cars',
    'listing_wrap': 'col-md-6 col-sm-6 grid-item',
}

BASE_URL = 'https://www.cannabiscreditscores.com/'

def get_posts(page: int) -> Tuple[list[dict[str, str]], int, bool]:
    if page > 0:
        PARAMS.update({'form_data[page]': str(page),
                    #    'form_data[preserve_page]': 'true'
                       })
        
    response = requests.get(BASE_URL, params=PARAMS, headers=HEADERS).json()
    soup = BeautifulSoup(response.get("html"), "html.parser")

    containers = soup.select("div.col-md-6.col-sm-6.grid-item")

    companies = []

    for container in containers:
        company_name_tag = container.select_one("h4.case27-primary-text.listing-preview-title")
        company_link_tag = container.select_one("a")
        credit_score_list = container.select_one("ul.lf-contact.no-list-style")
        credit_score_re = re.search(r"Credit\s+Score:\s+(\d+)\s*", 
                                    credit_score_list.__str__(), re.I|re.DOTALL)
        company_name = company_name_tag.get_text(strip=True)

        if credit_score_re is None or not company_name: continue

        data = {"company name": company_name,
                "ccs company link": company_link_tag.attrs.get("href"),
                "credit score": credit_score_re.group(1)}

        companies.append(data)
    
    return companies, response.get("found_posts"), page + 1 == int(response.get("max_num_pages"))

def get_specific_company_info(class_name: str, soup: BeautifulSoup) -> Optional[str]:
    info_tag = soup.select_one(f"div.block-field-{class_name} div.pf-body")

    return info_tag.get_text(strip=True) if info_tag else None

def get_proxies() -> dict[str, str]:
    """Gets a random proxy from a list of proxies"""
    while True:
        try:
            proxy = random.choice(proxy_handler.proxies)

            return {"https":f"http://{proxy}", "http":f"http://{proxy}"}
        
        except:pass

def get_company_data(data: dict[str, str]) -> None:
    while True:
        try:
            while not len(proxy_handler.proxies): pass

            proxies = get_proxies()

            response = requests.get(data.get("ccs company link"), 
                                    headers=HEADERS, 
                                    proxies=proxies,
                                    verify=False,
                                    timeout=5,)

            if not response.ok: 
                
                continue
            
            # print(data.get("ccs company link"))

            soup = BeautifulSoup(response.text, "html.parser")

            data.update({
                "legal name": get_specific_company_info("legal_name", soup),
                "license number": get_specific_company_info("license-number", soup),
                "address line 1": get_specific_company_info("address", soup),
                "city": get_specific_company_info("city", soup),
                "email": get_specific_company_info("job_email", soup),
                "phone": get_specific_company_info("job_phone", soup),
                "website": get_specific_company_info("job_website", soup)})
            
            k_found = False

            # print(data)

            for k, v in data.items(): 
                if k == "legal name": k_found = True

                if v is not None and k_found: return
            
            return

        except: pass

def work() -> None:
    while True:
        job = QUEUE.get()

        get_company_data(job)

        final.append(job)

        try:
            # if len(final) % 10 == 0:
                save_to_json(final, "complete_companies")
        except: pass

        CRAWLED.append("")

        print(f"Queue: {companies_no - len(CRAWLED)} || Crawled: {len(CRAWLED)}")

        QUEUE.task_done()


def get_companies() -> list[dict[str, str]]:
    companies, page, is_done = [], 0, False

    while not is_done:
        try:
            data, found, is_done = get_posts(page=page)

            companies.extend(data)

            print(f"Page: {page+1} || Companies: {len(companies)} || Total: {found}")

            page += 1

            time.sleep(5)

        except: pass

    return companies

def save_to_json(data: list[dict[str, str]], name: str) -> None:
    with open(f"./data/{name}.json", "w") as f:
        json.dump(data, f, indent=4)

    print(f"Data saved to {name}.json")

def save_to_excel(data: list[dict[str, str]]) -> None:
    df = pd.DataFrame(data)

    df.to_excel("./data/data.xlsx", index=False)

    print("Data saved to excel")

if __name__ == "__main__":
    [threading.Thread(target=work, daemon=True).start() for _ in range(20)]

    # companies = get_companies()

    # save_to_json(companies, "companies")

    final = []

    with open("./data/companies.json") as f:
        companies = json.load(f)
    
    with open("./data/complete_companies.json") as f:
        collected = json.load(f)

    companies_no = 0

    # final.extend(collected)

    for company in companies:
        found = False
        link = company.get("ccs company link")

        for c in collected:
            if c.get("ccs company link") == link:
                found = True

                final.append(c)

                break
        
        if not found:      
            QUEUE.put(company)

            companies_no += 1
            

    QUEUE.join()

    # for company in companies:
    #     found = False
    #     link = company.get("ccs company link")

    #     for c in collected:
    #         if c.get("ccs company link") == link:
    #             found = True

    #             break

    #     if found: continue

    #     get_company_data(company)

    #     CRAWLED.append("")

    #     print(f"Queue: {companies_no - len(CRAWLED)} || Crawled: {len(CRAWLED)}")

    #     time.sleep(3)

    save_to_json(final, "complete_companies")

    save_to_excel(final)