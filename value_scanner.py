from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

class valuescanner:
    """scans for high value betting opportunities based on probability analysis"""
    
    def __init__(self, kalshi_client, polymarket_client):
        self.kalshi = kalshi_client
        self.polymarket = polymarket_client
        self.min_edge = 0.05  # 5% edge minimum
        self.time_window_hours = None  # no filter by default
    
    def set_time_window(self, hours: Optional[float]):
        """set time window for filtering markets"""
        self.time_window_hours = hours
        
    def find_mispriced_markets(self, platform: str = "kalshi") -> List[Dict]:
        """
        finds markets where yes + no prices don't sum to 1,
        indicating potential value on one side.
        """
        opportunities = []
        
        if platform == "kalshi":
            markets = self.kalshi.get_markets(limit=20)  # reduced to avoid rate limits
            
            for market in markets:
                ticker = market.get("ticker", "")
                details = self.kalshi.get_market_details(ticker)
                
                yes_ask = details.get("yes_ask", 0)
                no_ask = details.get("no_ask", 0)
                yes_bid = details.get("yes_bid", 0)
                no_bid = details.get("no_bid", 0)
                
                if yes_ask and no_ask:
                    # if yes + no > 1, platform takes vig (expected)
                    # if yes + no < 1, there's inefficiency
                    total_ask = yes_ask + no_ask
                    
                    # check for value on yes side
                    if yes_bid > 0:
                        implied_prob_yes = yes_ask
                        fair_value_yes = 1 - no_ask
                        edge_yes = fair_value_yes - implied_prob_yes
                        
                        if edge_yes > self.min_edge:
                            expected_profit = edge_yes
                            kalshi_fee = expected_profit * 0.07
                            net_profit = expected_profit - kalshi_fee
                            
                            opportunities.append({
                                "type": "value_bet",
                                "platform": "kalshi",
                                "market": ticker,
                                "title": details.get("title", ""),
                                "side": "yes",
                                "trade_details": {
                                    "action": "buy yes",
                                    "entry_price": yes_ask,
                                    "position_size": 1.0,
                                    "max_payout": 1.0
                                },
                                "price": yes_ask,
                                "fair_value": fair_value_yes,
                                "edge": edge_yes,
                                "edge_percentage": edge_yes * 100,
                                "expected_profit": expected_profit,
                                "fees": {
                                    "platform_fee": kalshi_fee,
                                    "gas_fee": 0,
                                    "total_fees": kalshi_fee
                                },
                                "net_expected_profit": net_profit,
                                "roi_percentage": (net_profit / yes_ask) * 100,
                                "volume": details.get("volume", 0),
                                "liquidity": details.get("open_interest", 0),
                                "timestamp": datetime.now().isoformat()
                            })
                    
                    # check for value on no side
                    if no_bid > 0:
                        implied_prob_no = no_ask
                        fair_value_no = 1 - yes_ask
                        edge_no = fair_value_no - implied_prob_no
                        
                        if edge_no > self.min_edge:
                            expected_profit = edge_no
                            kalshi_fee = expected_profit * 0.07
                            net_profit = expected_profit - kalshi_fee
                            
                            opportunities.append({
                                "type": "value_bet",
                                "platform": "kalshi",
                                "market": ticker,
                                "title": details.get("title", ""),
                                "side": "no",
                                "trade_details": {
                                    "action": "buy no",
                                    "entry_price": no_ask,
                                    "position_size": 1.0,
                                    "max_payout": 1.0
                                },
                                "price": no_ask,
                                "fair_value": fair_value_no,
                                "edge": edge_no,
                                "edge_percentage": edge_no * 100,
                                "expected_profit": expected_profit,
                                "fees": {
                                    "platform_fee": kalshi_fee,
                                    "gas_fee": 0,
                                    "total_fees": kalshi_fee
                                },
                                "net_expected_profit": net_profit,
                                "roi_percentage": (net_profit / no_ask) * 100,
                                "volume": details.get("volume", 0),
                                "liquidity": details.get("open_interest", 0),
                                "timestamp": datetime.now().isoformat()
                            })
        
        elif platform == "polymarket":
            markets = self.polymarket.get_simplified_markets(self.time_window_hours)
            
            for market in markets:
                yes_price = market.get("yes_price", 0)
                no_price = market.get("no_price", 0)
                
                if yes_price and no_price:
                    # check yes side value
                    fair_value_yes = 1 - no_price
                    edge_yes = fair_value_yes - yes_price
                    
                    if edge_yes > self.min_edge:
                        expected_profit = edge_yes
                        gas_fee = 0.02
                        net_profit = expected_profit - gas_fee
                        
                        opportunities.append({
                            "type": "value_bet",
                            "platform": "polymarket",
                            "market": market.get("condition_id", ""),
                            "question": market.get("question", ""),
                            "side": "yes",
                            "trade_details": {
                                "action": "buy yes",
                                "entry_price": yes_price,
                                "token_id": market.get("yes_token_id", ""),
                                "position_size": 1.0,
                                "max_payout": 1.0
                            },
                            "price": yes_price,
                            "fair_value": fair_value_yes,
                            "edge": edge_yes,
                            "edge_percentage": edge_yes * 100,
                            "expected_profit": expected_profit,
                            "fees": {
                                "platform_fee": 0,
                                "gas_fee": gas_fee,
                                "total_fees": gas_fee
                            },
                            "net_expected_profit": net_profit,
                            "roi_percentage": (net_profit / yes_price) * 100 if yes_price > 0 else 0,
                            "volume": market.get("volume", 0),
                            "liquidity": market.get("liquidity", 0),
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    # check no side value
                    fair_value_no = 1 - yes_price
                    edge_no = fair_value_no - no_price
                    
                    if edge_no > self.min_edge:
                        expected_profit = edge_no
                        gas_fee = 0.02
                        net_profit = expected_profit - gas_fee
                        
                        opportunities.append({
                            "type": "value_bet",
                            "platform": "polymarket",
                            "market": market.get("condition_id", ""),
                            "question": market.get("question", ""),
                            "side": "no",
                            "trade_details": {
                                "action": "buy no",
                                "entry_price": no_price,
                                "token_id": market.get("no_token_id", ""),
                                "position_size": 1.0,
                                "max_payout": 1.0
                            },
                            "price": no_price,
                            "fair_value": fair_value_no,
                            "edge": edge_no,
                            "edge_percentage": edge_no * 100,
                            "expected_profit": expected_profit,
                            "fees": {
                                "platform_fee": 0,
                                "gas_fee": gas_fee,
                                "total_fees": gas_fee
                            },
                            "net_expected_profit": net_profit,
                            "roi_percentage": (net_profit / no_price) * 100 if no_price > 0 else 0,
                            "volume": market.get("volume", 0),
                            "liquidity": market.get("liquidity", 0),
                            "timestamp": datetime.now().isoformat()
                        })
        
        return sorted(opportunities, key=lambda x: x["edge_percentage"], reverse=True)
    
    def find_extreme_probabilities(self, platform: str = "kalshi", threshold: float = 0.9) -> List[Dict]:
        """
        finds markets with extreme probabilities (>90% or <10%).
        these might represent high confidence opportunities or potential traps.
        """
        opportunities = []
        
        if platform == "kalshi":
            markets = self.kalshi.get_markets(limit=20)  #reduced to avoid the rate limits
            
            for market in markets:
                ticker = market.get("ticker", "")
                details = self.kalshi.get_market_details(ticker)
                
                yes_ask = details.get("yes_ask", 0)
                
                if yes_ask > threshold or yes_ask < (1 - threshold):
                    opportunities.append({
                        "type": "extreme_probability",
                        "platform": "kalshi",
                        "market": ticker,
                        "title": details.get("title", ""),
                        "yes_price": yes_ask,
                        "confidence": "high_yes" if yes_ask > threshold else "high_no",
                        "volume": details.get("volume", 0),
                        "liquidity": details.get("open_interest", 0),
                        "close_time": details.get("close_time", ""),
                        "timestamp": datetime.now().isoformat()
                    })
        
        elif platform == "polymarket":
            markets = self.polymarket.get_simplified_markets(self.time_window_hours)
            
            for market in markets:
                yes_price = market.get("yes_price", 0)
                
                if yes_price > threshold or yes_price < (1 - threshold):
                    opportunities.append({
                        "type": "extreme_probability",
                        "platform": "polymarket",
                        "market": market.get("condition_id", ""),
                        "question": market.get("question", ""),
                        "yes_price": yes_price,
                        "confidence": "high_yes" if yes_price > threshold else "high_no",
                        "volume": market.get("volume", 0),
                        "liquidity": market.get("liquidity", 0),
                        "end_date": market.get("end_date", ""),
                        "timestamp": datetime.now().isoformat()
                    })
        
        return sorted(opportunities, key=lambda x: abs(x["yes_price"] - 0.5), reverse=True)
    
    def find_high_liquidity_value(self, platform: str = "kalshi", min_volume: float = 1000) -> List[Dict]:
        """
        finds value opportunities with sufficient liquidity to actually execute.
        filters for markets with good volume.
        """
        value_bets = self.find_mispriced_markets(platform)
        
        # filter for liquidity
        liquid_opportunities = [
            bet for bet in value_bets
            if bet.get("volume", 0) > min_volume or bet.get("liquidity", 0) > min_volume
        ]
        
        return liquid_opportunities
    
    def scan_all_value(self) -> dict:
        """runs all value scans and returns consolidated results"""
        results = {
            "scan_time": datetime.now().isoformat(),
            "kalshi_value": self.find_mispriced_markets("kalshi"),
            "polymarket_value": self.find_mispriced_markets("polymarket"),
            "kalshi_extremes": self.find_extreme_probabilities("kalshi"),
            "polymarket_extremes": self.find_extreme_probabilities("polymarket"),
            "kalshi_liquid_value": self.find_high_liquidity_value("kalshi"),
            "polymarket_liquid_value": self.find_high_liquidity_value("polymarket")
        }
        
        results["summary"] = {
            "total_value_opportunities": len(results["kalshi_value"]) + len(results["polymarket_value"]),
            "total_extreme_probabilities": len(results["kalshi_extremes"]) + len(results["polymarket_extremes"]),
            "total_liquid_value": len(results["kalshi_liquid_value"]) + len(results["polymarket_liquid_value"])
        }
        
        return results