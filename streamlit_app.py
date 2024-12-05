import streamlit as st
from streamlit import markdown
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
import yaml
from yaml.loader import SafeLoader

#LAYOUT
st.set_page_config(layout="centered")

#TITLE
st.title("InvinciBull 1.1")

#TICKER TAPE
tradingview_widget = f"""
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
<div class="tradingview-widget-container__widget"></div>
<div class="tradingview-widget-copyright">
    <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">
</div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js" async>
{{
    "symbols": [
        {{ "description": "S&P 500 ETF", "proName": "AMEX:SPY" }},
        {{ "description": "Nasdaq 100 ETF", "proName": "NASDAQ:QQQ" }},
        {{ "description": "Russell 2000 ETF", "proName": "AMEX:IWM" }},
        {{ "description": "Dow Jones ETF", "proName": "AMEX:DIA" }},
        {{ "description": "Apple Inc.", "proName": "NASDAQ:AAPL" }},
        {{ "description": "Amazon.com Inc.", "proName": "NASDAQ:AMZN" }},
        {{ "description": "Alphabet Inc.", "proName": "NASDAQ:GOOG" }},
        {{ "description": "Microsoft Corp.", "proName": "NASDAQ:MSFT" }},
        {{ "description": "NVIDIA Corp.", "proName": "NASDAQ:NVDA" }},
        {{ "description": "Tesla Inc.", "proName": "NASDAQ:TSLA" }}
    ],
    "showSymbolLogo": true,
    "isTransparent": true,
    "displayMode": "compact",
    "colorTheme": "dark",
    "locale": "en"
}}
</script>
</div>
<!-- TradingView Widget END -->
"""
st.components.v1.html(tradingview_widget, width=800, height=75)

#YAHOO
tickerSymbol = st.text_input("Enter the stock symbol here...", key="custom", label_visibility="visible", placeholder="AAPL", max_chars=5).upper()

# Function to fetch and extract SEC filing text, filtered by type
def fetch_sec_filing_text(filings, valid_types=["10-Q","10-K", "8-K", "6-K"]):
    try:
        # Filter filings by type
        filtered_filings = [
            filing for filing in filings if filing["Filing Type"] in valid_types
        ]
        if not filtered_filings:
            return "No relevant SEC filings available."

        # Get the first valid filing link
        filing_url = filtered_filings[0]["Filing Type"].split('href="')[1].split('"')[0]
        filing_url = "https://www.sec.gov" + filing_url

        # Fetch the filing content
        response = requests.get(filing_url)
        response.raise_for_status()  # Raise an error for bad responses
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract meaningful text from the filing (e.g., <div> or <p> tags)
        paragraphs = soup.find_all('p')  # Extract all paragraph tags
        text = "\n".join([p.get_text() for p in paragraphs if p.get_text()])

        # Limit the size of the text to avoid overwhelming the AI model
        return text[:5000]  # Truncate to the first 5000 characters
    except Exception as e:
        return f"Error fetching SEC filing: {e}"
        
if not tickerSymbol:
    st.info("Please enter a ticker symbol to fetch stock data.")
