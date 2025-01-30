import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from datetime import datetime
from datetime import timedelta
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import plotly.express as px
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
import matplotlib.style as style

st.set_page_config(layout="wide", page_title="InvinciBull")
st.title("InvinciBull")
tickerSymbol = st.text_input("Enter the stock symbol here...", value="AAPL", label_visibility="visible", placeholder="AAPL", max_chars=5).upper()
st.session_state.tickerSymbol = tickerSymbol
tickerData = yf.Ticker(tickerSymbol)
main_info = tickerData.fast_info
comp_info = tickerData.info
news = tickerData.news

# Home
def home_page():
    col1, col2, col3 = st.columns(3)

    # Column containing company name, hq, website, and employee count
    with col1:
        company_name = comp_info.get("shortName")
        st.subheader(company_name)
        # HQ & WEBSITE
        city = comp_info.get("city")
        state = comp_info.get("state")
        country = comp_info.get("country")
        website = comp_info.get("website")
        # Check and construct the address dynamically
        address_parts = [city, state, country]
        address = ", ".join(part for part in address_parts if part)  # Join non-empty parts
        # Display the address and website
        if website:
            # Remove "https://www." or "http://www." from the URL for display purposes
            clean_website = website.replace("https://www.", "").replace("http://www.", "").replace("https://", "").replace("http://", "")
            
            # Use a link symbol (🔗) with the cleaned website text
            st.write(address)
            st.markdown(f"[🔗 {clean_website}]({website})", unsafe_allow_html=True)
        else:
            st.write(address, "Website: Not available")
        FTE = comp_info.get("fullTimeEmployees")
        
        st.write("Employees:", f"{FTE:,}" if FTE else "No employee information available.")

    # Column containing price, shares, market cap, and enterprise value
    with col2:

        # Format price as $ with 2 decimals
        price = main_info.last_price
        st.write("Price:", f"${price:,.2f}")

        # Format shares in millions or billions
        shares = main_info.shares
        if shares >= 1_000_000_000:  # Billions
            st.write("Shares Out:", f"{shares / 1_000_000_000:.1f}B")
        elif shares >= 1_000_000:  # Millions
            st.write("Shares Out:", f"{shares / 1_000_000:.1f}M")
        else:  # Less than a million
            st.write("Shares Out:", f"{shares:,}")

        # Format market cap in $ with millions or billions
        market_cap = main_info.market_cap
        if market_cap >= 1_000_000_000:  # Billions
            st.write("Market Cap:", f"${market_cap / 1_000_000_000:.1f}B")
        elif market_cap >= 1_000_000:  # Millions
            st.write("Market Cap:", f"${market_cap / 1_000_000:.1f}M")
        else:  # Less than a million
            st.write("Market Cap:", f"${market_cap:,}")

        # Format EnterpriseValue in $ with millions or billions
        EV = comp_info.get("enterpriseValue")
        if EV >= 1_000_000_000:  # Billions
            st.write("Enterprise Value:", f"${EV / 1_000_000_000:.1f}B")
        elif EV >= 1_000_000:  # Millions
            st.write("Enterprise Value:", f"${EV / 1_000_000:.1f}M")
        else:  # Less than a million
            st.write("Enterprise Value:", f"${EV:,}")

    # Column containing performance
    with col3:
        def get_price_percentages(tickerData):
            # Get today's date
            today = datetime.now().date()
            # Define the start of the year
            start_of_year = datetime(today.year, 1, 1).date()
            
            # Define dates for 1 month, 6 months, and 1 year ago
            three_months_ago = today - timedelta(days=90)
            six_months_ago = today - timedelta(days=180)
            one_year_ago = today - timedelta(days=365)
            
            # Fetch historical data for the required periods
            data_3mo = tickerData.history(start=three_months_ago, end=today)
            data_6mo = tickerData.history(start=six_months_ago, end=today)
            data_ytd = tickerData.history(start=start_of_year, end=today)
            data_1yr = tickerData.history(start=one_year_ago, end=today)
            
            # Current price
            current_price = tickerData.history(period="1d")['Close'].iloc[0] if not tickerData.history(period="1d").empty else None
            
            # Calculate percentage changes
            performances = {}
            
            if current_price is not None:
                if not data_3mo.empty:
                    performances["3mo"] = ((current_price - data_3mo['Close'].iloc[0]) / data_3mo['Close'].iloc[0]) * 100
                else:
                    performances["3mo"] = None
                
                if not data_6mo.empty:
                    performances["6mo"] = ((current_price - data_6mo['Close'].iloc[0]) / data_6mo['Close'].iloc[0]) * 100
                else:
                    performances["6mo"] = None
                
                if not data_1yr.empty:
                    performances["1yr"] = ((current_price - data_1yr['Close'].iloc[0]) / data_1yr['Close'].iloc[0]) * 100
                else:
                    performances["1yr"] = None
                
                # YTD performance
                if not data_ytd.empty:
                    performances["ytd"] = ((current_price - data_ytd['Close'].iloc[0]) / data_ytd['Close'].iloc[0]) * 100
                else:
                    performances["ytd"] = None
            else:
                performances = {"3mo": None, "6mo": None, "YTD": None, "1yr": None}
            
            return performances

        percentages = get_price_percentages(tickerData)
        st.write(f"3mo: {'{:.2f}%'.format(percentages['3mo']) if percentages['3mo'] is not None else 'Not available'}")
        st.write(f"6mo: {'{:.2f}%'.format(percentages['6mo']) if percentages['6mo'] is not None else 'Not available'}")
        st.write(f"YTD: {'{:.2f}%'.format(percentages['ytd']) if percentages['ytd'] is not None else 'Not available'}")
        st.write(f"1yr: {'{:.2f}%'.format(percentages['1yr']) if percentages['1yr'] is not None else 'Not available'}")
        
    tradingview_widget = f"""
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container" style="height:100%;width:100%">
        <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
        <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
        {{
        "width": "1000",
        "height": "620",
        "symbol": "{tickerSymbol}",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "range": "12M",
        "hide_side_toolbar": false,
        "allow_symbol_change": false,
        "calendar": false,
        "hide_volume": true,
        "support_host": "https://www.tradingview.com"
        }}
        </script>
        </div>
        <!-- TradingView Widget END -->
        """
    # Render the TradingView widget
    st.components.v1.html(tradingview_widget, width=1000, height=620)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "About",
        "Holders",
        "SEC Filings",
        "News",
        "Ratings"
    ])
    with tab1:
        # Business Summary
        summary = comp_info.get("longBusinessSummary")

        if summary:
            st.write(summary)
        else:
            st.write("Business summary not available.")

        # OFFICERS & TITLES    
        c_level = comp_info.get("companyOfficers")
        if c_level:
            with st.expander("Officers"):
                for officer in c_level:
                    if 'name' in officer and 'title' in officer:
                        st.write(f"- **{officer['name']}**: {officer['title']}")
        else:
            st.write("No officers information available.")
    
    # Holders
    with tab2:
        holders = tickerData.major_holders
        # Plot the holders in a bar chart, but remove institutionsCount and make the y-axis a percentage value
        if not holders.empty:
            st.bar_chart(holders.drop("institutionsCount", axis=0))
        else:
            st.write("No holders information available.")

    # SEC Filings
    with tab3:
        def get_sec_filings(tickerSymbol):
            # Construct the SEC URL for the ticker symbol
            sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={tickerSymbol}&type=&dateb=&owner=include&start=0&count=40"
            headers = {'User-Agent': 'YourName (your.email@example.com)'}
    
            # Fetch the webpage
            response = requests.get(sec_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
    
            # Find the filings table
            table = soup.find('table', {'class': 'tableFile2'})
            rows = table.find_all('tr')
    
            # Extract data from the table rows
            filings_data = []
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) > 3:
                    filing_type = cols[0].text.strip()
                    description = cols[2].text.strip()
                    filing_date = cols[3].text.strip()
                    document_link = "https://www.sec.gov" + cols[1].find('a')['href']
    
                    filings_data.append({
                        'Filing Type': f'<a href="{document_link}" target="_blank">{filing_type}</a>',
                        'Description': description,
                        'Date': filing_date
                    })
    
            return filings_data
    
        if tickerSymbol:
            # Get SEC filings
            filings = get_sec_filings(tickerSymbol)
    
            # Convert to DataFrame
            df = pd.DataFrame(filings)
    
            # Display the DataFrame as a table with hyperlinks in Filing Type column
            st.write("Most Recent SEC Filings:")
            st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # News
    with tab4:
        news = tickerData.news
        
        if news:
            for article in news:
                # Extract the required fields
                # Assuming 'content' is the correct key for the nested dictionary
                content = article.get('content', {})
                
                title = content.get('title', 'No title available')
                summary = content.get('summary', 'No summary available')
                pub_date = content.get('pubDate', 'No publication date available')
                clickthrough_url = content.get('clickThroughUrl', 'URL not available')
                
                # Convert the publication date to a more readable format if it exists
                if pub_date != 'No publication date available':
                    pub_date_readable = datetime.strptime(pub_date, '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')
                else:
                    pub_date_readable = pub_date
                
                # Display the cleaned data in Streamlit
                st.write(f"**Title:** {title}")
                st.write(f"**Summary:** {summary}")
                st.write(f"**Date Published:** {pub_date_readable}")
                st.write(f"**Clickthrough URL:** [{clickthrough_url}]({clickthrough_url})")
                st.write("---")  # Adds a separator between articles
        else:
            st.write("No news articles found.")

    # Ratings
    with tab5:
        ratings = tickerData.recommendations
        # Create a bar chart

        # Set dark theme for matplotlib
        style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='none')

        # Number of periods
        num_periods = len(ratings)

        # Width of each bar
        bar_width = 0.15

        # Positions of the bars on the x-axis
        r1 = range(num_periods)
        r2 = [x + bar_width for x in r1]
        r3 = [x + 2*bar_width for x in r1]
        r4 = [x + 3*bar_width for x in r1]
        r5 = [x + 4*bar_width for x in r1]

        # Plotting each category
        ax.bar(r1, ratings['strongBuy'], color='green', width=bar_width, label='Strong Buy')
        ax.bar(r2, ratings['buy'], color='lightgreen', width=bar_width, label='Buy')
        ax.bar(r3, ratings['hold'], color='yellow', width=bar_width, label='Hold')
        ax.bar(r4, ratings['sell'], color='orange', width=bar_width, label='Sell')
        ax.bar(r5, ratings['strongSell'], color='red', width=bar_width, label='Strong Sell')

        # Customizing the plot
        ax.set_ylabel('Number of Recommendations')
        ax.set_xlabel('Time Period')
        ax.set_title('Analyst Recommendations')
        ax.set_xticks([r + bar_width*2 for r in range(num_periods)])
        ax.set_xticklabels(ratings['period'])
        ax.legend()

        # Display the plot in Streamlit
        st.pyplot(fig)


