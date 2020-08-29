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
from collections import deque
from itertools import chain
import datetime as dt
import gspread
import yagmail
import keyring

CQ_HOME_BASE_ID = '1uQs36Izy09dv5b5duAUzhA_NZRWqKF-bksNDftwgHfU'
CQ_RESPONSES_ID = '1b43ZbTiReD4oCXrX6odYESkylbe8zmgXVJRSrh2Cz_Y'
CQ_FORM_URL = 'https://forms.gle/CXbFueKHzhi4B2Y96'
START_EMAIL_BODY = '<a href='+CQ_FORM_URL+'>Click me!</a>'
MAX_OK_MISSING = 2 # the # of missing responses we are happy to proceed with
MAX_OK_RANGE = 420 # seconds
DUMMY = ('R2D2', 'C3PO', 'Some Random Planet', \
                    'Beep Beep', 'You are annoying', 'They went to bed for a nap')

gc = gspread.oauth()

def start():

    participants = get_participants()

    # Send the emails, with a link to the form - use yagmail and keyring
    for participant in participants:
        subject = "Hey " + participant[0] + " time to Consequence!"
        content = START_EMAIL_BODY
        email_address = participant[1]
        with yagmail.SMTP('greenbay.graham') as yag:
            yag.send(email_address, subject, content)
            print ("email sent to " + participant[0] + " at " + participant[1])
    return True

def finish():

    # At this point we are 'hoping' that all of the consequence forms
    # have been returned from the participants ...
    
    # we need to allow for the scenario that we get 1 or more, less than
    # we expected. 

    # we won't know whose we haven't got ...

    participants = get_participants()
    total_participants = len(participants)
    # print (participants)

    # get the responses spreadsheet
    responses_spreadsheet = gc.open_by_key(CQ_RESPONSES_ID)

    # Get the first worksheet of the spreadsheet
    responses_worksheet = responses_spreadsheet.get_worksheet(0)

    # get the first column data
    first_column_values = responses_worksheet.col_values(1)
    # pprint.pprint(first_column_values)

    # count usable responses
    from dateutil import parser # had to import here otherwise didn't work
    most_recent_date_time = parser.parse(first_column_values[-1])
    usable_responses_count = 0
    for v in reversed(first_column_values):
        try:
            date_time_of_response = parser.parse(v)
        except parser._parser.ParserError:
            # we have reached the first row
            break
        else:
            response_range = (most_recent_date_time - date_time_of_response).total_seconds()
            # print(response_range)
            if response_range <= MAX_OK_RANGE:
                usable_responses_count = usable_responses_count + 1
            else:
                break
    # print(usable_responses_count)

    # compare usable responses with ones we will use (using)
    if usable_responses_count < total_participants - MAX_OK_MISSING:
        return ("Not enough usable responses")
    elif usable_responses_count > total_participants:
        # possible in testing but very unlikely in production
        print ("WARNING")
        using_responses_count = total_participants
    else:
        using_responses_count = usable_responses_count


    # we can now go to creating and delivering the responses
    all_responses = responses_worksheet.get_all_values()
    # pprint.pprint(all_responses)

    # slice off the usable responses we will be using
    using_responses = all_responses[-using_responses_count:]
    # print(using_responses)

    # transpose the list from per response to per category 
    using_responses_by_category = list(list(a) for a in zip(*using_responses))
    # pprint.pprint(using_responses_by_category)

    # now rotate each category by 1, 2 etc to create the consequences
    consequences = []
    for position, category in enumerate(using_responses_by_category[1:]):
        # not the first column which is just dates
        category_to_rotate = deque(category)
        category_to_rotate.rotate(position)
        consequences.append(list(category_to_rotate))

    # pprint.pprint(consequences)
    consequences = list(zip(*consequences))

    # we could have more participants that consequences
    # in which case add dummy consequences to the consequences (if needed)
    dummy_count = total_participants - len(consequences)
    for x in range(dummy_count):
        # won't run if dummy_count is 0
        consequences.append(DUMMY)
    pprint.pprint(consequences)

    # I am not sure why the consequences are tuples (apart from the Dummy 
    # one(s) if any) because I set that to be a tuple to match
    # However going to convert to lists now to make the final bit easier

    consequences = [list(x) for x in consequences]
    pprint.pprint(consequences)

    # now for emailing
    for participant, consequence in zip(participants, consequences):
        subject = "Hey " + participant[0] + " actions have Consequences!"
        content = create_content(consequence)
        email_address = participant[1]
        with yagmail.SMTP('greenbay.graham') as yag:
            yag.send(email_address, subject, content)
            print ("result email sent to " + participant[0] + " at " + participant[1])
    return True

def create_content(consequence):
    # given the consequence, create the content of the email
    consequence[0] = "'" + consequence[0] + "'" # " ' "
    consequence[1] = "'" + consequence[1] + "'"
    consequence[3] = '"' + consequence[3] + '"' # ' " '
    consequence[4] = '"' + consequence[4] + '"'
    divider = "~"
    content = []

    # Male met Female
    male_met_female_text = consequence[0] + " met " + consequence[1]
    content.append(male_met_female_text)

    #At
    content.append("(at)")
    content.append(consequence[2]) # Where they met
    content.append(divider)

    #Male said to Female
    male_said_to_female_text = consequence[0] + " said to " + consequence[1]
    content.append(male_said_to_female_text)
    content.append(consequence[3]) # Male said to Female
    content.append(divider)

    #Female said to Male
    female_said_to_male_text = consequence[1] + " said to " + consequence[0]
    content.append(female_said_to_male_text)
    content.append(consequence[4]) # Female said to Male
    content.append(divider)

    #Consequence
    content.append("and the Covid Consequence was ...")
    content.append(consequence[5]) # Consequence 
    print(content)
    return content


def get_participants():

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
    #print('')
    #print('all_info')
    #pprint.pprint(all_info)

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
