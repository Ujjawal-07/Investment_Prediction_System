import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from prophet import Prophet
from prophet.make_holidays import make_holidays_df

# Helper function to fetch mutual fund data using NSE API
def fetch_mutual_fund_data(fund_code):
    try:
        url = f"https://www.nseindia.com/api/mf/owe/get-historical-data?schemeCode={fund_code}&fromDate=20200101&toDate=20231231"
        response = requests.get(url)
        data = response.json()
        
        if not data['data']:
            return None, "No data available for the specified mutual fund code."
        
        df = pd.DataFrame(data['data'])
        df['date'] = pd.to_datetime(df['date'])
        df.rename(columns={'date': 'ds', 'nav': 'y'}, inplace=True)
        df['y'] = pd.to_numeric(df['y'], errors='coerce')
        df = df.dropna(subset=['y'])  # Remove rows with NaN in 'y'

        if len(df) < 2:
            return None, "Not enough data points for prediction."

        return df, None
    except Exception as e:
        return None, str(e)

# Streamlit App Setup
st.set_page_config(page_title="Stock & Mutual Fund Price Predictor", layout="wide")
st.title("📊 Stock & Mutual Fund Price Predictor App")
st.subheader("Predict Future Stock & Mutual Fund Prices")

# Sidebar Navigation
st.sidebar.title("🔍 Navigation")
option = st.sidebar.radio("Go to:", ["Home", "Predict", "About"])

if option == "Home":
    st.subheader("Welcome! Select options from the sidebar.")
    st.subheader("This app leverages Streamlit to provide real-time predictions for Stock Prices and Mutual Fund NAVs using the powerful Prophet forecasting model. With intuitive interfaces and interactive features, users can easily input stock tickers or mutual fund codes to view live prices, past data, and future predictions, helping them make informed investment decisions.")
    st.subheader("Whether you're tracking stock performance or mutual fund NAVs, this app ensures you have the insights you need, seamlessly integrated into a single platform powered by Streamlit.")
elif option == "About":
    st.subheader("About This App")
    st.markdown("This app predicts stock and mutual fund prices using AI models like Prophet.")
    st.markdown("Disclaimer and Important Notes: ")
    st.markdown(" * Data Accuracy: The predictions generated by this app are based on historical data and may not always reflect future outcomes. Past performance is not indicative of future results.")
    st.markdown(" * Investment Risks: Stock and mutual fund investments carry inherent risks. The accuracy of predictions depends on various factors such as market conditions, economic events, and unforeseen circumstances.")
    st.markdown(" * For Informational Purposes Only: The information provided is for general informational purposes and should not be considered as financial advice. Users are advised to do their own due diligence and consult with a qualified financial advisor before making any investment decisions.")
    st.markdown(" * Accuracy of Predictions: The predictive models used here, while powered by AI and historical data, are subject to limitations and may not always yield precise outcomes. The results are best used as a reference, not as a definitive guide for investment decisions.")
    st.markdown(" * Future Predictions: Forecasts are generated based on assumptions, historical trends, and seasonality patterns. Actual market behavior may vary, and there is no guarantee that the predicted outcomes will materialize.")


elif option == "Predict":
    st.subheader("Predict Stock or Mutual Fund Prices")

    # Step 1: User Input - Select Asset Type
    asset_type = st.radio("Select Asset Type", ["Stock", "Mutual Fund"])

    if asset_type == "Stock":
        # Step 2: User Input - Stock Ticker
        ticker = st.text_input("Enter Indian Stock Ticker (e.g., TCS.NS, RELIANCE.NS)", "TCS.NS")
        try:
            # Fetch Real-Time Stock Price
            stock = yf.Ticker(ticker)
            stock_data = stock.history(period="5y", interval="1d")
            stock_data.reset_index(inplace=True)
            stock_data = stock_data[['Date', 'Close']]  # Select only the Date and Close columns
            stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)  # Ensure Date is in the correct format
            stock_data.rename(columns={'Date': 'ds', 'Close': 'y'}, inplace=True)
            
            live_price = stock_data['y'].iloc[-1]  # Use the last available day's closing price
            st.write(f"**Live Stock Price for {ticker}:** {live_price:.2f} INR")

            # Step 3: Train the Prophet Model for Stock
            model = Prophet(
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05,
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False
            )

            changepoint_dates = pd.to_datetime(['2022-03-01', '2022-06-01', '2023-01-01'])
            model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
            model.add_seasonality(name='weekly', period=7, fourier_order=3)

            # Define Indian holidays
            holidays = make_holidays_df(year_list=[2021, 2022, 2023, 2024], country='IN')
            model = Prophet(holidays=holidays)
            model.fit(stock_data)

            # Step 4: Make Future Predictions
            future = model.make_future_dataframe(periods=90)  # Forecast for 90 days (3 months)
            forecast = model.predict(future)

            # Filter forecast data from 2024 onwards
            forecast_filtered = forecast[forecast['ds'].dt.year >= 2024]

            # Display Forecast Data (filtered)
            st.write(f"**Predicted Stock Prices for {ticker} (From 2024, Next 90 Days):**")
            st.dataframe(forecast_filtered[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])

            # Plot Prediction Graph
            fig = model.plot(forecast_filtered)
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Error: {e}. Please enter a valid stock ticker (e.g., TCS.NS, RELIANCE.NS).")

    elif asset_type == "Mutual Fund":
        # Step 2: User Input - Mutual Fund Code
        fund_code = st.text_input("Enter Mutual Fund Code (e.g., HDFC.MF, SBI.MF)", "HDFC.MF")

        try:
            mf_data, error = fetch_mutual_fund_data(fund_code)

            if error:
                st.error(f"Error: {error}. Please enter a valid mutual fund code.")
            else:
                # Display the live price
                live_price = mf_data['y'].iloc[-1]  # Last available day's price
                st.write(f"**Live Mutual Fund Price for {fund_code}:** {live_price:.2f} INR")

                # Step 3: Train the Prophet Model for Mutual Fund
                model = Prophet(
                    seasonality_mode='multiplicative',
                    changepoint_prior_scale=0.05,
                    yearly_seasonality=True,
                    weekly_seasonality=True,
                    daily_seasonality=False
                )

                # Define holidays for India
                holidays = make_holidays_df(year_list=[2021, 2022, 2023, 2024], country='IN')
                model = Prophet(holidays=holidays)
                model.fit(mf_data)

                # Step 4: Make Future Predictions
                future = model.make_future_dataframe(periods=90)  # Forecast for 90 days (3 months)
                forecast = model.predict(future)

                # Filter forecast data from 2024 onwards
                forecast_filtered = forecast[forecast['ds'].dt.year >= 2024]

                # Display Forecast Data (filtered)
                st.write(f"**Predicted Mutual Fund Prices for {fund_code} (From 2024, Next 90 Days):**")
                st.dataframe(forecast_filtered[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])

                # Plot Prediction Graph
                fig = model.plot(forecast_filtered)
                st.pyplot(fig)

        except Exception as e:
            st.error(f"Error: {e}. Please enter a valid mutual fund code.")

