import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import datetime
from datetime import date
import os
import fxstreet_scraper
import StringIO
import csv

on_heroku = False

if 'DYNO' in os.environ:
    on_heroku = True

def main():
    wks = setup_credentials()

    if on_heroku:
        update_spreadsheet(wks)
    else:
        request = raw_input('Enter Y to update the fxstreet spreadsheet: ')
        if request is 'Y' or request is 'y':
            update_spreadsheet(wks)

def setup_credentials():
    scope = ['https://spreadsheets.google.com/feeds']
    if on_heroku:
        keyfile_dict = setup_keyfile_dict()
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, scope)
    else:
        credentials = ServiceAccountCredentials.from_json_keyfile_name('My Project-3b0bc29d35d3.json', scope)

    gc = gspread.authorize(credentials)

    wks = gc.open_by_key("1GnVhFp0s28HxAEOP6v7kmfmt3yPL_TGJSV2mcn1RPMY").sheet1
    return wks

def setup_keyfile_dict():
    keyfile_dict = dict()
    keyfile_dict['type'] = os.environ.get('TYPE')
    keyfile_dict['client_email'] = os.environ.get('CLIENT_EMAIL')
    keyfile_dict['private_key'] = unicode(os.environ.get('PRIVATE_KEY').decode('string_escape'))
    keyfile_dict['private_key_id'] = os.environ.get('PRIVATE_KEY_ID')
    keyfile_dict['client_id'] = os.environ.get('CLIENT_ID')

    return keyfile_dict


def bootstrap_sheet(wks):
    # If new spreadsheet, update current row indicator
    if wks.acell('A1').value == '':
        wks.update_acell('A1', 2)


def update_spreadsheet(wks):
    today = date.today()
    
    bootstrap_sheet(wks)
    current_row = int(wks.acell('A1').value)
    
    csv_data = fxstreet_scraper.main()
    csv_data = StringIO.StringIO(csv_data)
    csv_reader = csv.reader(csv_data)
    
    for csv_index, row in enumerate(csv_reader):
        cell_list = wks.range('A' + str(current_row) + ':G' + str(current_row))
        # are we in the first row of the csv data? aka(column names)
        if csv_index == 0:
            # Check if we have an empty spreadsheet
            if current_row > 2:
                continue
        for row_index, data in enumerate(row):
            cell_list[row_index].value = data
        wks.update_cells(cell_list)
        current_row += 1

    wks.update_acell('A1', current_row)
    

def pull_data(num_days):
    wks = setup_credentials()
    current_row = wks.acell('A1').value
    latest_entry = int(wks.acell('A1').value) - 1
    if num_days > latest_entry:
        start_row = 2
    else:
        start_row = latest_entry - num_days

    columns = [x for x in wks.row_values(1) if x]
    rollover_table = pd.DataFrame(columns=columns)
    for row_index in range(start_row, latest_entry + 1):
        row_data = pd.to_datetime(wks.row_values(row_index)[0])
        row_date = [float(x) for x in wks.row_values(row_index)[1:] if x]
        rollover_values = [row_data] + row_date
        rollover_table.loc[row_index - 2] = rollover_values
    rollover_table = rollover_table.set_index(current_row)
    return rollover_table


def increment_letter(letter, amount):
    cur = ord(letter)
    return chr(cur+amount)

if __name__ == "__main__":
    main()
