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
        print(f"* ARC TESTNET - CIRCLE FAUCET (CAPMONSTER OPTIMIZED) *")
        print("* ENTERPRISE SUPPORT + MIN_SCORE 0.9               *")
        print("************************************************************")

    def load_config(self):
        try:
            with open('captcha_key.txt', 'r') as f:
                self.captcha_api_key = f.readline().strip()
            with open('wallets.txt', 'r') as f:
                self.accounts = [l.strip() for l in f if l.strip()]
            print(f"{Fore.GREEN}✅ Config Loaded. ({len(self.accounts)} accounts)")
        except Exception as e:
            print(f"{Fore.RED}❌ File Error: {e}")
            sys.exit(1)

    def refresh_session(self):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        }
        try:
            self.session.get(self.page_url, headers=headers, timeout=15)
            print(f"{Fore.YELLOW}🔄 Cloudflare Session Initialized.")
        except:
            print(f"{Fore.RED}⚠️ Session Init Timeout.")

    def solve_captcha(self, idx):
        print(f"{Fore.CYAN}[Account #{idx}] ⏳ Requesting High-Score Token from CapMonster...")
        
        # CapMonster Enterprise V3 Params
        payload = {
            "clientKey": self.captcha_api_key,
            "task": {
                "type": "RecaptchaV3TaskProxyless",
                "websiteURL": self.page_url,
                "websiteKey": self.site_key,
                "minScore": 0.9, # Score အမြင့်ဆုံး တောင်းဆိုခြင်း
                "pageAction": "request_token",
                "isEnterprise": True # Enterprise Mode On ခြင်း
            }
        }
        
        try:
            # Create Task
            create_res = requests.post("https://api.capmonster.cloud/createTask", json=payload, timeout=20).json()
            if create_res.get('errorId') != 0:
                print(f"{Fore.RED}❌ CapMonster Error: {create_res.get('errorCode')}")
                return None
            
            task_id = create_res.get('taskId')
            print(f"{Fore.WHITE}[Account #{idx}] ⏳ Task ID: {task_id}. Polling solution...", end="\r")
            
            # Get Result
            for _ in range(30):
                time.sleep(3)
                result_payload = {"clientKey": self.captcha_api_key, "taskId": task_id}
                res = requests.post("https://api.capmonster.cloud/getTaskResult", json=result_payload, timeout=20).json()
                
                if res.get('status') == "ready":
                    print(f"\n{Fore.GREEN}[Account #{idx}] ✅ Token Received!")
                    return res.get('solution', {}).get('gRecaptchaResponse')
                
                if res.get('errorId') != 0:
                    print(f"\n{Fore.RED}❌ CapMonster Solve Error: {res.get('errorCode')}")
                    return None
            return None
        except Exception as e:
            print(f"\n{Fore.RED}❌ CapMonster Network Error: {e}")
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
            'recaptcha-token': captcha_token,
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }
        
        payload = {"operationName": "RequestToken", "query": query, "variables": variables}
        
        try:
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
                        print(f"{Fore.YELLOW}[Account #{idx}] Claiming {t_type}...")
                        success, result = self.claim_token(addr, t_type, token)
                        if success:
                            print(f"{Fore.GREEN}✅ SUCCESS: {result}")
                        else:
                            print(f"{Fore.RED}❌ FAILED: {result}")
                    else:
                        print(f"{Fore.RED}❌ Captcha Solving Failed.")
                    time.sleep(10) # IP rate limit ရှောင်ရန်
            
            print(f"\n{Fore.CYAN}✨ Round {round_count} Finished. Waiting 3 hours...")
            time.sleep(3 * 3600)
            round_count += 1

if __name__ == "__main__":
    bot = CircleFaucetBot()
    bot.run()
