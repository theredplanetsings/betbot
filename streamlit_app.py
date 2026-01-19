#!/usr/bin/env python3
"""
streamlit interface for betbot scanner
"""

import streamlit as st
import pandas as pd
import time
import json
from datetime import datetime
from kalshi_client import kalshiclient
from polymarket_client import polymarketclient
from arbitrage_scanner import arbitragescanner
from value_scanner import valuescanner

st.set_page_config(
    page_title="betbot scanner",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
    .profit-high { color: #00ff00; font-weight: bold; }
    .profit-med { color: #ffaa00; font-weight: bold; }
    .profit-low { color: #ff6600; font-weight: bold; }
    .stMetric { background-color: #1e1e1e; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_clients():
    """initialise api clients (cached)"""
    kalshi = kalshiclient()
    polymarket = polymarketclient()
    arb_scanner = arbitragescanner(kalshi, polymarket)
    value_scanner = valuescanner(kalshi, polymarket)
    return kalshi, polymarket, arb_scanner, value_scanner

def format_profit_color(profit_pct):
    """return color class based on profit percentage"""
    if profit_pct >= 10:
        return "profit-high"
    elif profit_pct >= 5:
        return "profit-med"
    else:
        return "profit-low"

def display_arbitrage_opportunities(opportunities):
    """display arbitrage opportunities in table format"""
    if not opportunities:
        st.info("no arbitrage opportunities found")
        return None
    
    data = []
    for opp in opportunities:
        opp_type = opp.get("type", "")
        fees = opp.get("fees", {})
        
        if opp_type == "cross_platform_arbitrage":
            trade_details = opp.get("trade_details", {})
            data.append({
                "type": "cross-platform",
                "market": f"{opp.get('kalshi_title', '')[:40]}",
                "strategy": opp.get("strategy", ""),
                "total cost": f"${opp.get('total_cost', 0):.3f}",
                "gross profit": f"${opp.get('gross_profit', 0):.3f}",
                "total fees": f"${fees.get('total_fees', 0):.3f}",
                "net profit": f"${opp.get('net_profit', 0):.3f}",
                "roi %": f"{opp.get('roi_percentage', 0):.2f}%",
                "kalshi market": opp.get("kalshi_market", ""),
                "polymarket id": opp.get("polymarket_market", "")
            })
        else:
            platform = opp.get("platform", "")
            title = opp.get("title", opp.get("question", ""))
            data.append({
                "type": f"{platform} internal",
                "market": f"{title[:40]}",
                "yes price": f"${opp.get('yes_ask', opp.get('yes_price', 0)):.3f}",
                "no price": f"${opp.get('no_ask', opp.get('no_price', 0)):.3f}",
                "total cost": f"${opp.get('total_cost', 0):.3f}",
                "gross profit": f"${opp.get('gross_profit', 0):.3f}",
                "total fees": f"${fees.get('total_fees', 0):.3f}",
                "net profit": f"${opp.get('net_profit', 0):.3f}",
                "roi %": f"{opp.get('roi_percentage', 0):.2f}%",
                "market id": opp.get("market", "")
            })
    
    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch', hide_index=True)
    return df


def display_value_opportunities(opportunities):
    """display value betting opportunities in table format"""
    if not opportunities:
        st.info("no value opportunities found")
        return None
    
    data = []
    for opp in opportunities:
        title = opp.get("title", opp.get("question", ""))
        fees = opp.get("fees", {})
        trade_details = opp.get("trade_details", {})
        
        data.append({
            "platform": opp.get("platform", ""),
            "market": f"{title[:40]}",
            "side": opp.get("side", ""),
            "entry price": f"${opp.get('price', 0):.3f}",
            "fair value": f"${opp.get('fair_value', 0):.3f}",
            "edge %": f"{opp.get('edge_percentage', 0):.2f}%",
            "expected profit": f"${opp.get('expected_profit', 0):.3f}",
            "total fees": f"${fees.get('total_fees', 0):.3f}",
            "net profit": f"${opp.get('net_expected_profit', 0):.3f}",
            "roi %": f"{opp.get('roi_percentage', 0):.2f}%",
            "volume": f"{opp.get('volume', 0):,.0f}",
            "market id": opp.get("market", "")
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch', hide_index=True)
    return df


def display_extreme_probabilities(opportunities):
    """display extreme probability markets"""
    if not opportunities:
        st.info("no extreme probability markets found")
        return
    
    data = []
    for opp in opportunities:
        title = opp.get("title", opp.get("question", ""))
        data.append({
            "platform": opp.get("platform", ""),
            "market": f"{title[:50]}...",
            "yes price": f"${opp.get('yes_price', 0):.3f}",
            "confidence": opp.get("confidence", ""),
            "volume": f"{opp.get('volume', 0):,.0f}"
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, width='stretch', hide_index=True)

def main():
    st.title("Betbot")
    st.markdown("Real-time profit scanning for Kalshi and Polymarket")
    with st.sidebar:
        st.header("Scan Settings")
        
        scan_type = st.selectbox(
            "Scan Type",
            ["all", "arbitrage", "value"],
            index=0
        )
        
        # time window filter
        st.subheader("Time window")
        time_window_option = st.selectbox(
            "filter markets closing within:",
            ["all markets", "1 hour", "30 minutes", "15 minutes", "5 minutes", "1 minute"],
            index=0
        )
        
        # convert to hours for api
        time_window_map = {
            "all markets": None,
            "1 hour": 1.0,
            "30 minutes": 0.5,
            "15 minutes": 0.25,
            "5 minutes": 0.083,
            "1 minute": 0.017
        }
        time_window_hours = time_window_map[time_window_option]
        
        st.divider()
        
        auto_refresh = st.checkbox("auto refresh", value=False)
        refresh_interval = st.slider(
            "refresh interval (seconds)",
            min_value=30,
            max_value=300,
            value=60,
            step=10
        )
        
        if st.button("run scan now", type="primary"):
            st.session_state.trigger_scan = True
        
        st.divider()
        st.markdown("### about")
        st.markdown("scans kalshi and polymarket for:")
        st.markdown("- arbitrage opportunities")
        st.markdown("- value bets")
        st.markdown("- Extreme probabilities")
    
    # initialise clients
    with st.spinner("initialising clients..."):
        kalshi, polymarket, arb_scanner, value_scanner = init_clients()
    
    # set time window for scanners
    arb_scanner.set_time_window(time_window_hours)
    value_scanner.set_time_window(time_window_hours)
    
    # initialize session state for auto-refresh
    if "last_scan_time" not in st.session_state:
        st.session_state.last_scan_time = None
    
    # auto-refresh logic
    if auto_refresh:
        current_time = time.time()
        
        # run the scan if it's the first time/enough time has passed
        if (st.session_state.last_scan_time is None or 
            current_time - st.session_state.last_scan_time >= refresh_interval):
            
            st.session_state.last_scan_time = current_time
            run_scan_display(scan_type, arb_scanner, value_scanner, st.container(), time_window_option)
            
            # triggers a rerun after interval
            time.sleep(refresh_interval)
            st.rerun()
        else:
            # show previous results and countdown
            time_until_next = refresh_interval - (current_time - st.session_state.last_scan_time)
            st.info(f"Next scan in {int(time_until_next)} seconds..")
            time.sleep(1)
            st.rerun()
    else:
        # manual scan mode
        st.session_state.last_scan_time = None  # reset when auto-refresh is off
        
        if st.session_state.get("trigger_scan", False):
            st.session_state.trigger_scan = False
            run_scan_display(scan_type, arb_scanner, value_scanner, st.container(), time_window_option)
        else:
            st.info("Click 'run scan now' to start scanning")


def run_scan_display(scan_type, arb_scanner, value_scanner, container, time_window_label="all markets"):
    """run scan and display results"""
    with container:
        scan_time = datetime.now().strftime("%H:%M:%S")
        st.subheader(f"Scan results - {scan_time}")
        st.caption(f"Filtering: {time_window_label}")
    
        col1, col2, col3, col4 = st.columns(4)
        results = {}
        
        # run scans based on type
        if scan_type in ["all", "arbitrage"]:
            with st.spinner("Scanning for arbitrage.."):
                arb_results = arb_scanner.scan_all_arbitrage()
                results["arbitrage"] = arb_results
                
                total_arb = arb_results["summary"]["total_opportunities"]
                col1.metric("arbitrage opps", total_arb)
                col2.metric("cross-platform", arb_results["summary"]["cross_platform_count"])
        
        if scan_type in ["all", "value"]:
            with st.spinner("Scanning for value.."):
                value_results = value_scanner.scan_all_value()
                results["value"] = value_results
                
                total_value = value_results["summary"]["total_value_opportunities"]
                col3.metric("value opps", total_value)
                col4.metric("high liquidity", value_results["summary"]["total_liquid_value"])
        st.divider()
        
        # csv download section
        download_col1, download_col2 = st.columns(2)
        
        if scan_type in ["all", "arbitrage"] and results.get("arbitrage"):
            arb_results = results["arbitrage"]
            
            # combine all arbitrage opportunities
            all_arb = []
            all_arb.extend(arb_results.get("cross_platform", []))
            all_arb.extend(arb_results.get("Kalshi_internal", []))
            all_arb.extend(arb_results.get("Polymarket_internal", []))
            
            if all_arb:
                st.subheader("Arbitrage opportunities")
                arb_df = display_arbitrage_opportunities(all_arb[:10])  # top 10
                
                # download button for arbitrage data
                if arb_df is not None:
                    with download_col1:
                        csv = arb_df.to_csv(index=False)
                        st.download_button(
                            label="Download arbitrage csv",
                            data=csv,
                            file_name=f"arbitrage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # also offer full json download
                    json_data = json.dumps(all_arb, indent=2)
                    st.download_button(
                        label="Download full arbitrage json",
                        data=json_data,
                        file_name=f"arbitrage_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
        if scan_type in ["all", "value"] and results.get("value"):
            value_results = results["value"]
            
            # value opportunities
            all_value = []
            all_value.extend(value_results.get("kalshi_value", []))
            all_value.extend(value_results.get("polymarket_value", []))
            
            if all_value:
                st.subheader("Value opportunities")
                value_df = display_value_opportunities(all_value[:10])  # top 10
                
                # download button for value data
                if value_df is not None:
                    with download_col2:
                        csv = value_df.to_csv(index=False)
                        st.download_button(
                            label="Download value csv",
                            data=csv,
                            file_name=f"value_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    # also offer full json download
                    json_data = json.dumps(all_value, indent=2)
                    st.download_button(
                        label="Download full value json",
                        data=json_data,
                        file_name=f"value_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            
            # extreme probabilities
            all_extreme = []
            all_extreme.extend(value_results.get("kalshi_extremes", []))
            all_extreme.extend(value_results.get("polymarket_extremes", []))
            
            if all_extreme:
                st.subheader("extreme probabilities")
                with st.expander("show extreme probability markets"):
                    display_extreme_probabilities(all_extreme[:10])
        
        st.caption(f"last updated: {scan_time}")

if __name__ == "__main__":
    main()