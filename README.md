# Options Strategy Analyzer

A tool for analyzing and visualizing profit/loss scenarios for different options strategies, featuring both a Python CLI and a modern Next.js web interface.

## Features

- Fetch options chains for any ticker symbol using Yahoo Finance API
- Support for multiple strategies:
  - Long Calls
  - Long Puts
  - Covered Calls
  - Cash-Secured Puts
- Interactive selection of expiration dates and strikes
- Visual profit/loss analysis
- Filter options by investment amount and expected price
- Calculate annualized returns based on target prices

## Architecture

This project consists of two main components:

### 1. Python Backend

A standalone command-line tool that can be used independently to analyze options strategies.

### 2. Next.js Frontend (New!)

A modern web interface built with Next.js that provides a user-friendly way to interact with the options analyzer.

## Installation

### Option 1: Python CLI Only

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

### Option 2: Full Stack (Python + Next.js)

1. Clone this repository
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install Node.js dependencies:
   ```
   cd frontend
   npm install
   ```

## Usage

### Python CLI

Run the script:
```
python options_analyzer.py
```

Follow the interactive prompts to:
1. Enter a ticker symbol
2. Select an expiration date
3. Choose a strategy
4. Enter investment amount and expected price
5. View filtered options and analysis

### Next.js Web Interface

Start the development server:
```
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser and follow the intuitive interface to:
1. Enter a ticker symbol
2. Select an expiration date 
3. Choose a strategy
4. Enter investment details
5. View filtered options ranked by expected return
6. Select an option to see detailed analysis

## Example (CLI)

```
Options Strategy Analyzer
------------------------
Enter ticker symbol: AAPL
Current price for AAPL: $191.52

Available expiration dates:
1. 2024-06-21
2. 2024-06-28
...

Select expiration date (number): 1
Selected expiration: 2024-06-21

Available strategies:
1. call
2. put
3. covered_call
4. cash_secured_put

Select strategy (number): 3
Selected strategy: covered_call

Available call strike prices:
1. 180.0
2. 185.0
...

Select call strike price (number): 5
```

A matplotlib chart will display showing the P&L profile for the selected strategy. 

## Technologies

- **Backend**: Python, yfinance, pandas, matplotlib
- **Frontend**: Next.js, React, Tailwind CSS
- **API**: REST endpoints connecting the frontend to the Python backend

## License

MIT 