# Options
def options_page():
    tickerSymbol = st.session_state.tickerSymbol
    if tickerSymbol:
        tickerData = yf.Ticker(tickerSymbol)
        options = tickerData.option_chain()
        
        if options.calls is not None and options.puts is not None:
            st.write(f"Options for {tickerSymbol}")
            
            # Option to switch between DataFrame view and visualizations
            view_type = st.radio("Choose View Type", ["DataFrames", "Visualizations"])
            
            if view_type == "DataFrames":
                st.dataframe(options.calls)
                st.dataframe(options.puts)
            else:
                # Fetch all expiration dates
                exp_dates = tickerData.options
                exp_date = st.selectbox("Select Expiration Date", exp_dates)
                
                # Fetch options data for the selected expiration date
                calls, puts = fetch_options_data(tickerSymbol, exp_date)
                
                # Heatmap for Implied Volatility
                st.subheader("Implied Volatility Heatmap")
                fig_iv = go.Figure(data=go.Heatmap(
                    z=calls['impliedVolatility'],
                    x=calls['strike'],
                    y=['Call Options'],
                    colorscale='Viridis',
                    colorbar=dict(title='Implied Volatility')
                ))
                fig_iv.update_layout(title=f'Implied Volatility for {tickerSymbol} - {exp_date}', xaxis_title='Strike Price', yaxis_title='Option Type')
                st.plotly_chart(fig_iv)
                
                # Scatter Plot for Options Pricing
                st.subheader("Options Pricing Scatter Plot")
                fig_price = px.scatter(calls, x='strike', y='lastPrice', color='impliedVolatility', 
                                      hover_data=['contractSymbol', 'volume', 'openInterest'],
                                      title=f'Options Pricing for {tickerSymbol} - {exp_date}')
                fig_price.update_xaxes(title='Strike Price')
                fig_price.update_yaxes(title='Last Price')
                st.plotly_chart(fig_price)
                
                # Bar Chart for Open Interest
                st.subheader("Open Interest Bar Chart")
                fig_oi = px.bar(calls, x='strike', y='openInterest', 
                                title=f'Open Interest for {tickerSymbol} Calls - {exp_date}',
                                labels={'strike': 'Strike Price', 'openInterest': 'Open Interest'})
                st.plotly_chart(fig_oi)
                
                # Combine Calls and Puts for more comprehensive visualizations
                options_data = pd.concat([calls.assign(Type='Call'), puts.assign(Type='Put')], ignore_index=True)
                
                # Volume vs. Open Interest for Calls and Puts
                st.subheader("Volume vs. Open Interest")
                fig_vol_oi = px.scatter(options_data, x='volume', y='openInterest', color='Type', 
                                       size='impliedVolatility', hover_data=['strike', 'lastPrice'],
                                       title=f'Volume vs. Open Interest for {tickerSymbol} Options - {exp_date}')
                fig_vol_oi.update_xaxes(title='Volume')
                fig_vol_oi.update_yaxes(title='Open Interest')
                st.plotly_chart(fig_vol_oi)
        else:
            st.write("No options data available for this symbol.")
    else:
        st.write("Please enter a ticker symbol to view options data.")

