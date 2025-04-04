#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, date
import sys
from tabulate import tabulate

def get_ticker_data(ticker_symbol):
    """Fetch ticker data from Yahoo Finance"""
    print(f"\n📊 Fetching data for {ticker_symbol}...")
    try:
        ticker = yf.Ticker(ticker_symbol)
        return ticker
    except Exception as e:
        print(f"❌ Error fetching data for {ticker_symbol}: {e}")
        return None

def get_options_chain(ticker):
    """Get available expiration dates and options chains"""
    print("\n📅 Retrieving available options expiration dates...")
    try:
        expirations = ticker.options
        if not expirations:
            print(f"❌ No options available for {ticker.ticker}")
            return None, None
        print(f"✅ Found {len(expirations)} expiration dates.")
        return expirations, ticker
    except Exception as e:
        print(f"❌ Error getting options chain: {e}")
        return None, None

def select_expiration(expirations):
    """Let user select an expiration date or enter a target date"""
    print("\n📅 Available expiration dates:")
    print("┌─────┬────────────┐")
    print("│ Num │ Date       │")
    print("├─────┼────────────┤")
    for i, exp in enumerate(expirations):
        print(f"│ {i+1:<3} │ {exp:<10} │")
    print("└─────┴────────────┘")
    
    print("\nYou can either:")
    print("1️⃣ Enter a number to select from the list above")
    print("2️⃣ Enter a date in YYYY-MM-DD format to find the closest expiration date")
    
    while True:
        choice = input("\n➡️ Enter selection (number or date): ")
        
        # Check if input is a number (option from the list)
        try:
            index = int(choice) - 1
            if 0 <= index < len(expirations):
                print(f"✅ Selected expiration: {expirations[index]}")
                return expirations[index]
            else:
                print("❌ Invalid selection. Please try again.")
        except ValueError:
            # Not a number, try to parse as date
            try:
                target_date = datetime.strptime(choice, '%Y-%m-%d').date()
                # Convert all expiration strings to date objects
                exp_dates = [datetime.strptime(exp, '%Y-%m-%d').date() for exp in expirations]
                
                # Find closest date using absolute difference
                closest_index = min(range(len(exp_dates)), key=lambda i: abs((exp_dates[i] - target_date).days))
                closest_date = expirations[closest_index]
                
                days_diff = abs((exp_dates[closest_index] - target_date).days)
                if days_diff == 0:
                    print(f"✅ Found exact match: {closest_date}")
                else:
                    print(f"✅ Closest expiration to {choice} is {closest_date} ({days_diff} days difference)")
                    
                return closest_date
            except ValueError:
                print("❌ Invalid format. Please enter a number or date in YYYY-MM-DD format.")

def get_options_for_expiration(ticker, expiration):
    """Get calls and puts for a specific expiration date"""
    print(f"\n🔍 Fetching options chain for {expiration}...")
    try:
        options = ticker.option_chain(expiration)
        calls = options.calls
        puts = options.puts
        print(f"✅ Found {len(calls)} call options and {len(puts)} put options.")
        return calls, puts
    except Exception as e:
        print(f"❌ Error getting options for {expiration}: {e}")
        return None, None

def parse_float(input_str):
    """More lenient float parsing that handles various formats"""
    try:
        # First try direct conversion
        return float(input_str)
    except ValueError:
        # Try removing common non-numeric characters
        cleaned = input_str.strip().replace('$', '').replace(',', '')
        try:
            return float(cleaned)
        except ValueError:
            # If still fails, raise exception
            raise ValueError(f"Cannot convert '{input_str}' to a number")

