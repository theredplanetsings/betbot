import requests
import time
from typing import list, dict, optional
from datetime import datetime


class polymarketclient:
    """fetches market data from polymarket's public api"""
    
    def __init__(self):
        # polymarket uses clob api for orderbook data
        self.clob_url = "https://clob.polymarket.com"
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.session = requests.session()
        
    def get_markets(self, limit: int = 100, active: bool = true) -> list[dict]:
        """fetch active markets"""
        try:
            params = {
                "limit": limit,
                "active": str(active).lower()
            }
            response = self.session.get(
                f"{self.gamma_url}/markets",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except exception as e:
            print(f"failed to fetch polymarket markets: {e}")
            return []
    
    def get_market_orderbook(self, token_id: str) -> dict:
        """fetch orderbook for a specific market token"""
        try:
            response = self.session.get(
                f"{self.clob_url}/book",
                params={"token_id": token_id}
            )
            response.raise_for_status()
            data = response.json()
            
            bids = data.get("bids", [])
            asks = data.get("asks", [])
            
            return {
                "token_id": token_id,
                "best_bid": float(bids[0]["price"]) if bids else None,
                "best_ask": float(asks[0]["price"]) if asks else None,
                "bid_size": float(bids[0]["size"]) if bids else 0,
                "ask_size": float(asks[0]["size"]) if asks else 0,
                "timestamp": datetime.now().isoformat()
            }
        except exception as e:
            print(f"failed to fetch orderbook for {token_id}: {e}")
            return {}
    
    def get_market_price(self, condition_id: str) -> dict:
        """fetch current market price"""
        try:
            response = self.session.get(
                f"{self.gamma_url}/markets/{condition_id}"
            )
            response.raise_for_status()
            market = response.json()
            
            # polymarket has binary outcomes (yes or no)
            tokens = market.get("tokens", [])
            
            result = {
                "condition_id": condition_id,
                "question": market.get("question", ""),
                "active": market.get("active", false),
                "closed": market.get("closed", false),
                "end_date": market.get("end_date_iso", ""),
                "volume": float(market.get("volume", 0)),
                "liquidity": float(market.get("liquidity", 0)),
            }
            
            # extract token prices (usually 2 tokens: yes/no)
            for token in tokens:
                outcome = token.get("outcome", "").lower()
                price = float(token.get("price", 0))
                token_id = token.get("token_id", "")
                
                if outcome == "yes":
                    result["yes_price"] = price
                    result["yes_token_id"] = token_id
                elif outcome == "no":
                    result["no_price"] = price
                    result["no_token_id"] = token_id
                    
            return result
        except exception as e:
            print(f"failed to fetch market price for {condition_id}: {e}")
            return {}
    
    def search_markets(self, query: str) -> list[dict]:
        """search for markets by keyword"""
        try:
            response = self.session.get(
                f"{self.gamma_url}/search",
                params={"q": query}
            )
            response.raise_for_status()
            return response.json()
        except exception as e:
            print(f"failed to search markets: {e}")
            return []
    
    def get_simplified_markets(self) -> list[dict]:
        """fetch markets in simplified format for scanning"""
        markets = self.get_markets(limit=200)
        simplified = []
        
        for market in markets:
            if not market.get("active", false):
                continue
                
            tokens = market.get("tokens", [])
            yes_token = next((t for t in tokens if t.get("outcome", "").lower() == "yes"), none)
            no_token = next((t for t in tokens if t.get("outcome", "").lower() == "no"), none)
            
            if yes_token and no_token:
                simplified.append({
                    "condition_id": market.get("condition_id", ""),
                    "question": market.get("question", ""),
                    "yes_price": float(yes_token.get("price", 0)),
                    "no_price": float(no_token.get("price", 0)),
                    "yes_token_id": yes_token.get("token_id", ""),
                    "no_token_id": no_token.get("token_id", ""),
                    "volume": float(market.get("volume", 0)),
                    "liquidity": float(market.get("liquidity", 0)),
                    "end_date": market.get("end_date_iso", "")
                })
        
        return simplified