from django.shortcuts import render
from django.contrib.auth.decorators import login_required
#for Meetup
import requests
from django.http import HttpResponse, HttpRequest
from django.conf import settings
from urllib.parse import urlparse


# Create your views here.

# @login_required
def index(request):
    context = {}
    return render(request, "index.html", context)

def event_page(request):
    return render(request, 'event_page.html')


def about_page(request):
    return render(request, 'about_page.html')

# REDIRECT_URI = 'https://pizzapy.ph/events/pizzapy-ph'
def get_redirect_uri(request):
    current_location = request.build_absolute_uri()
    parsed_url = urlparse(current_location)
    path = parsed_url.path.rstrip('/')  # Remove trailing slash if any
    parts = path.split('/')  # Split the path by "/"
    if len(parts) >= 3:  # Ensure that there are at least 3 parts
        return '/'.join(parts[:3])  # Join the first three parts
    else:
        return None  # Unable to determine the correct URI

# def get_access_token(code):
#     token_url = 'https://secure.meetup.com/oauth2/access'
#     payload = {
#         'client_id': settings.OAUTH_KEY,
#         'client_secret': settings.OAUTH_SECRET,
#         'grant_type': 'authorization_code',
#         'redirect_uri': REDIRECT_URI,
#         'code': code
#     }
#     response = requests.post(token_url, data=payload)
#     if response.status_code == 200:
#         return response.json().get('access_token')
#     else:
#         return None
def get_access_token(request, code):
    REDIRECT_URI = get_redirect_uri(request)
    if not REDIRECT_URI:
        return None  # Unable to determine redirect URI
    token_url = 'https://secure.meetup.com/oauth2/access'
    payload = {
        'client_id': settings.OAUTH_KEY,
        'client_secret': settings.OAUTH_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        return None

def fetch_events(query, token, variables):
    url = 'https://api.meetup.com/gql'
    headers = {"Authorization": "Bearer " + token}
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def extract_events(data, event_type):
    return data.get("data", {}).get("groupByUrlname", {}).get(event_type, {}).get("edges", [])

def render_events(request, event_type, query, group_name):
    token = request.token
    if not token:
        return HttpResponse("Failed to retrieve access token", status=400)
    
    variables = {"urlname": group_name}
    data = fetch_events(query, token, variables)
    
    if data:
        events = extract_events(data, event_type)
        return render(request, 'events.html', {'events': events})
    else:
        return HttpResponse("Failed to retrieve events", status=400)

def get_past_events(request, group_name):
    past_events_query = """
    query ($urlname: String!) {
      groupByUrlname(urlname: $urlname) {
        id
        pastEvents(input: { first: 3 }, sortOrder: DESC){
            count,
            pageInfo {
                    endCursor
                },
                  edges {
            node {
              id
              title
              description
              eventType
              images {
                id
                baseUrl
                preview
                source
              }
              venue {
                address
                city
                postalCode
              }
            }
          }
        }
      }
    }
    """
    return render_events(request, "pastEvents", past_events_query, group_name)

def get_upcoming_events(request, group_name):
    upcoming_events_query = """
    query ($urlname: String!) {
        groupByUrlname(urlname: $urlname) {
            id,
            upcomingEvents(input: { first: 3 }, sortOrder: DESC){
                count,
                pageInfo {
                        endCursor
                    },
                    edges {
                node {
                id
                title
                description
                eventType
                venue {
                    address
                    city
                    postalCode
                }
                }
            }
            }
        }
        }
    """
    return render_events(request, "upcomingEvents", upcoming_events_query, group_name)
