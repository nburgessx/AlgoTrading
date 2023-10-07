# Import libraries
import pandas as pd
import statsmodels.api as sm
import numpy as np
import math

# Get historical data for the instruments
x = pd.read_csv('EWA.csv',index_col=0)['Adj Close']
y = pd.read_csv('EWC.csv',index_col=0)['Adj Close']    

# Hedge Ratio
model = sm.OLS(y.iloc[:90], x.iloc[:90])
model = model.fit() 

# Spread GLD - hedge ratio * GDX
spread = -model.params[0]*x + y
spread = spread.iloc[:90]

# Spread and differenence between spread
spread_x = np.mean(spread) - spread 
spread_y = spread.shift(-1) - spread
spread_df = pd.DataFrame({'x':spread_x,'y':spread_y})
spread_df = spread_df.dropna()

# Theta as regression beta between spread and difference between spread
model_s = sm.OLS(spread_df['y'], spread_df['x'])
model_s = model_s.fit() 
theta=  model_s.params[0]

# Calculate the half life
hl = math.log(2)/theta
print(hl,'days')
