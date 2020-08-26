'''
This module is used to
1.
Start the process by emailing a form link to all the participants

2.
Finish by emailing a "consequence" to each participant
'''

import config
import os
import pprint
from distutils.util import strtobool
import gspread
import yagmail
import keyring

CQ_HOME_BASE_ID = '1uQs36Izy09dv5b5duAUzhA_NZRWqKF-bksNDftwgHfU'
CQ_RESPONSES_ID = "Flag, Blue"
CQ_FORM_URL = 'https://forms.gle/CXbFueKHzhi4B2Y96'
START_EMAIL_BODY = '<a href='+CQ_FORM_URL+'>Click me!</a>'


def start():

    participants = get_participants()

    # Send the emails, with a link to the form - use yagmail and keyring
    for participant in participants:
        subject = "Hey " + participant[0] + " time to Consequence!"
        content = START_EMAIL_BODY
        email_address = participant[1]
        with yagmail.SMTP('greenbay.graham') as yag:
            yag.send(email_address, subject, content)
    return True

def finish():

    # At this point we are 'hoping' that all of the consequence forms
    # have been returned from the participants ...
    
    # we need to allow for the scenario that we get 1 or more, less than
    # we expected. It is going to be a bit variable ...

    # we won't know whose we haven't got ...

    participants = get_participants()
    print (participants)

    # get the responses spreadsheet

    return True

def get_participants():
    gc = gspread.oauth()

    # Get the whole spreadsheet
    home_base_spreadsheet = gc.open_by_key(CQ_HOME_BASE_ID)

    # Get the first worksheet of the spreadsheet
    home_base_worksheet = home_base_spreadsheet.get_worksheet(0)

    # Get the values along the top of the worksheet
    # We are assuming that we are going to get something like
    '''['Name',
       'Email',
       'August 25, 2020 11:33:12',
       'August 25, 2020 11:38:11',
       'August 26, 2020 11:23:41']
    '''
    # we WILL USE the last value in this list to start the game    
    top_row_values = home_base_worksheet.row_values(1)
    game_datetime = top_row_values[-1]
    print('Game Date Time')
    pprint.pprint(game_datetime)


    # Get all of the information on the home base worksheet 
    # We will get a list of dicts
    # The format appears to be like what is given below
    # 
    # 2 things I have noticed
    # a) The *first entry* always seems to be '':'FALSE'
    # b) Apart from this *first entry* there MUST be something in the first row
    #     of the spreadsheet column for an associated entry to appear in the dict
    '''
    [{'': 'FALSE',
     'August 25, 2020 11:33:12': 'FALSE',
     'August 25, 2020 11:38:11': 'FALSE',
     'August 26, 2020 11:23:41': 'FALSE',
     'Email': 'pangakupu@gmail.com',
     'Name': 'roger'}, etc... etc...
    '''
        
    all_info = home_base_worksheet.get_all_records()
    print('')
    print('all_info')
    pprint.pprint(all_info)

    # extract the list of participants and their emails
    # as a list of tuples (Name, Email)
    participants = []
    for person_info in all_info:
        if strtobool(person_info[game_datetime]):
            # this person is participating
            participants.append((person_info['Name'], person_info['Email']))

    pprint.pprint("There are " + str(len(participants)) + " taking part")
    return participants

if __name__ == '__main__':

    import sys
    import argparse
    import ast

    # create the top-level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # create the parser for the start function
    start_parser = subparsers.add_parser('start')
    start_parser.set_defaults(function = start)

    # create the parser for the finish function
    finish_parser = subparsers.add_parser('finish')
    finish_parser.set_defaults(function = finish)

    # parse the arguments
    arguments = parser.parse_args()
    arguments = vars(arguments) #convert from Namespace to dict

    #attempt to extract and then remove the function entry
    try:
        function_to_call = arguments['function']
    except KeyError:
        print ("You need a function name. Please type -h to get help")
        sys.exit()
    else:
        #remove the function entry as we are only passing arguments
        del arguments['function']

    if arguments:
        #remove any entries that have a value of 'None'
        #We are *assuming* that these are optional
        #We are doing this because we want the function definition to define
        #the defaults (NOT the function call)
        arguments = { k : v for k,v in arguments.items() if v is not None }

        #alter any string 'True' or 'False' to bools
        arguments = { k : ast.literal_eval(v) if v in ['True','False'] else v
                                              for k,v in arguments.items() }

    result = function_to_call(**arguments) #note **arguments works fine for empty dict {}

    print (result)
