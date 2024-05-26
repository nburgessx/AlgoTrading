import random

# Get the ip address where the BERT Server is running
def get_ip_address():
    return "bert-server.quantinsti.com"


# API key to access quandl data
def get_quantinsti_api_key():
    keys = ["Type your API key here"]
    return random.choice(keys)
