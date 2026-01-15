from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time

class arbitragescanner:
    """scans for arbitrage opportunities between polymarket and kalshi"""
    
    def __init__(self, kalshi_client, polymarket_client):
        self.kalshi = kalshi_client
        self.polymarket = polymarket_client
        self.min_profit_threshold = 0.02  # 2% minimum profit
        self.time_window_hours = None  # no filter by default
    
    def set_time_window(self, hours: Optional[float]):
        """set time window for filtering markets (e.g., 1, 0.25 for 15min, 0.5 for 30min)"""
        self.time_window_hours = hours
        
    def find_cross_platform_arbitrage(self) -> List[Dict]:
        """
        finds arbitrage opportunities between kalshi and polymarket.
        looks for same event priced differently on both platforms.
        """
        opportunities = []
        
        # fetch markets from both platforms with time window
        kalshi_params = {"limit": 50}
        if self.time_window_hours:
            max_close_ts = int((datetime.now() + timedelta(hours=self.time_window_hours)).timestamp())
            kalshi_params["max_close_ts"] = max_close_ts
        
        kalshi_markets = self.kalshi.get_markets(**kalshi_params)
        polymarket_markets = self.polymarket.get_simplified_markets(self.time_window_hours)
        
        # match markets by similarity in titles/questions
        for k_market in kalshi_markets:
            k_title = k_market.get("title", "").lower()
            
            for p_market in polymarket_markets:
                p_question = p_market.get("question", "").lower()
                
                # basic keyword matching (you'd improve this with better matching logic)
                if self._markets_match(k_title, p_question):
                    arb = self._calculate_arbitrage(k_market, p_market)
                    if arb:
                        opportunities.append(arb)
        
        return sorted(opportunities, key=lambda x: x["profit_percentage"], reverse=True)
    
    def _markets_match(self, title1: str, title2: str) -> bool:
        """check if two market titles likely refer to same event"""
        # extract key words (skip common words)
        skip_words = {"will", "the", "be", "a", "an", "in", "on", "at", "to", "for"}
        
        words1 = set(word for word in title1.split() if word not in skip_words and len(word) > 2)
        words2 = set(word for word in title2.split() if word not in skip_words and len(word) > 2)
        
        # need significant overlap
        if not words1 or not words2:
            return False
            
        overlap = len(words1 & words2) / min(len(words1), len(words2))
        return overlap > 0.5
    
    def _calculate_arbitrage(self, kalshi_market: dict, polymarket_market: dict) -> Optional[Dict]:
        """
        calculates if arbitrage exists between two matched markets.
        arbitrage exists when you can bet on both outcomes and guarantee profit.
        """
        # get pricing from kalshi
        k_yes_ask = kalshi_market.get("yes_ask", 0)
        k_no_ask = kalshi_market.get("no_ask", 0)
        
        # get pricing from polymarket
        p_yes_price = polymarket_market.get("yes_price", 0)
        p_no_price = polymarket_market.get("no_price", 0)
        
        if not all([k_yes_ask, k_no_ask, p_yes_price, p_no_price]):
            return None
        
        # strategy 1: buy yes on cheaper platform, no on other
        cost1_kalshi_yes = k_yes_ask
        cost1_poly_no = p_no_price
        total_cost1 = cost1_kalshi_yes + cost1_poly_no
        
        # kalshi fee: 7% on profits, polymarket: ~2% gas + 2% platform
        kalshi_fee_rate = 0.07
        polymarket_fee_rate = 0.04  # 2% platform + ~2% gas estimate
        
        cost2_poly_yes = p_yes_price
        cost2_kalshi_no = k_no_ask
        total_cost2 = cost2_poly_yes + cost2_kalshi_no
        
        # arbitrage exists if total cost < 1 (guaranteed profit)
        if total_cost1 < 1:
            gross_profit = 1 - total_cost1
            kalshi_profit_fee = gross_profit * kalshi_fee_rate
            polymarket_gas = 0.02  # estimated gas in dollars
            net_profit = gross_profit - kalshi_profit_fee - polymarket_gas
            profit_pct = (net_profit / total_cost1) * 100
            
            if profit_pct >= self.min_profit_threshold * 100:
                return {
                    "type": "cross_platform_arbitrage",
                    "kalshi_market": kalshi_market.get("ticker", ""),
                    "polymarket_market": polymarket_market.get("condition_id", ""),
                    "kalshi_title": kalshi_market.get("title", ""),
                    "polymarket_question": polymarket_market.get("question", ""),
                    "strategy": "buy yes on kalshi, no on polymarket",
                    "trade_details": {
                        "kalshi_side": "yes",
                        "kalshi_price": cost1_kalshi_yes,
                        "polymarket_side": "no",
                        "polymarket_price": cost1_poly_no,
                        "position_size": 1.0
                    },
                    "total_cost": total_cost1,
                    "guaranteed_return": 1.0,
                    "gross_profit": gross_profit,
                    "fees": {
                        "kalshi_fee": kalshi_profit_fee,
                        "polymarket_gas": polymarket_gas,
                        "total_fees": kalshi_profit_fee + polymarket_gas
                    },
                    "net_profit": net_profit,
                    "profit_percentage": profit_pct,
                    "roi_percentage": (net_profit / total_cost1) * 100,
                    "timestamp": datetime.now().isoformat()
                }
        
        if total_cost2 < 1:
            gross_profit = 1 - total_cost2
            kalshi_profit_fee = gross_profit * kalshi_fee_rate
            polymarket_gas = 0.02
            net_profit = gross_profit - kalshi_profit_fee - polymarket_gas
            profit_pct = (net_profit / total_cost2) * 100
            
            if profit_pct >= self.min_profit_threshold * 100:
                return {
                    "type": "cross_platform_arbitrage",
                    "kalshi_market": kalshi_market.get("ticker", ""),
                    "polymarket_market": polymarket_market.get("condition_id", ""),
                    "kalshi_title": kalshi_market.get("title", ""),
                    "polymarket_question": polymarket_market.get("question", ""),
                    "strategy": "buy yes on polymarket, no on kalshi",
                    "trade_details": {
                        "polymarket_side": "yes",
                        "polymarket_price": cost2_poly_yes,
                        "kalshi_side": "no",
                        "kalshi_price": cost2_kalshi_no,
                        "position_size": 1.0
                    },
                    "total_cost": total_cost2,
                    "guaranteed_return": 1.0,
                    "gross_profit": gross_profit,
                    "fees": {
                        "kalshi_fee": kalshi_profit_fee,
                        "polymarket_gas": polymarket_gas,
                        "total_fees": kalshi_profit_fee + polymarket_gas
                    },
                    "net_profit": net_profit,
                    "profit_percentage": profit_pct,
                    "roi_percentage": (net_profit / total_cost2) * 100,
                    "timestamp": datetime.now().isoformat()
                }
        
        return None
    
    def find_internal_arbitrage(self, platform: str = "kalshi") -> List[Dict]:
        """
        finds arbitrage within single platform.
        checks if yes + no prices don't sum to 1.
        """
        opportunities = []
        
        if platform == "kalshi":
            kalshi_params = {"limit": 50}
            if self.time_window_hours:
                max_close_ts = int((datetime.now() + timedelta(hours=self.time_window_hours)).timestamp())
                kalshi_params["max_close_ts"] = max_close_ts
            
            markets = self.kalshi.get_markets(**kalshi_params)
            
            for market in markets:
                yes_ask = market.get("yes_ask", 0) / 100 if market.get("yes_ask") else 0
                no_ask = market.get("no_ask", 0) / 100 if market.get("no_ask") else 0
                
                if yes_ask and no_ask:
                    total_cost = yes_ask + no_ask
                    
                    if total_cost < 1:
                        gross_profit = 1 - total_cost
                        kalshi_fee = gross_profit * 0.07  # 7% on profits
                        net_profit = gross_profit - kalshi_fee
                        profit_pct = (net_profit / total_cost) * 100
                        
                        if profit_pct >= self.min_profit_threshold * 100:
                            opportunities.append({
                                "type": "internal_arbitrage",
                                "platform": "kalshi",
                                "market": market.get("ticker", ""),
                                "title": market.get("title", ""),
                                "trade_details": {
                                    "buy_yes_at": yes_ask,
                                    "buy_no_at": no_ask,
                                    "position_size": 1.0
                                },
                                "yes_ask": yes_ask,
                                "no_ask": no_ask,
                                "total_cost": total_cost,
                                "gross_profit": gross_profit,
                                "fees": {
                                    "platform_fee": kalshi_fee,
                                    "gas_fee": 0,
                                    "total_fees": kalshi_fee
                                },
                                "net_profit": net_profit,
                                "profit_percentage": profit_pct,
                                "roi_percentage": (net_profit / total_cost) * 100,
                                "timestamp": datetime.now().isoformat()
                            })
        
        elif platform == "polymarket":
            markets = self.polymarket.get_simplified_markets(self.time_window_hours)
            
            for market in markets:
                yes_price = market.get("yes_price", 0)
                no_price = market.get("no_price", 0)
                
                if yes_price and no_price:
                    total_cost = yes_price + no_price
                    
                    if total_cost < 1:
                        gross_profit = 1 - total_cost
                        gas_fee = 0.02  # estimated gas in dollars
                        net_profit = gross_profit - gas_fee
                        profit_pct = (net_profit / total_cost) * 100
                        
                        if profit_pct >= self.min_profit_threshold * 100:
                            opportunities.append({
                                "type": "internal_arbitrage",
                                "platform": "polymarket",
                                "market": market.get("condition_id", ""),
                                "question": market.get("question", ""),
                                "trade_details": {
                                    "buy_yes_at": yes_price,
                                    "buy_no_at": no_price,
                                    "yes_token_id": market.get("yes_token_id", ""),
                                    "no_token_id": market.get("no_token_id", ""),
                                    "position_size": 1.0
                                },
                                "yes_price": yes_price,
                                "no_price": no_price,
                                "total_cost": total_cost,
                                "gross_profit": gross_profit,
                                "fees": {
                                    "platform_fee": 0,
                                    "gas_fee": gas_fee,
                                    "total_fees": gas_fee
                                },
                                "net_profit": net_profit,
                                "profit_percentage": profit_pct,
                                "roi_percentage": (net_profit / total_cost) * 100,
                                "timestamp": datetime.now().isoformat()
                            })
        
        return sorted(opportunities, key=lambda x: x["profit_percentage"], reverse=True)
    
    def scan_all_arbitrage(self) -> dict:
        """runs all arbitrage scans and returns consolidated results"""
        results = {
            "scan_time": datetime.now().isoformat(),
            "cross_platform": self.find_cross_platform_arbitrage(),
            "kalshi_internal": self.find_internal_arbitrage("kalshi"),
            "polymarket_internal": self.find_internal_arbitrage("polymarket")
        }
        
        total_opportunities = (
            len(results["cross_platform"]) +
            len(results["kalshi_internal"]) +
            len(results["polymarket_internal"])
        )
        
        results["summary"] = {
            "total_opportunities": total_opportunities,
            "cross_platform_count": len(results["cross_platform"]),
            "kalshi_internal_count": len(results["kalshi_internal"]),
            "polymarket_internal_count": len(results["polymarket_internal"])
        }
        
        return results