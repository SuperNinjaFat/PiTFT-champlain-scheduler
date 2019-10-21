from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


#  Adapted from https://developers.google.com/calendar/quickstart/python
def pullCalendarClass():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.today().isoformat() + 'Z' # 'Z' indicates UTC time
    tonight = datetime.datetime.combine(datetime.datetime.utcnow(), datetime.datetime.max.time()).isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting upcoming classes for today')
    calendars = service.calendarList().list().execute()  # grab all calendars
    calID = None
    for calendar in calendars['items']:
        if "Class Times" in calendar['summary']:
            calID = calendar['id']
    if not calID:
        print("No \'Class Times\' calendar found for user. Please designate class times with a calendar that includes \'Class Times\' in the title.")
        return None, "No \'Class Times\' calendar found!"
    else:
        cal_day_result = service.events().list(calendarId=calID,
                                               maxResults=1,  # Only retrieve one class.
                                               timeMin=now, timeMax=tonight,
                                               singleEvents=True,
                                               orderBy="startTime").execute()

        event = cal_day_result['items'][0]  # Only retrieve one class from the list.

        if not event:
            print('No upcoming class found.')
            return None, "No upcoming classes!"
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start[:19].strip(), event['summary'])
        return datetime.datetime.strptime(start[:19].strip(), "%Y-%m-%dT%H:%M:%S"), event['summary']
