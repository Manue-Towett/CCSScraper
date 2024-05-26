import threading
from queue import Queue

import requests
from bs4 import BeautifulSoup

class ProxyHandler:
    """Scrapes proxies from https://free-proxy-list.net/"""
    def __init__(self) -> None:
        self.ports = ["3128", "3124", "80", "8080"]
        self.proxies = []

        with open("proxies.txt", "r") as f:
            self.proxies.extend([l.strip() for l in f.readlines()])
        
        self.proxy_queue = Queue()

        self.create_ip_workers()
        
        threading.Thread(target=self.get_proxies, daemon=True).start()

    def get_proxies(self) -> None:
        """Fetches proxies from https://free-proxy-list.net/"""
        proxies = set()

        while True:
            try:
                response = requests.get('https://free-proxy-list.net/')
                proxies_table = BeautifulSoup(response.text, "html.parser")

                if response.status_code != 200:
                    continue

                table_rows = proxies_table.select("tbody tr")[:299]

                if not len(table_rows):
                    continue

                for row in table_rows:
                    for port in [*self.ports, row.select('td')[1].text.strip()]:   
                        proxy = ":".join(
                            [row.select('td')[0].text.strip(), port
                            #  row.select('td')[1].text.strip()
                             ]
                             )            
                        proxies.add(proxy)

            except:continue

            self.create_ip_jobs(list(proxies))
    
    def create_ip_workers(self) -> None:
        """Creates threads to check if a proxy is working"""
        for _ in range(100):
            thread = threading.Thread(target=self.work_ip, daemon=True)
            thread.start()
        
    def work_ip(self) -> None:
        """Checks if a free proxy is working"""
        while True:
            ip_port, proxies = self.proxy_queue.get()
            try:
                url = "https://www.cannabiscreditscores.com/"
                proxy = {"https":f"http://{ip_port}"}
                proxies.remove(ip_port)

                response = requests.get(
                    url, proxies=proxy, verify=False, timeout=10)

                if response.ok:
                    self.proxies.append(f"{ip_port}")

            except:pass

            self.proxy_queue.task_done()
    
    def create_ip_jobs(self, proxies:list) -> None:
        """Create ip thread jobs"""
        [self.proxy_queue.put((proxy, proxies)) for proxy in proxies]
        self.proxy_queue.join()

        self.proxies = list(set(self.proxies))

        print(len(self.proxies))

        with open("proxies.txt", "w") as f:
            [f.write(l + "\n") for l in self.proxies]