import streamlit as st
import requests
import datetime
import json
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup

# Initialize session state for holding if not initialized
if "holding" not in st.session_state:
    st.session_state.holding = []

# Define the file path for saving the data
html_file_path = "holdings_data.html"

# Function to read holdings data from the HTML file (if it exists)
def read_holdings_from_file():
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        st.warning("Holdings data file not found. Starting fresh.")
        return None
    
# Function to load holdings data from the JSON file
def load_holdings_from_file():
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            # Load the holdings as a JSON string
            holdings_data = json.load(file)
            if holdings_data:
                st.session_state.holding = holdings_data
                st.success("Holdings data loaded successfully!")
            else:
                st.warning("Holdings file is empty.")
    except FileNotFoundError:
        st.warning("Holdings data file not found. Starting fresh.")
    except json.JSONDecodeError:
        st.warning("Error loading holdings: Invalid JSON format.")




# Function to save holdings data to the HTML file
def save_holdings_to_file(holdings_df):
    try:
        with open(html_file_path, "w", encoding="utf-8") as file:
            json.dump(holdings_df.to_dict(orient="records"), file)
        st.success("Holdings data saved successfully!")
    except Exception as e:
        st.error(f"Failed to save holdings: {e}")

# Function to fetch the current price and company name of a stock
def fetch_current_price_and_name(ticker, exchange):
    try:
        url = f'https://www.google.com/finance/quote/{ticker}:{exchange}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract company name (usually in the <title> or <meta> tag)
        title_tag = soup.find('title')
        company_name = title_tag.text.split(' Stock Price & News')[0] if title_tag else ticker

        # Extract current price
        price_element = soup.find(class_="YMlKec fxKbKc")
        if price_element:
            current_price = float(price_element.text.strip()[1:].replace(",", ""))
            return current_price, company_name
        else:
            raise ValueError(f"Unable to fetch price for {ticker}:{exchange}")
    except Exception as e:
        st.warning(f"Error fetching data for {ticker}:{exchange}: {e}")
        return None, None

