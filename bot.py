# -*- coding: utf-8 -*-
import requests
import time
from colorama import Fore, Style, init
import sys

init(autoreset=True)

class CircleFaucetBot:
    def __init__(self):
        self.api_url = "https://faucet.circle.com/api/graphql"
        self.site_key = "6LcNs_0pAAAAAJuAAa-VQryi8XsocHubBk-YlUy2"
        self.page_url = "https://faucet.circle.com"
        self.session = requests.Session()
        self.accounts = []
        self.captcha_api_key = ""

    def welcome(self):
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("************************************************************")
        print(f"* ARC TESTNET - CIRCLE FAUCET (ADVANCED BYPASS)    *")
        print("* COOKIES + APOLLO PREFLIGHT + ACTION HEADER       *")
        print("************************************************************")

    def load_config(self):
        try:
            with open('captcha_key.txt', 'r') as f:
                self.captcha_api_key = f.readline().strip()
            with open('wallets.txt', 'r') as f:
                self.accounts = [l.strip() for l in f if l.strip()]
            print(f"{Fore.GREEN}✅ Config Loaded.")
        except Exception as e:
            print(f"{Fore.RED}❌ Config Error: {e}")
            sys.exit(1)

    def refresh_session(self):
        """Cloudflare Cookies ရအောင် Website ကို အရင်သွားဖတ်ခြင်း"""
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,share/zstd,*/*;q=0.8'
        }
        self.session.get(self.page_url, headers=headers)
        print(f"{Fore.YELLOW}🔄 Session Cookies Refreshed.")

    def solve_captcha(self, idx):
        print(f"{Fore.CYAN}[Account #{idx}] ⏳ Solving ReCAPTCHA (V3 Enterprise Mode)...")
        params = {
            'key': self.captcha_api_key,
            'method': 'userrecaptcha',
            'googlekey': self.site_key,
            'pageurl': self.page_url,
            'invisible': 1,
            'enterprise': 1,
            'action': 'request_token',
            'json': 1
        }
        try:
            res = self.session.post("http://2captcha.com/in.php", data=params).json()
            if res.get('status') != 1: return None
            job_id = res.get('request')
            for _ in range(60):
                time.sleep(5)
                res = self.session.get(f"http://2captcha.com/res.php?key={self.captcha_api_key}&action=get&id={job_id}&json=1").json()
                if res.get('status') == 1:
                    return res.get('request')
            return None
        except: return None

    def claim_token(self, address, token_type, captcha_token):
        query = """
        mutation RequestToken($input: RequestTokenInput!) {
          requestToken(input: $input) {
            hash
            status
          }
        }
        """
        variables = {"input": {"destinationAddress": address, "token": token_type, "blockchain": "ARC"}}
        
        # သင်ပေးပို့ထားသော Headers များအတိုင်း အတိအကျ ပြင်ဆင်ထားပါသည်
        headers = {
            'accept': '*/*',
            'apollo-require-preflight': 'true', # ဒါ အရေးကြီးဆုံးပါ
            'content-type': 'application/json',
            'origin': 'https://faucet.circle.com',
            'referer': 'https://faucet.circle.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'recaptcha-action': 'request_token',
            'recaptcha-token': captcha_token,
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }
        
        payload = {"operationName": "RequestToken", "query": query, "variables": variables}
        
        try:
            response = self.session.post(self.api_url, json=payload, headers=headers)
            res_json = response.json()
            if 'errors' in res_json:
                return False, res_json['errors'][0]['message']
            data = res_json.get('data', {}).get('requestToken', {})
            if data.get('hash'): return True, data['hash']
            return False, f"Status: {data.get('status')}"
        except Exception as e:
            return False, str(e)

    def run(self):
        self.welcome()
        self.load_config()
        while True:
            self.refresh_session() # အကျော့တိုင်း Cookie အသစ်ယူမည်
            for idx, addr in enumerate(self.accounts, 1):
                for t_type in ["USDC", "EURC"]:
                    token = self.solve_captcha(idx)
                    if token:
                        print(f"{Fore.YELLOW}[Account #{idx}] Requesting {t_type}...")
                        success, res = self.claim_token(addr, t_type, token)
                        if success: print(f"{Fore.GREEN}✅ Success: {res}")
                        else: print(f"{Fore.RED}❌ Failed: {res}")
                    time.sleep(5)
            
            print(f"\n{Fore.CYAN}✨ Round Finished. Sleeping 3 Hours...")
            time.sleep(3 * 3600)

if __name__ == "__main__":
    bot = CircleFaucetBot()
    bot.run()