else:
    # Here you proceed with fetching the data since tickerSymbol is not empty
    tickerData = yf.Ticker(tickerSymbol)
    main_info = tickerData.fast_info
    comp_info = tickerData.info
    QFS = tickerData.quarterly_financials
    QBS = tickerData.quarterly_balancesheet
    #TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Company", 
        "Chart", 
        "Financials", 
        "Filings", 
        "AI Overview"])
    #COMPANY
    with tab1:
        # SUMMARY
        company_name = comp_info.get("shortName")
        st.header(company_name)
        # HQ & WEBSITE
        city = comp_info.get("city")
        state = comp_info.get("state")
        country = comp_info.get("country")
        website = comp_info.get("website")
        # Check and construct the address dynamically
        address_parts = [city, state, country]
        address = ", ".join(part for part in address_parts if part)  # Join non-empty parts
        # Display the address and website
        st.write(address)
        col1, col2, col3 = st.columns(3)
        with col1:
            #MINI CHART 
            tradingview_widget = f"""
                <!-- TradingView Widget BEGIN -->
                <div class="tradingview-widget-container">
                <div class="tradingview-widget-container__widget"></div>
                <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
                <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js" async>
                {{
                "symbol": "{tickerSymbol}",
                "width": "100%",
                "height": "100%",
                "locale": "en",
                "dateRange": "12M",
                "colorTheme": "dark",
                "isTransparent": true,
                "autosize": true,
                "largeChartUrl": "",
                "chartOnly": false
                }}
                </script>
                </div>
                <!-- TradingView Widget END -->
                """
    
            # Render the TradingView widget
            st.components.v1.html(tradingview_widget, width=450, height=200)
        with col3:
            # Inject CSS to remove underline from links
            st.markdown(
                """
                <style>
                a {
                    text-decoration: none;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
    
            if website:
                # Remove "https://www." or "http://www." from the URL for display purposes
                clean_website = website.replace("https://www.", "").replace("http://www.", "").replace("https://", "").replace("http://", "")
                
                # Use a link symbol (🔗) with the cleaned website text
                st.markdown(f"[🔗 {clean_website}]({website})", unsafe_allow_html=True)
            else:
                st.write("Website: Not available")
    
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
        # Business Summary
        summary = comp_info.get("longBusinessSummary")
    
        if summary:
            with st.expander("Business Summary"):
                st.write(summary)
        else:
            st.write("Business summary not available.")
        ## OFFICERS/EMPLOYEES    
        c_level = comp_info.get("companyOfficers")
        if c_level:
            st.subheader("Officers:")
            for officer in c_level:
                if 'name' in officer and 'title' in officer:
                    st.write(f"- **{officer['name']}**: {officer['title']}")
        else:
            st.write("No officers information available.")
    
        FTE = comp_info.get("fullTimeEmployees")
        st.subheader("Employees:")
        st.write(f"{FTE:,}" if FTE else "No employee information available.")
    
    #CHART
    with tab2:
        company_name = comp_info.get("shortName")
        st.subheader(company_name)
        tradingview_widget = f"""
            <!-- TradingView Widget BEGIN -->
            <div class="tradingview-widget-container" style="height:100%;width:100%">
            <div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
            <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
            <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
            {{
            "width": "1000",
            "height": "610",
            "symbol": "{tickerSymbol}",
            "timezone": "America/New_York",
            "theme": "dark",
            "style": "2",
            "locale": "en",
            "backgroundColor": "rgba(0, 0, 0, 1)",
            "gridColor": "rgba(0, 0, 0, 0.06)",
            "hide_top_toolbar": true,
            "withdateranges": true,
            "range": "YTD",
            "allow_symbol_change": false,
            "save_image": false,
            "calendar": false,
            "support_host": "https://www.tradingview.com"
            }}
            </script>
            </div>
            <!-- TradingView Widget END -->
            """
    
        # Render the TradingView widget
        st.components.v1.html(tradingview_widget, width=1000, height=1000)
        
    #FINANCIALS
    with tab3:
        company_name = comp_info.get("shortName")
        st.subheader(company_name)
        #FINANCIALS TRADINGVIEW WIDGET
        tradingview_widget = f"""
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container">
          <div class="tradingview-widget-container__widget"></div>
          <div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
          <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-financials.js" async>
          {{
          "isTransparent": true,
          "largeChartUrl": "",
          "displayMode": "regular",
          "width": 400,
          "height": 550,
          "colorTheme": "dark",
          "symbol": "NASDAQ:AAPL",
          "locale": "en"
        }}
          </script>
        </div>
        <!-- TradingView Widget END -->
        """
        st.components.v1.html(tradingview_widget, width=1000, height=400)
    
        # Display Quarterly Balance Sheet (QBS)
        st.write("### Quarterly Balance Sheet")
        try:
            # Transpose QBS to have quarters as rows
            qbs_transposed = QBS.T
    
            # Format the column headers (dates) as 'Q1YYYY', 'Q2YYYY', etc.
            quarters = [
                f"Q{(date.month - 1) // 3 + 1}{date.year}" for date in qbs_transposed.index
            ]
            qbs_transposed.index = quarters
    
            # Format the values as currency
            qbs_transposed = qbs_transposed.applymap(
                lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"
            )
    
            # Display the formatted DataFrame
            st.dataframe(qbs_transposed)
        except Exception as e:
            st.write("Quarterly Balance Sheet (QBS) data is not available.")
    
        # Display Quarterly Financial Statements (QFS)
        st.write("### Quarterly Financial Statements")
        try:
            # Transpose QFS to have quarters as rows
            qfs_transposed = QFS.T
    
            # Format the column headers (dates) as 'Q1YYYY', 'Q2YYYY', etc.
            quarters = [
                f"Q{(date.month - 1) // 3 + 1}{date.year}" for date in qfs_transposed.index
            ]
            qfs_transposed.index = quarters
    
            # Format the values as currency
            qfs_transposed = qfs_transposed.applymap(
                lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A"
            )
    
            # Display the formatted DataFrame
            st.dataframe(qfs_transposed)
        except Exception as e:
            st.write("Quarterly Financial Statements (QFS) data is not available.")
    
    #FILINGS
    with tab4:
        company_name = comp_info.get("shortName")
        st.subheader(company_name)
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
    
    #AI OVERVIEW
    with tab5:
        if st.button("Analyze stock"):
            company_name = comp_info.get("shortName")
            st.subheader(company_name)
            company_info = [company_name, city, state, country, website, summary]
            st.write("AI Overview")
    
            # Initialize the Ollama LLM
            llm = OllamaLLM(model="llama3.1", api_base="http://localhost:11434")  # Update with your Ollama API URL
    
            # Define a prompt template for the AI overview
            prompt_template = """
                        Analyze the following financial data for {company_name} and provide insights:
                            1. Read through: 
                                Company Info:
                                {company_info}
    
                                SEC Filing Highlights:
                                {filing_text}
    
                                Quarterly Financial Statements (QFS):
                                {qfs}
    
                                Quarterly Balance Sheet (QBS):
                                {qbs}
                            2. Key performance indicators (KPIs) (e.g., revenue growth, profit margins, cash flow).
                            3. Recent stock performance and key drivers behind fluctuations.
                            4. SWOT analysis (Strengths, Weaknesses, Opportunities, Threats).
                            5. Future outlook and risks based on current market trends and company trajectory.
                        Include actionable recommendations for portfolio strategy: Should we buy, sell, or hold? Justify your suggestion based on quantitative and qualitative factors. Provide all insights in a clear, bullet-point format for quick review."
                    """
            # LangChain prompt
            prompt = PromptTemplate(template=prompt_template, input_variables=["company_name", "comp_info", "summary","filing_text", "qfs", "qbs"])
    
            # Define the LangChain LLMChain
            chain = LLMChain(llm=llm, prompt=prompt)
    
            # Get the most relevant SEC filing text
            try:
                filings = get_sec_filings(tickerSymbol)  # Use the existing function to get filings
                filing_text = fetch_sec_filing_text(filings, valid_types=["10-K", "8-K", "6-K", "10-Q"])
            except Exception as e:
                filing_text = f"Error retrieving SEC filings: {e}"
                print(filing_text)
    
            # Generate the AI overview when the "Analyze stock" button is pressed
            try:
                # Convert QFS and QBS to string format for the prompt
                qfs_summary = QFS.T.to_string() if not QFS.empty else "No data available."
                qbs_summary = QBS.T.to_string() if not QBS.empty else "No data available."
    
                # Generate the AI overview
                ai_overview = chain.run({"company_name": company_name, "company_info": company_info, "summary": summary, "filing_text": filing_text, "qfs": qfs_summary, "qbs": qbs_summary})
    
                # Display the AI overview
                st.write(ai_overview)
            except Exception as e:
                st.write("AI Overview could not be generated. Please check the data or API configuration.")
