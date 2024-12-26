import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt 
from django.conf import settings
from .models import UserResponse
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Path to your service account key file
SERVICE_ACCOUNT_FILE = os.path.join(settings.BASE_DIR, 'data', 'puzzles-2-puzzle-u.json')

# The ID of your Google Sheet (from its URL)
SPREADSHEET_ID = '1xq4gSQuMZOukHIkNDXW7SSSJixLCQSO9V1XKKxv6TYU'

# The range where data will be appended
RANGE_NAME = 'Sheet1!A1:F1'

@csrf_exempt
def submit_response(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            email = data.get('email')
            response = data.get('response')
            puzzle_id = data.get('puzzleId')
            
            # Check if the response is correct
            correct_answer = '42'
            is_correct = (response == correct_answer)
            
            # Create or update the UserResponse object
            user_response, created = UserResponse.objects.get_or_create(
                name=name,
                email=email,
                puzzle_id=puzzle_id,
                defaults={
                    'response': response,
                    'is_correct': is_correct,
                    'attempts': 1,
                    'puzzles_solved': 1 if is_correct else 0,
                    'solved': is_correct
                }
            )

            if not created:  # User already exists
                if user_response.solved:
                    return JsonResponse({'message': 'Puzzle already solved'}, status=200)
                if user_response.attempts >= 3:
                    return JsonResponse({'message': 'Max attempts reached'}, status=400)

                # Update the record
                user_response.attempts += 1
                user_response.response = response
                if is_correct:
                    user_response.is_correct = True
                    user_response.solved = True
                    user_response.puzzles_solved += 1
                user_response.save()

            # Send data to Google Sheets
            credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)
            service = build('sheets', 'v4', credentials=credentials)
            sheet = service.spreadsheets()

            # Prepare the data to append
            values = [
                [name, email, response, puzzle_id, is_correct, user_response.attempts]
            ]
            body = {'values': values}

            # Append data to the sheet
            result = sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption='RAW',
                body=body
            ).execute()

            return JsonResponse({'message': 'Response recorded and sent to Google Sheets'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405) 

def get_leaderboard_data(request):
    # Set up Google Sheets API credentials
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Build the Sheets API service
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    # Fetch the data from the specified range
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    # Prepare the data for the leaderboard
    leaderboard = []
    if values:
        for row in values[1:]:  # Skip the header row
            leaderboard.append({
                'name': row[0],  # Column A: Name
                'puzzles_solved': int(row[3]),  # Column D: Puzzles Solved
                'attempts': int(row[5]) if len(row) > 5 else 0  # Column F: Attempts
            })

    # Return the data as JSON
    return JsonResponse({'leaderboard': leaderboard})