def filter_options_by_investment(options, strategy, investment_amount, stock_price=None, target_breakeven=None):
    """Filter options based on investment amount and target breakeven price"""
    filtered_options = []
    
    for _, option in options.iterrows():
        strike = option['strike']
        premium = option['lastPrice']
        
        # Calculate cost and breakeven
        if strategy == 'call':
            contract_cost = premium * 100  # One contract = 100 shares
            breakeven = strike + premium
            # For calls, we want strike + premium < target_breakeven
            meets_breakeven_criteria = True if target_breakeven is None else breakeven < target_breakeven
        elif strategy == 'put':
            contract_cost = premium * 100
            breakeven = strike - premium
            # For puts, we want strike - premium > target_breakeven
            meets_breakeven_criteria = True if target_breakeven is None else breakeven > target_breakeven
        elif strategy == 'covered_call':
            # Cost of 100 shares + premium received
            contract_cost = (stock_price * 100) - (premium * 100)
            breakeven = stock_price - premium
            # For covered calls, we want stock_price - premium < target_breakeven
            meets_breakeven_criteria = True if target_breakeven is None else breakeven < target_breakeven
        elif strategy == 'cash_secured_put':
            # Cash to secure 100 shares at strike price - premium received
            contract_cost = (strike * 100) - (premium * 100)
            breakeven = strike - premium
            # For cash secured puts, we want strike - premium > target_breakeven
            meets_breakeven_criteria = True if target_breakeven is None else breakeven > target_breakeven
        
        # Check if the option meets both investment and breakeven criteria
        if contract_cost <= investment_amount and meets_breakeven_criteria:
            filtered_options.append({
                'strike': strike,
                'premium': premium,
                'breakeven': breakeven,
                'cost': contract_cost,
                'remaining_budget': investment_amount - contract_cost,
                'option_data': option
            })
    
    # Sort by strike price
    filtered_options.sort(key=lambda x: x['strike'])
    return filtered_options

def display_filtered_options(filtered_options, strategy):
    """Display filtered options in a readable format using tabulate library"""
    if not filtered_options:
        print("\n❌ No options match your criteria.")
        return
    
    print(f"\n✅ Found {len(filtered_options)} options matching your criteria:")
    
    # Create a list to hold table data
    table_data = []
    
    # Add headers based on strategy
    if strategy in ['call', 'put']:
        headers = ["Num", "Strike Price", "Premium", "Breakeven", "Cost/Contract", "Remaining Budget", "Volume", "Open Int"]
        
        # Add data rows
        for i, opt in enumerate(filtered_options):
            volume = opt['option_data'].get('volume', 'N/A')
            open_int = opt['option_data'].get('openInterest', 'N/A')
            
            row = [
                i+1,
                f"${opt['strike']:.2f}",
                f"${opt['premium']:.2f}",
                f"${opt['breakeven']:.2f}",
                f"${opt['cost']:.2f}",
                f"${opt['remaining_budget']:.2f}",
                volume,
                open_int
            ]
            table_data.append(row)
    else:  # covered_call or cash_secured_put
        headers = ["Num", "Strike Price", "Premium", "Breakeven", "Required Capital", "Return %", "Volume", "Open Int"]
        
        # Add data rows
        for i, opt in enumerate(filtered_options):
            volume = opt['option_data'].get('volume', 'N/A')
            open_int = opt['option_data'].get('openInterest', 'N/A')
            
            if strategy == 'covered_call':
                return_pct = (opt['premium'] / (opt['strike'] - opt['premium'])) * 100
            else:  # cash_secured_put
                return_pct = (opt['premium'] / opt['strike']) * 100
                
            row = [
                i+1,
                f"${opt['strike']:.2f}",
                f"${opt['premium']:.2f}",
                f"${opt['breakeven']:.2f}",
                f"${opt['cost']:.2f}",
                f"{return_pct:.2f}%",
                volume,
                open_int
            ]
            table_data.append(row)
    
    # Create and display table using tabulate with grid format
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

