# Step 1:
# If you get yfinance module not found error. 
# Uncomment below Python code to install it

#!pip install yfinance

# Step 2:
import yfinance as yf

# Step 3:
# Define a function to fetch historical data
def get_stock_data(inst_name, start_date, end_date):
    
    try:
        # Step 4:
        # Fetch the data
        data = yf.download(inst_name, start_date, end_date, auto_adjust=True)            
        # Return data
        return data
                
    except Exception as e:
        # Show exception if the data retrieval fails
        print ("Failed to get stock data for", inst_name, e)       