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
        self.accounts = []
        self.captcha_api_key = ""

    def welcome(self):
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("************************************************************")
        print(f"* ARC TESTNET - CIRCLE FAUCET AUTO BOT              *")
        print("* FIXED: ACTION HEADER + DUAL TOKEN                 *")
        print("************************************************************")
        print("-" * 60)

    def load_config(self):
        try:
            with open('captcha_key.txt', 'r') as f:
                self.captcha_api_key = f.readline().strip()
            with open('wallets.txt', 'r') as f:
                self.accounts = [l.strip() for l in f if l.strip()]
            print(f"{Fore.GREEN}✅ Loaded {len(self.accounts)} accounts and 2Captcha key.")
        except Exception as e:
            print(f"{Fore.RED}❌ Error loading files: {e}")
            sys.exit(1)

    def solve_captcha(self, idx):
        print(f"{Fore.CYAN}[Account #{idx}] ⏳ Solving ReCAPTCHA via 2Captcha...")
        params = {
            'key': self.captcha_api_key,
            'method': 'userrecaptcha',
            'googlekey': self.site_key,
            'pageurl': self.page_url,
            'invisible': 1,
            'json': 1
        }
        try:
            res = requests.post("http://2captcha.com/in.php", data=params).json()
            if res.get('status') != 1: 
                print(f"{Fore.RED}❌ 2Captcha Error: {res.get('request')}")
                return None
            
            job_id = res.get('request')
            for _ in range(60):
                time.sleep(5)
                res = requests.get(f"http://2captcha.com/res.php?key={self.captcha_api_key}&action=get&id={job_id}&json=1").json()
                if res.get('status') == 1:
                    print(f"{Fore.GREEN}[Account #{idx}] ✅ Captcha Solved!")
                    return res.get('request')
            return None
        except Exception as e:
            print(f"{Fore.RED}❌ Captcha Exception: {e}")
            return None

    def claim_token(self, address, token_type, captcha_token):
        query = """
        mutation RequestToken($input: RequestTokenInput!) {
          requestToken(input: $input) {
            ...RequestTokenResponseInfo
            __typename
          }
        }

        fragment RequestTokenResponseInfo on RequestTokenResponse {
          amount
          blockchain
          contractAddress
          currency
          destinationAddress
          explorerLink
          hash
          status
          __typename
        }
        """
        
        variables = {
            "input": {
                "destinationAddress": address,
                "token": token_type,
                "blockchain": "ARC"
            }
        }
        
        # သင်ပေးလိုက်တဲ့ Header နှစ်ခုလုံးကို အတိအကျ ထည့်သွင်းထားပါတယ်
        headers = {
            'accept': '*/*',
            'content-type': 'application/json',
            'origin': 'https://faucet.circle.com',
            'referer': 'https://faucet.circle.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'recaptcha-action': 'request_token',  # အသစ်ထည့်လိုက်သော Header
            'recaptcha-token': captcha_token      # Captcha Token Header
        }
        
        payload = {
            "operationName": "RequestToken",
            "query": query,
            "variables": variables
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
            res_json = response.json()
            
            if 'errors' in res_json:
                return False, res_json['errors'][0]['message']
            
            data = res_json.get('data', {}).get('requestToken', {})
            if data and data.get('hash'):
                return True, data['hash']
            elif data and data.get('status'):
                return False, f"Status: {data['status']}"
            
            return False, "Response missing data/hash."
        except Exception as e:
            return False, str(e)

    def run(self):
        self.welcome()
        self.load_config()
        round_count = 1
        
        while True:
            print(f"\n{Fore.MAGENTA}=== STARTING ROUND {round_count} ===")
            for idx, addr in enumerate(self.accounts, 1):
                for t_type in ["USDC", "EURC"]:
                    # Token တစ်ခုစီအတွက် Captcha အသစ် တောင်းခံဖြေရှင်းခြင်း
                    captcha_token = self.solve_captcha(idx)
                    
                    if captcha_token:
                        print(f"{Fore.YELLOW}[Account #{idx}] Requesting {t_type} for {addr}...")
                        success, result = self.claim_token(addr, t_type, captcha_token)
                        
                        if success:
                            print(f"{Fore.GREEN}[Account #{idx}] ✅ {t_type} Success! Hash: {result}")
                        else:
                            print(f"{Fore.RED}[Account #{idx}] ❌ {t_type} Failed: {result}")
                    else:
                        print(f"{Fore.RED}[Account #{idx}] ❌ Captcha bypass failed.")
                    
                    time.sleep(5)

                if idx < len(self.accounts):
                    print(f"{Fore.WHITE}⏳ Waiting 15s before next account...")
                    time.sleep(15)

            print(f"\n{Fore.CYAN}✨ Round {round_count} finished.")
            
            # ၃ နာရီ စောင့်ဆိုင်းခြင်း
            total_seconds = 3 * 60 * 60
            while total_seconds > 0:
                h, m, s = total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60
                print(f"{Fore.YELLOW}Next round in: {h:02d}:{minutes:02d}:{s:02d}", end="\r")
                time.sleep(1)
                total_seconds -= 1
            round_count += 1

if __name__ == "__main__":
    bot = CircleFaucetBot()
    bot.run()
