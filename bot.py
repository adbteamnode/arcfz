# -*- coding: utf-8 -*-
import requests
import time
from eth_account import Account
from colorama import Fore, Style, init
import sys

init(autoreset=True)

class CircleFaucetBot:
    def __init__(self):
        self.api_url = "https://faucet.circle.com/api/graphql"
        # သင်ပေးထားတဲ့ Site Key အသစ်
        self.site_key = "6LcNs_0pAAAAAJuAAa-VQryi8XsocHubBk-YlUy2" 
        self.page_url = "https://faucet.circle.com"
        self.accounts = []
        self.captcha_api_key = ""

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
        print(f"{Fore.CYAN}[Account #{idx}] ⏳ Solving Captcha...")
        params = {
            'key': self.captcha_api_key,
            'method': 'userrecaptcha',
            'googlekey': self.site_key,
            'pageurl': self.page_url,
            'invisible': 1, # Invisible captcha ဖြစ်လို့ ၁ ထည့်ပေးရပါတယ်
            'json': 1
        }
        try:
            res = requests.post("http://2captcha.com/in.php", data=params).json()
            if res.get('status') != 1: return None
            
            job_id = res.get('request')
            for _ in range(60): # ၁ မိနစ်အထိ စောင့်မယ်
                time.sleep(5)
                res = requests.get(f"http://2captcha.com/res.php?key={self.captcha_api_key}&action=get&id={job_id}&json=1").json()
                if res.get('status') == 1:
                    print(f"{Fore.GREEN}[Account #{idx}] ✅ Captcha Solved!")
                    return res.get('request')
            return None
        except: return None

    def claim_token(self, address, token_type, captcha_token):
        # သင်ပေးထားတဲ့ Payload အတိုင်း အတိအကျ ပြန်ပြင်ထားပါတယ်
        query = """
        mutation RequestToken($input: RequestTokenInput!) {
          requestToken(input: $input) {
            ...RequestTokenResponseInfo
            __typename
          }
        }

        fragment RequestTokenResponseInfo on RequestTokenResponse {
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
        
        # Header မှာ recaptcha-token ထည့်ရမယ်လို့ သင်ပြောတဲ့အတွက် ဒီမှာ ထည့်ပေးထားပါတယ်
        headers = {
            'content-type': 'application/json',
            'origin': 'https://faucet.circle.com',
            'referer': 'https://faucet.circle.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'recaptcha-token': captcha_token 
        }
        
        payload = {
            "operationName": "RequestToken",
            "query": query,
            "variables": variables
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            return response.json()
        except Exception as e:
            return {"errors": [{"message": str(e)}]}

    def run(self):
        self.load_config()
        round_count = 1
        
        while True:
            print(f"\n{Fore.MAGENTA}=== STARTING ROUND {round_count} ===")
            for idx, addr in enumerate(self.accounts, 1):
                # Circle မှာ Token တစ်ခုချင်းစီအတွက် Captcha အသစ် ဖြေပေးရလေ့ရှိပါတယ်
                for t_type in ["USDC", "EURC"]:
                    captcha_token = self.solve_captcha(idx)
                    if captcha_token:
                        print(f"{Fore.YELLOW}[Account #{idx}] Requesting {t_type}...")
                        result = self.claim_token(addr, t_type, captcha_token)
                        
                        if 'data' in result and result['data']['requestToken'].get('hash'):
                            tx = result['data']['requestToken']['hash']
                            print(f"{Fore.GREEN}[Account #{idx}] ✅ {t_type} Success! Hash: {tx}")
                        else:
                            error = result.get('errors', [{'message': 'Unknown Error'}])[0]['message']
                            print(f"{Fore.RED}[Account #{idx}] ❌ {t_type} Failed: {error}")
                    else:
                        print(f"{Fore.RED}[Account #{idx}] ❌ Captcha bypass failed.")
                    
                    time.sleep(5) # Token တစ်ခုနဲ့တစ်ခုကြား စောင့်ဆိုင်းချိန်

                if idx < len(self.accounts):
                    print(f"{Fore.WHITE}⏳ Waiting 15s before next account...")
                    time.sleep(15)

            # ၃ နာရီ စောင့်ဆိုင်းခြင်း
            print(f"\n{Fore.CYAN}✨ Round {round_count} finished.")
            total_seconds = 3 * 60 * 60
            while total_seconds > 0:
                h, m, s = total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60
                print(f"{Fore.YELLOW}Next round in: {h:02d}:{m:02d}:{s:02d}", end="\r")
                time.sleep(1)
                total_seconds -= 1
            round_count += 1

if __name__ == "__main__":
    bot = CircleFaucetBot()
    bot.run()