# Stock Dashboard Page
# Stock Dashboard Page
def stock_dashboard():
    st.header("Indian Stock Dashboard")

    ticker = st.sidebar.text_input('Symbol Code', 'INFY', key="sidebar_ticker_input")
    exchange = st.sidebar.text_input('Exchange', 'NSE', key="exchange_input")

    # Fetch stock data
    current_price, company_name = fetch_current_price_and_name(ticker, exchange)

    if current_price:
        st.subheader("Stock Details")
        st.write(f"**Current Price of {company_name}: ₹{current_price}**")

        buy_price = st.number_input("Enter Buying Price (₹)", min_value=0.0, step=0.01, value=current_price, key="buy_price_input")
        quantity = st.number_input("Enter Quantity", min_value=1, step=1, key="quantity_input")

        if st.button("Buy", key="buy_button"):
            total_buy_price = buy_price * quantity

            # Check if the stock is already in holdings
            stock_exists = False
            for stock in st.session_state.holding:
                if stock['Ticker'] == ticker and stock['Exchange'] == exchange:
                    stock_exists = True
                    # Update quantity and total price
                    stock['Quantity'] += quantity
                    stock['Total Price'] += total_buy_price

                    # Recalculate charges for this new purchase
                    brokerage = max(2, min(0.001 * total_buy_price, 20))
                    stt = total_buy_price * 0.001

                    if exchange == 'NSE':
                        exchange_charge = total_buy_price * 0.0000297
                    elif exchange == 'BSE':
                        exchange_charge = total_buy_price * 0.0000375
                    else:
                        exchange_charge = 0

                    sebi_fee = total_buy_price * 0.000001
                    stamp_duty = total_buy_price * 0.00015
                    dp_charges = 3.5
                    groww_charges = 15
                    dp_and_groww_charges = dp_charges + groww_charges
                    dp_groww_gst = 0.18 * dp_and_groww_charges
                    total_dp_and_groww_charges = dp_and_groww_charges + dp_groww_gst
                    gst = 0.18 * (brokerage + exchange_charge + sebi_fee)

                    # Update the Buying Price After Charges to include new charges
                    additional_charges = (brokerage * 2) + (stt * 2) + (exchange_charge * 2) + (sebi_fee * 2) + stamp_duty + (gst * 2) + total_dp_and_groww_charges
                    stock['Buying Price After Charges'] += total_buy_price + additional_charges

                    # Update breakdown of charges
                    stock['Charges']['Brokerage'] += brokerage * 2
                    stock['Charges']['STT'] += stt * 2
                    stock['Charges']['Exchange Charges'] += exchange_charge * 2
                    stock['Charges']['SEBI Fees'] += sebi_fee * 2
                    stock['Charges']['Stamp Duty'] += stamp_duty
                    stock['Charges']['DP and Groww Charges'] += total_dp_and_groww_charges
                    stock['Charges']['GST'] += gst * 2
                    stock['Charges']['Total Charges'] += additional_charges

                    stock['Date'] = str(datetime.date.today())  # Update date to reflect the latest transaction
                    save_holdings_to_file(pd.DataFrame(st.session_state.holding))
                    st.success(f"Updated {company_name} in holdings!")
                    break

            # If the stock doesn't exist, add it as a new entry
            if not stock_exists:
                brokerage = max(2, min(0.001 * total_buy_price, 20))
                stt = total_buy_price * 0.001

                if exchange == 'NSE':
                    exchange_charge = total_buy_price * 0.0000297
                elif exchange == 'BSE':
                    exchange_charge = total_buy_price * 0.0000375
                else:
                    exchange_charge = 0

                sebi_fee = total_buy_price * 0.000001
                stamp_duty = total_buy_price * 0.00015
                dp_charges = 3.5
                groww_charges = 15
                dp_and_groww_charges = dp_charges + groww_charges
                dp_groww_gst = 0.18 * dp_and_groww_charges
                total_dp_and_groww_charges = dp_and_groww_charges + dp_groww_gst
                gst = 0.18 * (brokerage + exchange_charge + sebi_fee)

                total_buy_price_after_charges = total_buy_price + (brokerage * 2) + (stt * 2) + (exchange_charge * 2) + (sebi_fee * 2) + stamp_duty + (gst * 2) + total_dp_and_groww_charges

                st.session_state.holding.append({
                    'Ticker': ticker,
                    'Exchange': exchange,
                    'Company Name': company_name,
                    'Buying Price': buy_price,
                    'Quantity': quantity,
                    'Total Price': total_buy_price,
                    'Buying Price After Charges': total_buy_price_after_charges,

                    'Charges': {
                        'Brokerage': (brokerage * 2),
                        'STT': (stt * 2),
                        'Exchange Charges': (exchange_charge * 2),
                        'SEBI Fees': (sebi_fee * 2),
                        'Stamp Duty': stamp_duty,
                        'DP and Groww Charges': dp_and_groww_charges + dp_groww_gst,
                        'GST': (gst * 2),
                        'Total Charges': (brokerage * 2) + (stt * 2) + (exchange_charge * 2) + (sebi_fee * 2) + stamp_duty + (gst * 2) + total_dp_and_groww_charges
                    },
                    'Date': str(datetime.date.today())
                })

                save_holdings_to_file(pd.DataFrame(st.session_state.holding))
                st.success(f"{company_name} added to holdings!")

    else:
        st.error("Could not fetch stock data. Please try again.")



