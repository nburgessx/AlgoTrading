# Import libraries
import pandas as pd
import statsmodels.api as sm
import numpy as np
import math


# Get historical data for the Equity Index ETFs EWA (Australia) and EWC (Canada)
x = pd.read_csv('EWA.csv',index_col=0)['Close']
y = pd.read_csv('EWC.csv',index_col=0)['Close']    

# Hedge Ratio
model = sm.OLS(y.iloc[:90], x.iloc[:90])
model = model.fit() 

# Spread EWC - hedge ratio * EWA
spread = -model.params[0]*x + y
spread = spread.iloc[:90]

# Compute the Hurst Exponent using the Rescaled Range Approach
# Using Numpy vectorization compute the spread and difference between spread
spread_x = np.mean(spread) - spread 
spread_y = spread.shift(-1) - spread
spread_df = pd.DataFrame({'x':spread_x,'y':spread_y})
spread_df = spread_df.dropna()

# Hurst Exponent as regression beta between spread and difference between spread
# Use Ordinary Least Squares (OLS) Regression from statsmodels
model_s = sm.OLS(spread_df['y'], spread_df['x'])
model_s = model_s.fit() 
hurst_exponent =  model_s.params[0]
print(f'Hurst Exponent: {hurst_exponent:.2f}')

# Calculate the half life
# This is the derived from the expected value of an Ohnstein-Uhlenbeck (OU) process
half_life = math.log(2)/hurst_exponent
print(f'Half-Life: {half_life} (days)')
