# -*- coding: utf-8 -*-
import requests
import time
import json
from eth_account import Account
from colorama import Fore, Style, init
import sys

init(autoreset=True)

class CircleFaucetBot:
    def __init__(self):
        # Circle Faucet GraphQL API
        self.api_url = "https://faucet.circle.com/api/graphql"
        self.accounts = []
        
        # Network Info (Arc Testnet)
        self.network_name = "Arc Testnet"

    def welcome(self):
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("************************************************************")
        print(f"* CIRCLE FAUCET AUTO BOT - {self.network_name}       *")
        print("* NO CAPTCHA MODE | 3-HOUR INTERVAL                 *")
        print("************************************************************")
        print("-" * 60)

    def load_accounts(self, filename='wallets.txt'):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.accounts = [line.strip() for line in f if line.strip()]
            print(f"{Fore.GREEN}✅ Loaded {len(self.accounts)} accounts")
        except FileNotFoundError:
            print(f"{Fore.RED}❌ {filename} not found!")
            sys.exit(1)

    def claim_token(self, private_key, token_type, idx):
        try:
            account = Account.from_key(private_key)
            address = account.address
            
            # GraphQL Mutation Payload (No Captcha Version)
            query = """
            mutation RequestTestnetTokens($input: RequestTestnetTokensInput!) {
              requestTestnetTokens(input: $input) {
                transactionHash
              }
            }
            """
            
            variables = {
                "input": {
                    "address": address,
                    "blockchain": "ARC", 
                    "network": "TESTNET",
                    "token": token_type,
                    "captchaToken": "" # Captcha မလိုတဲ့အတွက် အလွတ်ထားပါတယ်
                }
            }

            headers = {
                'content-type': 'application/json',
                'origin': 'https://faucet.circle.com',
                'referer': 'https://faucet.circle.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            payload = {"query": query, "variables": variables}
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_data = response.json()
                if "errors" in res_data:
                    return False, res_data['errors'][0]['message']
                
                # Check if data exists
                if res_data.get('data') and res_data['data'].get('requestTestnetTokens'):
                    tx_hash = res_data['data']['requestTestnetTokens']['transactionHash']
                    return True, tx_hash
                return False, "Unknown Error in Response"
            
            return False, f"HTTP Error {response.status_code}"
            
        except Exception as e:
            return False, str(e)

    def run(self):
        self.welcome()
        self.load_accounts()
        
        round_count = 1
        while True:
            print(f"\n{Fore.MAGENTA}=== STARTING ROUND {round_count} ===")
            
            for idx, private_key in enumerate(self.accounts, 1):
                # USDC & EURC နှစ်မျိုးလုံး တောင်းမယ်
                for token in ["USDC", "EURC"]:
                    print(f"{Fore.YELLOW}[Account #{idx}] Requesting {token}...")
                    
                    success, result = self.claim_token(private_key, token, idx)
                    if success:
                        print(f"{Fore.GREEN}[Account #{idx}] ✅ {token} Success! Tx: {result}")
                    else:
                        print(f"{Fore.RED}[Account #{idx}] ❌ {token} Failed: {result}")
                    
                    time.sleep(2) # တစ်ခုနဲ့တစ်ခုကြား ၂ စက္ကန့် စောင့်မယ်
                
                if idx < len(self.accounts):
                    # အကောင့်တစ်ခုနဲ့တစ်ခုကြား IP block မဖြစ်အောင် ၁၀ စက္ကန့် စောင့်ခိုင်းထားပါတယ်
                    print(f"{Fore.WHITE}⏳ Waiting 10s before next account...")
                    time.sleep(10)
            
            print(f"\n{Fore.CYAN}✨ Round {round_count} finished.")
            
            # ၃ နာရီ စောင့်ဆိုင်းခြင်း (3 hours = 10800 seconds)
            total_seconds = 3 * 60 * 60
            while total_seconds > 0:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                print(f"{Fore.YELLOW}Next round in: {hours:02d}:{minutes:02d}:{seconds:02d}", end="\r")
                time.sleep(1)
                total_seconds -= 1
            
            round_count += 1

if __name__ == "__main__":
    bot = CircleFaucetBot()
    bot.run()