# Holdings Page
def holding_page():
    st.header("Holding")

    if st.session_state.holding:
        # Initialize the total invested amount
        total_invested_amount = 0
        total_returns_value = 0
        # Fetch current prices and calculate returns
        for stock in st.session_state.holding:
            current_price, company_name = fetch_current_price_and_name(stock['Ticker'], stock.get('Exchange', 'NSE'))

            stock['Current Price'] = current_price if current_price is not None else "N/A"
            stock['Company Name'] = company_name if company_name else "N/A"

            if current_price is not None:
                total_current_value = current_price * stock['Quantity']
                returns_value = total_current_value - stock['Buying Price After Charges']
                returns_percentage = (returns_value / stock['Buying Price After Charges']) * 100
                stock['Returns'] = f"₹{returns_value:,.2f} ({returns_percentage:.2f}%)"
                stock['Returns Color'] = "green" if returns_value > 0 else "red"

                total_returns_value += returns_value  # Accumulate returns value for total
            else:
                stock['Returns'] = "N/A"
                stock['Returns Color'] = "black"

            # Add the total invested amount for each stock
            total_invested_amount += stock['Buying Price After Charges']

            # Calculate the total returns percentage
        total_returns_percentage = (
            (total_returns_value / total_invested_amount) * 100
            if total_invested_amount > 0
            else 0
        )

            # Display total invested amount and total returns
        total_returns_color = "green" if total_returns_value > 0 else "red"
        st.write(
            f"""
            <div style="font-size:20px; font-weight:bold;">
                Total Invested Amount: ₹{total_invested_amount:,.2f}<br>
                Total Returns: <span style="color:{total_returns_color};">
                ₹{total_returns_value:,.2f} ({(total_returns_value / total_invested_amount) * 100:.2f}%)
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Display total invested amount for all stocks at the top
        

        # Display holdings with box-like layout
        st.write("### Current Holding")
        for i, stock in enumerate(st.session_state.holding):
            company_name = stock['Company Name']

            # Display the card layout for each stock
            st.markdown(
                f"""
                <style>
                .card {{
                width: 700px;
                height: auto;
                background-image: linear-gradient(163deg, #ff00ff 0%, #3700ff 100%);
                border-radius: 20px;
                transition: all .3s;
                margin-bottom: 15px;
                }}
                .card2 {{
                width: 700px;
                height: auto;
                background-color: #000000;
                border-radius: 20px;
                padding: 20px;
                transition: all .2s;
                }}
                .card2:hover {{
                transform: scale(0.99);
                border-radius: 20px;
                }}
                .card:hover {{
                box-shadow: 0px 0px 30px 1px rgba(204, 0, 255, 0.3);
                }}
                </style>
                <div class="card">
                <div class="card2">
                <strong style="font-size: 20px; color: white;">Company:</strong>
                <span style="font-size: 20px; color: white; font-weight: bold;">{stock['Company Name']}</span><br>
                <strong style="color:#848884; font-size: 18px;"> Buying Price:</strong>
                <span style="color:white; font-size: 18px;">₹{stock['Buying Price']:.2f}</span><br>
                <strong style="color:#848884; font-size: 18px;"> Buying Price After Charges:</strong>
                <span style="color:white; font-size: 18px;">₹{stock['Buying Price After Charges']:.2f}</span><br>
                <strong style="color:#848884; font-size: 18px;"> Current Price:</strong>
                <span style="color:white; font-size: 18px;">₹{stock['Current Price'] if stock['Current Price'] != "N/A" else "N/A"}</span><br>
                <strong style="color:#848884; font-size: 18px;"> Quantity:</strong>
                <span style="color:white; font-size: 18px;">{stock['Quantity']}</span><br>
                <strong style="color:#848884; font-size: 18px;"> Total Invested:</strong>
                <span style="color:white; font-size: 18px;">₹{stock['Buying Price After Charges']:.2f}</span><br>
                <strong style="font-size: 18px; color:white;"> Returns:</strong>
                <span style="color:{stock['Returns Color']}; font-size: 18px; font-weight: bold;">{stock['Returns']}</span>
                </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(f"Info on {stock['Company Name']}", key=f"info_{i}"):
                st.write(f"### Details for {stock['Company Name']}")
                st.write(f"**Ticker:** {stock['Ticker']}")
                st.write(f"**Exchange:** {stock['Exchange']}")
                st.write(f"**Date Added:** {stock.get('Date', 'N/A')}")
                st.write(f"**Charges Breakdown:**")
                charges = stock.get("Charges", {})
                st.write(f"- **Brokerage:** ₹{charges.get('Brokerage', 0):.2f}")
                st.write(f"- **STT:** ₹{charges.get('STT', 0):.2f}")
                st.write(f"- **Exchange Charges:** ₹{charges.get('Exchange Charges', 0):.2f}")
                st.write(f"- **SEBI Fees:** ₹{charges.get('SEBI Fees', 0):.2f}")
                st.write(f"- **Stamp Duty:** ₹{charges.get('Stamp Duty', 0):.2f}")
                st.write(f"- **DP & Groww Charges (incl. GST):** ₹{charges.get('DP and Groww Charges', 0):.2f}")
                st.write(f"- **GST on Brokerage, Exchange, SEBI Fees:** ₹{charges.get('GST', 0):.2f}")
                st.write(f"**Total Charges:** ₹{charges.get('Total Charges', 0):.2f}")
                st.write(f"**Final Invested Amount:** ₹{stock['Buying Price After Charges']:.2f}")

            # Add Remove button
            if st.button(f"Remove {company_name}", key=f"remove_{i}"):
                del st.session_state.holding[i]
                save_holdings_to_file(pd.DataFrame(st.session_state.holding))
                st.success(f"{company_name} removed from holdings!")
    else:
        st.write("No stocks added to holdings yet!")

# Streamlit App Layout
def main():
    load_holdings_from_file()
    st.sidebar.title("Menu")
    page = st.sidebar.radio("Select a page", ("Stock Dashboard", "Holdings"))

    if page == "Stock Dashboard":
        stock_dashboard()
    elif page == "Holdings":
        holding_page()

if __name__ == "__main__":
    main()