def fetch_options_data(ticker, exp_date):
    stock = yf.Ticker(ticker)
    options = stock.option_chain(exp_date)
    return options.calls, options.puts


# Sentiment
def sentiment_page():
    tickerSymbol = st.session_state.tickerSymbol
    st.write("Nothing to see here yet")



# Futures
def Futures_page():
    futuresSymbol = st.selectbox("Select Futures Symbol", [
        "MES1!",
        "NQ1!",
        "YM1!",
        "RTY1!",
        "VX1!",
        "NKD1!",
        "HSI1!",
        "CL1!",
        "GC1!",
        "SI1!",
        "HG1!",
        
    ])
    futures_chart = f"""
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container" style="height:100%;width:100%">
        <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
        <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
        {{
        "width": "1000",
        "height": "620",
        "symbol": "{futuresSymbol}",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "range": "12M",
        "hide_side_toolbar": false,
        "allow_symbol_change": false,
        "calendar": false,
        "hide_volume": true,
        "support_host": "https://www.tradingview.com"
        }}
        </script>
        </div>
        <!-- TradingView Widget END -->
        """
    # Render the TradingView widget
    st.components.v1.html(futures_chart, width=1000, height=620)


pg = st.navigation([st.Page(home_page, title="Home", icon="📈"), st.Page(options_page, title="Options", icon="📊"), st.Page(sentiment_page, title="Sentiment", icon="😰"), st.Page(Futures_page, title="Futures", icon="🔮")], position="sidebar")
pg.run()

# Calendar Widget in Sidebar
tradingview_calendar_widget = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">
    <div class="tradingview-widget-container__widget"></div>
    <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
    <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
    {{
    "colorTheme": "dark",
    "isTransparent": false,
    "width": "350",
    "height": "500",
    "locale": "en",
    "importanceFilter": "0,1",
    "countryFilter": "us"
    }}
    </script>
    </div>
    <!-- TradingView Widget END -->
    """

# Embed in sidebar
with st.sidebar:
    components.html(tradingview_calendar_widget, height=600, scrolling=True)