def calculate_pnl(strategy, stock_price, selected_data):
    """Calculate P&L for different strategies across a range of prices"""
    print("\n📊 Strategy Analysis")
    print("═══════════════════")
    
    # Get current stock price if not provided
    if stock_price is None:
        stock_price = selected_data.get('stock_price', 100)  # Default to 100 if unknown
    
    if strategy == 'call':
        # Long call: max loss is premium, profit is unlimited
        strike = selected_data['call_strike']
        premium = selected_data['call_option']['lastPrice']
        print(f"\n📈 Strategy Summary - Long Call:")
        print(f"   Strike Price: ${strike}")
        print(f"   Premium Paid: ${premium:.2f}")
        print(f"   Breakeven Price: ${strike + premium:.2f}")
        print(f"   Maximum Loss: ${premium:.2f} (if stock price is below ${strike} at expiration)")
        print(f"   Maximum Profit: Unlimited (increases as stock price rises above breakeven)")
            
    elif strategy == 'put':
        # Long put: max loss is premium, profit is limited by strike
        strike = selected_data['put_strike']
        premium = selected_data['put_option']['lastPrice']
        print(f"\n📉 Strategy Summary - Long Put:")
        print(f"   Strike Price: ${strike}")
        print(f"   Premium Paid: ${premium:.2f}")
        print(f"   Breakeven Price: ${strike - premium:.2f}")
        print(f"   Maximum Loss: ${premium:.2f} (if stock price is above ${strike} at expiration)")
        print(f"   Maximum Profit: ${strike - premium:.2f} (if stock price goes to $0)")
            
    elif strategy == 'covered_call':
        # Covered call: own 100 shares and sell 1 call option
        strike = selected_data['call_strike']
        premium = selected_data['call_option']['lastPrice']
        print(f"\n📊 Strategy Summary - Covered Call:")
        print(f"   Current Stock Price: ${stock_price:.2f}")
        print(f"   Strike Price: ${strike}")
        print(f"   Premium Received: ${premium:.2f}")
        print(f"   Maximum Profit: ${(strike - stock_price + premium):.2f} (if stock price is at or above ${strike} at expiration)")
        print(f"   Breakeven Price: ${stock_price - premium:.2f}")
            
    elif strategy == 'cash_secured_put':
        # Cash secured put: sell 1 put option
        strike = selected_data['put_strike']
        premium = selected_data['put_option']['lastPrice']
        print(f"\n💰 Strategy Summary - Cash Secured Put:")
        print(f"   Strike Price: ${strike}")
        print(f"   Premium Received: ${premium:.2f}")
        print(f"   Maximum Profit: ${premium:.2f} (if stock price is at or above ${strike} at expiration)")
        print(f"   Breakeven Price: ${strike - premium:.2f}")
        print(f"   Maximum Loss: ${strike - premium:.2f} (if stock price goes to $0)")

def display_welcome():
    """Display welcome message and explanation"""
    print("\n" + "═" * 70)
    print("                   OPTIONS STRATEGY ANALYZER")
    print("═" * 70)
    print("\n📱 This tool helps you analyze options strategies and find contracts")
    print("   that match your investment criteria.")
    print("\n📊 Supported strategies:")
    print("   c:   Call          - Buy call options")
    print("   p:   Put           - Buy put options")
    print("   cc:  Covered Call  - Own stock and sell call options")
    print("   csp: Cash Secured Put - Sell put options with cash as collateral")
    print("\n🔍 The tool will guide you through the following steps:")
    print("   1. Enter a stock ticker symbol")
    print("   2. Select an options expiration date")
    print("   3. Choose a strategy")
    print("   4. Enter investment amount")
    print("   5. Optionally filter by specific strike price")
    print("   6. View matching options and analysis")
    print("\n🚀 Let's get started!")
    print("─" * 70)

def explain_target_strike():
    """Explain what target breakeven price means for filtering options"""
    print("\n📝 About Target Breakeven Price:")
    print("   You can filter options to show those that will be profitable")
    print("   at your expected stock price.")
    print("\n   For CALLS and COVERED CALLS: Shows options with breakeven BELOW your target.")
    print("   For PUTS and CASH SECURED PUTS: Shows options with breakeven ABOVE your target.")
    print("\n   If you leave this blank, all options that fit your investment budget will be shown.")

