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
        self.max_retries = 3 # တစ်ကောင့်ကို ၃ ကြိမ်အထိ Retry လုပ်မည်

    def welcome(self):
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("************************************************************")
        print(f"* ARC TESTNET - CIRCLE FAUCET (RETRY LOGIC ENABLED) *")
        print("* INTERVAL: 2 HOURS 2 MINUTES | RETRIES: 3 TIMES   *")
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
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        try:
            self.session.get(self.page_url, headers=headers, timeout=15)
            print(f"{Fore.YELLOW}🔄 Cloudflare Session Refreshed.")
        except:
            print(f"{Fore.RED}⚠️ Session Refresh Error.")

    def solve_captcha(self, idx):
        print(f"{Fore.CYAN}[Account #{idx}] ⏳ Requesting CapMonster...")
        payload = {
            "clientKey": self.captcha_api_key,
            "task": {
                "type": "RecaptchaV3TaskProxyless",
                "websiteURL": self.page_url,
                "websiteKey": self.site_key,
                "minScore": 0.9,
                "pageAction": "request_token",
                "isEnterprise": True
            }
        }
        try:
            create_res = requests.post("https://api.capmonster.cloud/createTask", json=payload, timeout=20).json()
            if create_res.get('errorId') != 0:
                print(f"{Fore.RED}❌ CapMonster Error: {create_res.get('errorCode')}")
                return None
            
            task_id = create_res.get('taskId')
            for _ in range(30):
                time.sleep(3)
                result_payload = {"clientKey": self.captcha_api_key, "taskId": task_id}
                res = requests.post("https://api.capmonster.cloud/getTaskResult", json=result_payload, timeout=20).json()
                if res.get('status') == "ready":
                    return res.get('solution', {}).get('gRecaptchaResponse')
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
            response = self.session.post(self.api_url, json=payload, headers=headers, timeout=30)
            res_json = response.json()
            if 'errors' in res_json:
                return False, res_json['errors'][0]['message']
            
            data = res_json.get('data', {}).get('requestToken', {})
            if data:
                if data.get('hash'):
                    return True, data['hash']
                elif data.get('status') == 'success':
                    return True, "Request submitted (Status: Success)"
            return False, f"Status: {data.get('status', 'Unknown')}"
        except Exception as e:
            return False, str(e)

    def process_account(self, idx, addr, t_type):
        """အကောင့်တစ်ခုချင်းစီအတွက် Retry Logic ဖြင့် Claim ခြင်း"""
        for attempt in range(1, self.max_retries + 1):
            retry_msg = f" (Attempt {attempt}/{self.max_retries})" if attempt > 1 else ""
            print(f"{Fore.YELLOW}[Account #{idx}] Claiming {t_type}{retry_msg}...")
            
            token = self.solve_captcha(idx)
            if not token:
                print(f"{Fore.RED}❌ Captcha Solving Failed. Retrying...")
                continue
            
            success, result = self.claim_token(addr, t_type, token)
            if success:
                print(f"{Fore.GREEN}✅ SUCCESS: {result}")
                return True
            else:
                print(f"{Fore.RED}❌ FAILED: {result}")
                
                # အကယ်၍ Error က Captcha ကြောင့်မဟုတ်ဘဲ တခြားကန့်သတ်ချက်ကြောင့်ဆိုရင် Retry မလုပ်တော့ပါ
                stop_errors = ["rate limit", "cooldown", "already", "denied", "forbidden"]
                if any(err in result.lower() for err in stop_errors):
                    print(f"{Fore.YELLOW}ℹ️ Stopping retries for this account due to permanent error.")
                    break
                
                if attempt < self.max_retries:
                    print(f"{Fore.WHITE}⏳ Waiting 10s before retry...")
                    time.sleep(10)
        return False

    def run(self):
        self.welcome()
        self.load_config()
        round_count = 1
        while True:
            print(f"\n{Fore.MAGENTA}=== ROUND {round_count} START ===")
            self.refresh_session()
            for idx, addr in enumerate(self.accounts, 1):
                for t_type in ["USDC", "EURC"]:
                    self.process_account(idx, addr, t_type)
                    time.sleep(5)
            
            print(f"\n{Fore.CYAN}✨ Round {round_count} Finished.")
            total_seconds = (2 * 60 * 60) + (2 * 60) 
            while total_seconds > 0:
                h, m, s = total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60
                print(f"{Fore.YELLOW}Next round in: {h:02d}:{m:02d}:{s:02d}", end="\r")
                time.sleep(1)
                total_seconds -= 1
            round_count += 1

if __name__ == "__main__":
    bot = CircleFaucetBot()
    bot.run()
