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
        self.api_url = "https://faucet.circle.com/api/graphql"
        self.accounts = []
        self.network_name = "Arc Testnet"

    def welcome(self):
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("************************************************************")
        print(f"* CIRCLE FAUCET AUTO BOT - {self.network_name}       *")
        print("* SUPPORTING USDC & EURC | 3-HOUR INTERVAL          *")
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
            
            # Browser Payload အတိုင်း အတိအကျ ပြင်ဆင်ထားသော GraphQL Query
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
                    "token": token_type, # "USDC" သို့မဟုတ် "EURC"
                    "blockchain": "ARC"
                }
            }

            headers = {
                'accept': '*/*',
                'content-type': 'application/json',
                'origin': 'https://faucet.circle.com',
                'referer': 'https://faucet.circle.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
            }
            
            payload = {
                "operationName": "RequestToken",
                "query": query,
                "variables": variables
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                res_data = response.json()
                if "errors" in res_data:
                    return False, res_data['errors'][0]['message']
                
                data = res_data.get('data', {}).get('requestToken', {})
                # Hash ပြန်လာရင် အောင်မြင်သည်ဟု ယူဆမည်
                if data.get('hash'):
                    return True, data['hash']
                elif data.get('status'):
                    return False, f"Status: {data.get('status')}"
                return False, "No hash received"
            
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
                # USDC နှင့် EURC နှစ်မျိုးလုံးကို တစ်လှည့်စီ တောင်းမည်
                for token in ["USDC", "EURC"]:
                    print(f"{Fore.YELLOW}[Account #{idx}] Requesting {token}...")
                    
                    success, result = self.claim_token(private_key, token, idx)
                    if success:
                        print(f"{Fore.GREEN}[Account #{idx}] ✅ {token} Success! Hash: {result}")
                    else:
                        print(f"{Fore.RED}[Account #{idx}] ❌ {token} Failed: {result}")
                    
                    # Token တစ်ခုတောင်းပြီးတိုင်း ၅ စက္ကန့် စောင့်မည်
                    time.sleep(5) 
                
                if idx < len(self.accounts):
                    print(f"{Fore.WHITE}⏳ Waiting 15s before next account...")
                    time.sleep(15)
            
            print(f"\n{Fore.CYAN}✨ Round {round_count} finished.")
            
            # ၃ နာရီ စောင့်ဆိုင်းခြင်း
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