def calculate_option_value(strategy, future_price, selected_data, expiration_date):
    """Calculate option value at a specific future price"""
    strike = None
    premium = None
    current_price = selected_data.get('stock_price')
    
    # Get days until expiration
    exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
    today = date.today()
    days_to_expiration = (exp_date - today).days
    if days_to_expiration <= 0:
        days_to_expiration = 1  # Avoid division by zero
    
    if strategy == 'call':
        strike = selected_data['call_strike']
        premium = selected_data['call_option']['lastPrice']
        # Calculate intrinsic value at expiration
        if future_price > strike:
            value = future_price - strike
        else:
            value = 0
        
        # Calculate dollar profit/loss
        profit = value - premium
        
        # Calculate percentage return
        if premium > 0:
            percent_return = (profit / premium) * 100
        else:
            percent_return = 0
            
        # Calculate annualized return
        annualized_return = ((1 + (percent_return / 100)) ** (365 / days_to_expiration) - 1) * 100
        
    elif strategy == 'put':
        strike = selected_data['put_strike']
        premium = selected_data['put_option']['lastPrice']
        # Calculate intrinsic value at expiration
        if future_price < strike:
            value = strike - future_price
        else:
            value = 0
            
        # Calculate dollar profit/loss
        profit = value - premium
        
        # Calculate percentage return
        if premium > 0:
            percent_return = (profit / premium) * 100
        else:
            percent_return = 0
            
        # Calculate annualized return
        annualized_return = ((1 + (percent_return / 100)) ** (365 / days_to_expiration) - 1) * 100
        
    elif strategy == 'covered_call':
        strike = selected_data['call_strike']
        premium = selected_data['call_option']['lastPrice']
        # Stock P&L + option premium
        stock_profit = future_price - current_price
        
        if future_price > strike:
            option_value = -(future_price - strike)  # Loss on the short call
        else:
            option_value = 0  # Option expires worthless
            
        profit = stock_profit + premium + option_value
        
        # Calculate percentage return on investment
        investment = current_price  # Cost of 100 shares (simplified)
        percent_return = (profit / investment) * 100
        
        # Calculate annualized return
        annualized_return = ((1 + (percent_return / 100)) ** (365 / days_to_expiration) - 1) * 100
        
    elif strategy == 'cash_secured_put':
        strike = selected_data['put_strike']
        premium = selected_data['put_option']['lastPrice']
        
        if future_price < strike:
            option_value = -(strike - future_price)  # Loss on the short put
        else:
            option_value = 0  # Option expires worthless
            
        profit = premium + option_value
        
        # Calculate percentage return on investment (cash secured = strike price)
        investment = strike  # Amount of cash secured
        percent_return = (profit / investment) * 100
        
        # Calculate annualized return
        annualized_return = ((1 + (percent_return / 100)) ** (365 / days_to_expiration) - 1) * 100
    
    return {
        'strategy': strategy,
        'days_to_expiration': days_to_expiration,
        'future_price': future_price,
        'strike': strike,
        'premium': premium,
        'value_at_expiration': value if 'value' in locals() else option_value,
        'profit': profit,
        'percent_return': percent_return,
        'annualized_return': annualized_return
    }

