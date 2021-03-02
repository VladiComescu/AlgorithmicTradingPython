import numpy as np
import pandas as pd
import requests
import xlsxwriter
import math

# Importing List of Stocks
stocks = pd.read_csv('sp_500_stocks.csv')

# Acquiring an API Token
from secrets import IEX_CLOUD_API_TOKEN

"""
API Call Test
* Market capitalization for each stock
* Price of each stock
"""
symbol = 'AAPL'
api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote?token={IEX_CLOUD_API_TOKEN}'
data = requests.get(api_url).json()

# Parsing API Call
data['latestPrice']
data['marketCap']

# Adding Stocks Data to a DataFrame
my_columns = ['Ticker', 'Price', 'Market Capitalization', 'Number Of Shares to Buy']

# First test with AAPL stock
final_dataframe = pd.DataFrame(columns=my_columns)

final_dataframe = final_dataframe.append(pd.Series(
    ['AAPL', data['latestPrice'], data['marketCap'], 'N/A'],
    index=my_columns),
    ignore_index=True)

# Looping Through The Tickers in the List of Stocks
final_dataframe = pd.DataFrame(columns=my_columns)

for symbol in stocks['Ticker']:
    api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote?token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(api_url).json()
    final_dataframe = final_dataframe.append(pd.Series(
        [symbol, data['latestPrice'], data['marketCap'], 'N/A'],
        index=my_columns),
        ignore_index=True)

"""
Using Batch API Calls to Improve Performance
IEX Cloud limits their batch API calls to 100 tickers per request.
"""


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


symbol_groups = list(chunks(stocks['Ticker'], 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))
    # print(symbol_strings[i])


final_dataframe = pd.DataFrame(columns=my_columns)

for symbol_string in symbol_strings:
    # print(symbol_strings)
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(pd.Series(
            [symbol, data[symbol]['quote']['latestPrice'], data[symbol]['quote']['marketCap'], 'N/A'],
            index=my_columns),
            ignore_index=True)


# Number of Shares to Buy
portfolio_size = input("Enter the value of your portfolio:")

try:
    val = float(portfolio_size)
except ValueError:
    print("That's not a number! \n Try again:")
    portfolio_size = input("Enter the value of your portfolio:")


position_size = float(portfolio_size) / len(final_dataframe.index)
for i in range(0, len(final_dataframe['Ticker']) - 1):
    final_dataframe.loc[i, 'Number Of Shares to Buy'] = math.floor(position_size / final_dataframe['Price'][i])


# Initializing our XlsxWriter Object
writer = pd.ExcelWriter('recommended_trades.xlsx', engine='xlsxwriter')
final_dataframe.to_excel(writer, sheet_name='Recommended Trades', index=False)

"""
Creating the Formats
* String format for tickers
* \\$XX.XX format for stock prices
* \\$XX,XXX format for market capitalization
* Integer format for the number of shares to purchase
"""

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format(
    {'font_color': font_color, 'bg_color': background_color, 'border': 1})

dollar_format = writer.book.add_format(
    {'num_format': '$0.00', 'font_color': font_color, 'bg_color': background_color, 'border': 1})

integer_format = writer.book.add_format(
        {'num_format': '0', 'font_color': font_color, 'bg_color': background_color, 'border': 1})

"""
Applying the Formats to the Columns

We can use the `set_column` method applied to the `writer.sheets['Recommended Trades']` object

writer.sheets['Recommended Trades'].set_column('B:B', 18, string_format)
# (Apply the format to column B, Apply a column width of 18 pixels, Applies the format 'string_format' to the column)

# writer.sheets['Recommended Trades'].write('A1', 'Ticker', string_format)
# writer.sheets['Recommended Trades'].write('B1', 'Price', string_format)
# writer.sheets['Recommended Trades'].write('C1', 'Market Capitalization', string_format)
# writer.sheets['Recommended Trades'].write('D1', 'Number Of Shares to Buy', string_format)
# writer.sheets['Recommended Trades'].set_column('A:A', 20, string_format)
# writer.sheets['Recommended Trades'].set_column('B:B', 20, dollar_format)
# writer.sheets['Recommended Trades'].set_column('C:C', 20, dollar_format)
# writer.sheets['Recommended Trades'].set_column('D:D', 20, integer_format)
"""

column_formats = {
    'A': ['Ticker', string_format],
    'B': ['Price', dollar_format],
    'C': ['Market Capitalization', dollar_format],
    'D': ['Number of Shares to Buy', integer_format]
}

for column in column_formats.keys():
    writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 20, column_formats[column][1])
    writer.sheets['Recommended Trades'].write(f'{column}1', column_formats[column][0], string_format)

# Saving Excel Output
writer.save()
