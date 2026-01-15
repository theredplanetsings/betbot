import requests
import time
from typing import List, Dict, Optional
from datetime import datetime

class kalshiclient:
    """fetches market data from kalshi's public api"""
    
    def __init__(self):
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.session = requests.session()
        
    def get_markets(self, limit: int = 50, status: str = "open") -> List[Dict]:
        """fetch active markets"""
        try:
            response = self.session.get(
                f"{self.base_url}/markets",
                params={"limit": limit, "status": status}
            )
            response.raise_for_status()
            return response.json().get("markets", [])
        except Exception as e:
            print(f"failed to fetch kalshi markets: {e}")
            return []
    
    def get_market_orderbook(self, ticker: str) -> dict:
        """fetch orderbook for a specific market"""
        try:
            response = self.session.get(
                f"{self.base_url}/markets/{ticker}/orderbook"
            )
            response.raise_for_status()
            data = response.json()
            
            # parse orderbook
            yes_bids = data.get("yes", [])
            no_bids = data.get("no", [])
            
            return {
                "ticker": ticker,
                "best_yes_bid": yes_bids[0]["price"] / 100 if yes_bids else None,
                "best_yes_ask": yes_bids[0]["price"] / 100 if yes_bids else None,
                "best_no_bid": no_bids[0]["price"] / 100 if no_bids else None,
                "best_no_ask": no_bids[0]["price"] / 100 if no_bids else None,
                "yes_volume": sum(bid.get("quantity", 0) for bid in yes_bids),
                "no_volume": sum(bid.get("quantity", 0) for bid in no_bids),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"failed to fetch orderbook for {ticker}: {e}")
            return {}
    
    def get_event_markets(self, event_ticker: str) -> List[Dict]:
        """fetch all markets for a specific event"""
        try:
            response = self.session.get(
                f"{self.base_url}/events/{event_ticker}/markets"
            )
            response.raise_for_status()
            return response.json().get("markets", [])
        except Exception as e:
            print(f"failed to fetch event markets: {e}")
            return []
    
    def get_market_details(self, ticker: str) -> dict:
        """fetch detailed market information"""
        try:
            time.sleep(0.1)  # rate limiting
            response = self.session.get(f"{self.base_url}/markets/{ticker}")
            response.raise_for_status()
            market = response.json().get("market", {})
            
            # extract key pricing info
            return {
                "ticker": ticker,
                "title": market.get("title", ""),
                "yes_bid": market.get("yes_bid", 0) / 100,
                "yes_ask": market.get("yes_ask", 0) / 100,
                "no_bid": market.get("no_bid", 0) / 100,
                "no_ask": market.get("no_ask", 0) / 100,
                "last_price": market.get("last_price", 0) / 100,
                "volume": market.get("volume", 0),
                "open_interest": market.get("open_interest", 0),
                "close_time": market.get("close_time", ""),
                "status": market.get("status", "")
            }
        except Exception as e:
            print(f"failed to fetch market details for {ticker}: {e}")
            return {}