def display_future_results(results):
    """Display the results of future price analysis"""
    strategy_names = {
        'call': 'Long Call',
        'put': 'Long Put',
        'covered_call': 'Covered Call',
        'cash_secured_put': 'Cash-Secured Put'
    }
    
    print("\n" + "═" * 70)
    print(f"📊 ANALYSIS RESULTS FOR EXPECTED FUTURE PRICE: ${results['future_price']:.2f}")
    print("═" * 70)
    print(f"Strategy: {strategy_names.get(results['strategy'], results['strategy'])}")
    print(f"Days until expiration: {results['days_to_expiration']}")
    
    if results['strategy'] == 'call':
        print(f"\nCall Strike: ${results['strike']}")
        print(f"Premium Paid: ${results['premium']:.2f}")
        print(f"\nAt your expected price of ${results['future_price']:.2f}:")
        print(f"Option Value at Expiration: ${results['value_at_expiration']:.2f}")
        print(f"Profit/Loss: ${results['profit']:.2f}")
        print(f"Percentage Return: {results['percent_return']:.2f}%")
        print(f"Annualized Return: {results['annualized_return']:.2f}%")
        
    elif results['strategy'] == 'put':
        print(f"\nPut Strike: ${results['strike']}")
        print(f"Premium Paid: ${results['premium']:.2f}")
        print(f"\nAt your expected price of ${results['future_price']:.2f}:")
        print(f"Option Value at Expiration: ${results['value_at_expiration']:.2f}")
        print(f"Profit/Loss: ${results['profit']:.2f}")
        print(f"Percentage Return: {results['percent_return']:.2f}%")
        print(f"Annualized Return: {results['annualized_return']:.2f}%")
        
    elif results['strategy'] == 'covered_call':
        print(f"\nCurrent Stock Price: ${results.get('current_price', 'N/A')}")
        print(f"Call Strike: ${results['strike']}")
        print(f"Premium Received: ${results['premium']:.2f}")
        print(f"\nAt your expected price of ${results['future_price']:.2f}:")
        print(f"Profit/Loss: ${results['profit']:.2f}")
        print(f"Percentage Return: {results['percent_return']:.2f}%")
        print(f"Annualized Return: {results['annualized_return']:.2f}%")
        
    elif results['strategy'] == 'cash_secured_put':
        print(f"\nPut Strike: ${results['strike']}")
        print(f"Premium Received: ${results['premium']:.2f}")
        print(f"\nAt your expected price of ${results['future_price']:.2f}:")
        print(f"Profit/Loss: ${results['profit']:.2f}")
        print(f"Percentage Return: {results['percent_return']:.2f}%")
        print(f"Annualized Return: {results['annualized_return']:.2f}%")
    
    print("\nNote: These calculations assume holding until expiration.")
    print("═" * 70)

def calculate_annualized_returns(filtered_options, strategy, target_price, expiration_date):
    """Calculate annualized returns for all filtered options at the target price"""
    today = date.today()
    exp_date = datetime.strptime(expiration_date, '%Y-%m-%d').date()
    days_to_expiration = max(1, (exp_date - today).days)  # Ensure at least 1 day
    
    results = []
    for opt in filtered_options:
        strike = opt['strike']
        premium = opt['premium']
        
        # Calculate profit at target price based on strategy
        if strategy == 'call':
            if target_price > strike:
                option_value = target_price - strike
            else:
                option_value = 0
            profit = option_value - premium
            investment = premium
            
        elif strategy == 'put':
            if target_price < strike:
                option_value = strike - target_price
            else:
                option_value = 0
            profit = option_value - premium
            investment = premium
            
        elif strategy == 'covered_call':
            current_price = opt.get('stock_price', strike)  # Fallback to strike if stock price unknown
            stock_profit = target_price - current_price
            
            if target_price > strike:
                option_value = -(target_price - strike)  # Loss on short call
            else:
                option_value = 0
            profit = stock_profit + premium + option_value
            investment = current_price
            
        elif strategy == 'cash_secured_put':
            if target_price < strike:
                option_value = -(strike - target_price)  # Loss on short put
            else:
                option_value = 0
            profit = premium + option_value
            investment = strike
        
        # Calculate percentage and annualized returns
        if investment > 0:
            percent_return = (profit / investment) * 100
            annualized_return = ((1 + (percent_return / 100)) ** (365 / days_to_expiration) - 1) * 100
        else:
            percent_return = 0
            annualized_return = 0
        
        results.append({
            'strike': strike,
            'premium': premium,
            'breakeven': opt['breakeven'],
            'profit': profit,
            'percent_return': percent_return,
            'annualized_return': annualized_return,
            'option_data': opt['option_data']
        })
    
    # Sort by annualized return (highest first)
    results.sort(key=lambda x: x['annualized_return'], reverse=True)
    return results

def display_top_returns(options_by_return, strategy, target_price, limit=5):
    """Display the top options by annualized return using tabulate"""
    if not options_by_return:
        print("\n⚠️ Could not calculate returns for any options at your target price.")
        return
    
    print(f"\n🔝 Top options by annualized return if {target_price:.2f} is reached:")
    
    # Create table headers and data
    headers = ["Strike", "Premium", "Breakeven", "Profit", "Return %", "Annual Return"]
    table_data = []
    
    # Add top N options (or all if less than N)
    show_limit = min(limit, len(options_by_return))
    for i in range(show_limit):
        opt = options_by_return[i]
        
        row = [
            f"${opt['strike']:.2f}",
            f"${opt['premium']:.2f}",
            f"${opt['breakeven']:.2f}",
            f"${opt['profit']:.2f}",
            f"{opt['percent_return']:.2f}%",
            f"{opt['annualized_return']:.2f}%"
        ]
        table_data.append(row)
    
    # Display using tabulate with grid format
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Add explanation
    print("\n📝 These options would provide the highest annualized returns")
    print(f"   if the stock reaches ${target_price:.2f} by expiration.")
    print("   Annualized return assumes holding until expiration.")

