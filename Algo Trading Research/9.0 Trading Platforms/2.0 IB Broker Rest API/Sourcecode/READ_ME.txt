---> REST API Lecture <---

01. cp_web_api_functions.py --> This file contains all user-defined functions to perform various trading operations using the IB REST API.

02. Entry_Point.py --> This file imports all functions defined in the above file and demonstrates how to use them. Start with this file.

03. Real_Time_Data_Using_Websockets.py --> This file demonstrates how to stream real-time data for assets over WebSockets from IB.

04.a. alpaca_keys.txt --> Store your API key and API secret here in the file.

04.b. Real_Time_Data_From_Alpaca.py --> This file demonstrates streaming of real-time data over WebSockets from Alpaca. To execute code in this file, you will need to obtain API key and API secret by registering an account on Alpaca. Store API Key and Secret in the above-mentioned text file.

### 05 Strategy

The idea of this sample strategy is to demonstrate how one can build a full-fledged trading strategy and trade in an automated fashion.

05.a base_functions.py --> This file contains all functions that will place requests and receive responses using the REST API.

05.b RSI_Intraday_Strategy.py --> This file contains the core logic of the strategy. It uses functions defined in the above file to execute trading operations.