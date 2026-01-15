#!/usr/bin/env python3
"""
main python file - scans kalshi and polymarket for profitable betting opportunities
"""
import time
import json
from datetime import datetime
from kalshi_client import kalshiclient
from polymarket_client import polymarketclient
from arbitrage_scanner import arbitragescanner
from value_scanner import valuescanner

class betscanner:
    """orchestrates all scanning operations"""
    
    def __init__(self):
        print("initialising clients...")
        self.kalshi = kalshiclient()
        self.polymarket = polymarketclient()
        self.arb_scanner = arbitragescanner(self.kalshi, self.polymarket)
        self.value_scanner = valuescanner(self.kalshi, self.polymarket)
        print("clients ready\n")
    
    def run_single_scan(self, scan_type: str = "all") -> dict:
        """runs a single scan across all strategies"""
        print(f"Starting scan at {datetime.now().strftime('%h:%m:%s')}")
        print("-" * 60)
        
        results = {
            "scan_time": datetime.now().isoformat(),
            "scan_type": scan_type
        }
        
        if scan_type in ["all", "arbitrage"]:
            print("Scanning for arbitrage opportunities..")
            arb_results = self.arb_scanner.scan_all_arbitrage()
            results["arbitrage"] = arb_results
            self._print_arbitrage_summary(arb_results)
        
        if scan_type in ["all", "value"]:
            print("\nScanning for value opportunities..")
            value_results = self.value_scanner.scan_all_value()
            results["value"] = value_results
            self._print_value_summary(value_results)
        
        return results
    
    def run_continuous_scan(self, interval: int = 60, scan_type: str = "all"):
        """runs continuous scanning at specified interval (seconds)"""
        print(f"Starting continuous scan (interval: {interval}s)")
        print(f"Scan type: {scan_type}")
        print("Press ctrl+C to stop\n")
        
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                print(f"Scan #{scan_count}")
                
                results = self.run_single_scan(scan_type)
                
                # save results to file
                filename = f"scan_results_{datetime.now().strftime('%y%m%d_%h%m%s')}.json"
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\nresults saved to {filename}")
                
                print(f"\nwaiting {interval}s until next scan...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n✗ scan terminated by user")
            print(f"completed {scan_count} scans before exit")
    
    def _print_arbitrage_summary(self, results: dict):
        """prints formatted arbitrage results"""
        summary = results.get("summary", {})
        
        print(f"\narbitrage scan complete:")
        print(f"  total opportunities: {summary.get('total_opportunities', 0)}")
        print(f"  cross-platform: {summary.get('cross_platform_count', 0)}")
        print(f"  kalshi internal: {summary.get('kalshi_internal_count', 0)}")
        print(f"  polymarket internal: {summary.get('polymarket_internal_count', 0)}")
        
        # show top opportunities
        all_opps = []
        all_opps.extend(results.get("cross_platform", []))
        all_opps.extend(results.get("kalshi_internal", []))
        all_opps.extend(results.get("polymarket_internal", []))
        
        if all_opps:
            print("\ntop 3 arbitrage opportunities:")
            for i, opp in enumerate(all_opps[:3], 1):
                profit = opp.get("profit_percentage", 0)
                opp_type = opp.get("type", "")
                if opp_type == "cross_platform_arbitrage":
                    print(f"  {i}. cross-platform: {profit:.2f}% profit")
                    print(f"     kalshi: {opp.get('kalshi_title', '')[:50]}")
                    print(f"     polymarket: {opp.get('polymarket_question', '')[:50]}")
                else:
                    platform = opp.get("platform", "")
                    title = opp.get("title", opp.get("question", ""))
                    print(f"  {i}. {platform} internal: {profit:.2f}% profit")
                    print(f"     {title[:60]}")
    
    def _print_value_summary(self, results: dict):
        """prints formatted value betting results"""
        summary = results.get("summary", {})
        
        print(f"\nvalue scan complete:")
        print(f"  total value opportunities: {summary.get('total_value_opportunities', 0)}")
        print(f"  extreme probabilities: {summary.get('total_extreme_probabilities', 0)}")
        print(f"  liquid value bets: {summary.get('total_liquid_value', 0)}")
        
        # show top value opportunities
        all_value = []
        all_value.extend(results.get("kalshi_value", []))
        all_value.extend(results.get("polymarket_value", []))
        
        if all_value:
            print("\ntop 3 value opportunities:")
            for i, opp in enumerate(all_value[:3], 1):
                edge = opp.get("edge_percentage", 0)
                platform = opp.get("platform", "")
                title = opp.get("title", opp.get("question", ""))
                side = opp.get("side", "")
                price = opp.get("price", 0)
                print(f"  {i}. {platform} - {edge:.2f}% edge on {side}")
                print(f"     {title[:60]}")
                print(f"     price: {price:.3f}")

def main():
    """entry point"""
    scanner = betscanner()
    
    # run single scan by default
    # uncomment below to run continuous scanning
    scanner.run_single_scan(scan_type="all")
    
    # for continuous scanning:
    # scanner.run_continuous_scan(interval=60, scan_type="all")

if __name__ == "__main__":
    main()