def main():
    display_welcome()
    
    # Get ticker symbol from user
    ticker_symbol = input("\n📈 Enter ticker symbol: ").upper()
    
    # Get ticker data
    ticker = get_ticker_data(ticker_symbol)
    if not ticker:
        sys.exit(1)
    
    # Get current stock price
    try:
        stock_info = ticker.info
        stock_price = stock_info.get('regularMarketPrice', None)
        if stock_price:
            print(f"💲 Current price for {ticker_symbol}: ${stock_price:.2f}")
        else:
            print(f"⚠️ Could not get current price for {ticker_symbol}")
    except:
        stock_price = None
        print(f"⚠️ Could not get current price for {ticker_symbol}")
    
    # Get available expiration dates
    expirations, ticker = get_options_chain(ticker)
    if not expirations:
        sys.exit(1)
    
    # Let user select expiration date
    selected_expiration = select_expiration(expirations)
    print(f"📅 Selected expiration: {selected_expiration}")
    
    # Get options chain for selected expiration
    calls, puts = get_options_for_expiration(ticker, selected_expiration)
    if calls is None or puts is None:
        sys.exit(1)
    
    # Let user select strategy
    strategies = {
        'c': 'call',
        'p': 'put', 
        'cc': 'covered_call', 
        'csp': 'cash_secured_put'
    }
    
    strategy_descriptions = {
        'c': 'Buy a call option to profit from stock price increases',
        'p': 'Buy a put option to profit from stock price decreases',
        'cc': 'Own stock and sell a call option for income',
        'csp': 'Sell a put option with cash as collateral'
    }
    
    # Calculate width for each column with fixed width for description
    code_width = 6  # Width for the code column including padding
    desc_width = 52  # Width for the description column including padding
    
    print("\n📊 Available strategies:")
    print("┏" + "━" * code_width + "┳" + "━" * desc_width + "┓")
    print("┃ Code" + " " * (code_width - 5) + "┃ Description" + " " * (desc_width - 12) + "┃")
    print("┣" + "━" * code_width + "╋" + "━" * desc_width + "┫")
    
    for code, description in strategy_descriptions.items():
        # Truncate description if it's too long for the column
        if len(description) > desc_width - 2:  # -2 for padding
            description = description[:desc_width - 5] + "..."
        
        # Ensure consistent padding - left align code, left align description
        code_formatted = f" {code}" + " " * (code_width - len(code) - 1)
        desc_formatted = f" {description}" + " " * (desc_width - len(description) - 1)
        print(f"┃{code_formatted}┃{desc_formatted}┃")
    
    print("┗" + "━" * code_width + "┻" + "━" * desc_width + "┛")
    
    while True:
        strategy_choice = input("\n➡️ Select strategy (c/p/cc/csp): ").lower().strip()
        if strategy_choice in strategies:
            selected_strategy = strategies[strategy_choice]
            print(f"✅ Selected strategy: {selected_strategy}")
            break
        else:
            print("❌ Invalid selection. Please enter c, p, cc, or csp.")
    
    # Ask for investment amount with custom prompt based on strategy
    investment_amount = None
    while investment_amount is None:
        try:
            if selected_strategy == 'cash_secured_put':
                prompt = "\n💵 Enter the maximum collateral amount for this position ($): "
            elif selected_strategy == 'covered_call':
                prompt = "\n💵 Enter the maximum amount to spend on this position ($): "
            else:
                prompt = "\n💵 Enter the maximum amount you're willing to invest per contract ($): "
                
            amount_input = input(prompt)
            investment_amount = parse_float(amount_input)
            if investment_amount <= 0:
                print("❌ Amount must be greater than zero.")
                investment_amount = None
        except ValueError as e:
            print(f"❌ Error: {e}")
    
    # Get user's expected future price for return calculation - MOVED THIS PART EARLIER
    future_price = None
    while future_price is None:
        try:
            price_input = input(f"\n🔮 Enter your expected price for {ticker_symbol} at expiration: $")
            future_price = parse_float(price_input)
            if future_price <= 0:
                print("❌ Price must be greater than zero.")
                future_price = None
        except ValueError as e:
            print(f"❌ Error: {e}")
    
    # Filter options based on strategy and investment amount
    if selected_strategy == 'call':
        filtered_options = filter_options_by_investment(calls, selected_strategy, investment_amount, stock_price)
    elif selected_strategy == 'put':
        filtered_options = filter_options_by_investment(puts, selected_strategy, investment_amount, stock_price)
    elif selected_strategy == 'covered_call':
        if stock_price is None:
            print("❌ Error: Current stock price is required for covered call analysis but could not be retrieved.")
            sys.exit(1)
        filtered_options = filter_options_by_investment(calls, selected_strategy, investment_amount, stock_price)
    elif selected_strategy == 'cash_secured_put':
        filtered_options = filter_options_by_investment(puts, selected_strategy, investment_amount, stock_price)
    
    # Check if we found any options
    if not filtered_options:
        print("\n❌ No options match your criteria. Try adjusting your investment amount.")
        sys.exit(0)
    
    # Calculate returns based on expected price and sort by annualized return
    options_by_return = calculate_annualized_returns(filtered_options, selected_strategy, future_price, selected_expiration)
    
    # Display ALL options sorted by annualized return
    print(f"\n📊 Options sorted by highest annualized return if ${future_price:.2f} is reached:")
    
    # Create table headers and data for all options
    headers = ["Num", "Strike", "Premium", "Breakeven", "Profit", "Return %", "Annual Return", "Volume", "Open Int"]
    table_data = []
    
    for i, opt in enumerate(options_by_return):
        volume = opt['option_data'].get('volume', 'N/A')
        open_int = opt['option_data'].get('openInterest', 'N/A')
        
        row = [
            i+1,
            f"${opt['strike']:.2f}",
            f"${opt['premium']:.2f}",
            f"${opt['breakeven']:.2f}",
            f"${opt['profit']:.2f}",
            f"{opt['percent_return']:.2f}%",
            f"{opt['annualized_return']:.2f}%",
            volume,
            open_int
        ]
        table_data.append(row)
    
    # Display using tabulate
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    print("\n📝 These options are sorted by annualized return if the stock reaches")
    print(f"   ${future_price:.2f} by expiration. Higher returns may involve higher risks.")
    
    # Let user select from filtered options or exit
    option_choice = None
    while option_choice is None:
        try:
            choice_input = input("\n➡️ Select an option by number (1 to " + str(len(options_by_return)) + ") or 'q' to quit: ")
            if choice_input.lower() == 'q':
                print("👋 Exiting analysis.")
                sys.exit(0)
                
            choice_idx = int(choice_input) - 1
            if 0 <= choice_idx < len(options_by_return):
                option_choice = options_by_return[choice_idx]
            else:
                print(f"❌ Please enter a number between 1 and {len(options_by_return)}.")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q'.")
    
    # Prepare selected data for analysis
    selected_data = {'stock_price': stock_price}
    
    if selected_strategy in ['call', 'covered_call']:
        selected_data['call_strike'] = option_choice['strike']
        selected_data['call_option'] = option_choice['option_data']
    
    if selected_strategy in ['put', 'cash_secured_put']:
        selected_data['put_strike'] = option_choice['strike']
        selected_data['put_option'] = option_choice['option_data']
    
    # Display strategy analysis
    calculate_pnl(selected_strategy, stock_price, selected_data)
    
    # Calculate option value and returns at the expected price
    future_results = calculate_option_value(selected_strategy, future_price, selected_data, selected_expiration)
    
    # Display future price analysis
    display_future_results(future_results)

if __name__ == "__main__":
    main() 