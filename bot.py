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
        print(f"* ARC TESTNET - CIRCLE FAUCET (STABLE VERSION)     *")
        print("* COOKIES + APOLLO + CAPTCHA FIX                   *")
        print("************************************************************")

    def load_config(self):
        try:
            with open('captcha_key.txt', 'r') as f:
                self.captcha_api_key = f.readline().strip()
            with open('wallets.txt', 'r') as f:
                self.accounts = [l.strip() for l in f if l.strip()]
            print(f"{Fore.GREEN}✅ Loaded {len(self.accounts)} accounts.")
        except Exception as e:
            print(f"{Fore.RED}❌ File Error: {e}")
            sys.exit(1)

    def refresh_session(self):
        """Cloudflare Cookies ရအောင်ယူခြင်း"""
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        try:
            self.session.get(self.page_url, headers=headers, timeout=15)
            print(f"{Fore.YELLOW}🔄 Session Cookies Refreshed.")
        except:
            print(f"{Fore.RED}⚠️ Session Refresh Failed (Network Error)")

    def solve_captcha(self, idx):
        print(f"{Fore.CYAN}[Account #{idx}] ⏳ Requesting 2Captcha to solve...")
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
            # 2Captcha ကို session မသုံးဘဲ direct requests နဲ့ ပို့ပါမယ်
            res = requests.post("http://2captcha.com/in.php", data=params, timeout=20).json()
            if res.get('status') != 1:
                print(f"{Fore.RED}❌ 2Captcha Error: {res.get('request')}")
                return None
            
            job_id = res.get('request')
            print(f"{Fore.WHITE}[Account #{idx}] ⏳ Captcha ID: {job_id}. Solving...", end="\r")
            
            for _ in range(60):
                time.sleep(5)
                res = requests.get(f"http://2captcha.com/res.php?key={self.captcha_api_key}&action=get&id={job_id}&json=1", timeout=20).json()
                if res.get('status') == 1:
                    print(f"\n{Fore.GREEN}[Account #{idx}] ✅ Captcha Solved!")
                    return res.get('request')
            return None
        except Exception as e:
            print(f"\n{Fore.RED}❌ Captcha Request Failed: {e}")
            return None

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
        
        headers = {
            'accept': '*/*',
            'apollo-require-preflight': 'true',
            'content-type': 'application/json',
            'origin': 'https://faucet.circle.com',
            'referer': 'https://faucet.circle.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'recaptcha-action': 'request_token',
            'recaptcha-token': captcha_token
        }
        
        payload = {"operationName": "RequestToken", "query": query, "variables": variables}
        
        try:
            # Claim လုပ်တဲ့နေရာမှာတော့ Session (Cookies) ကို သုံးပါမယ်
            response = self.session.post(self.api_url, json=payload, headers=headers, timeout=30)
            res_json = response.json()
            
            if 'errors' in res_json:
                return False, res_json['errors'][0]['message']
            
            data = res_json.get('data', {}).get('requestToken', {})
            if data and data.get('hash'):
                return True, data['hash']
            return False, f"Status: {data.get('status', 'No Hash')}"
        except Exception as e:
            return False, str(e)

    def run(self):
        self.welcome()
        self.load_config()
        round_count = 1
        while True:
            print(f"\n{Fore.MAGENTA}=== ROUND {round_count} START ===")
            self.refresh_session()
            
            for idx, addr in enumerate(self.accounts, 1):
                for t_type in ["USDC", "EURC"]:
                    token = self.solve_captcha(idx)
                    if token:
                        print(f"{Fore.YELLOW}[Account #{idx}] Sending {t_type} Request...")
                        success, result = self.claim_token(addr, t_type, token)
                        if success:
                            print(f"{Fore.GREEN}✅ Success: {result}")
                        else:
                            print(f"{Fore.RED}❌ Failed: {result}")
                    else:
                        print(f"{Fore.RED}❌ Captcha Timeout/Error")
                    time.sleep(5)
            
            print(f"\n{Fore.CYAN}✨ Round {round_count} finished. Waiting 3 hours...")
            time.sleep(3 * 3600)
            round_count += 1

if __name__ == "__main__":
    bot = CircleFaucetBot()
    bot.run()
