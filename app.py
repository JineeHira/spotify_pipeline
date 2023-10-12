from flask import Flask, request, url_for, session, redirect, render_template
import time
import pandas as pd
from datetime import datetime
import datetime
import requests
import json
from secrets import clientId, clientSecret, secret_key
import numpy as np
from flask_sqlalchemy import SQLAlchemy

import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__) #creates Flask application


app.secret_key = secret_key 
app.config['SESSION_COOKIE_NAME'] = 'J Cookie' #random string to sign the session cookie
TOKEN_INFO = "token_info"

#set up endpoints
@app.route('/')
def login(): #automatically logs you into spotify & asks for permission
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url) #sends user back to website

@app.route('/redirect')
def redirectPage(): # where spotify sends us back
    sp_oauth = create_spotify_oauth()
    session.clear() # if in the redirected state, we wanted to clear of any other state we were in
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info #saves the token information in the session
    # token info has the refresh token, access token, expires_at, and we just saved it above
    return redirect(url_for('getTracks', _external=True))

@app.route('/getChart')
def getChart():
    try:
        print('works')
    except:
        print("User not logged in")
        return redirect(url_for('getTracks', _external=True))

    chart = session.get("chart")
    
    return chart


@app.route('/getTracks')
def getTracks():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect(url_for('login', _external=False))
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    timestamp_saved = []
    album_names = []
    artist_names = []
    tracks = []

    count = 0
    iteration = 0

    while count < 10:
        date_added = sp.current_user_saved_tracks(limit=50, offset=iteration*50)['items'][count]['added_at']
        album_name = sp.current_user_saved_tracks(limit=50, offset=iteration*50)['items'][count]['track']['album']['name']
        artist_name = sp.current_user_saved_tracks(limit=50, offset=iteration*50)['items'][count]["track"]["artists"][0]["name"]
        songs = sp.current_user_saved_tracks(limit=50, offset=iteration*50)['items'][count]['track']['name']

        timestamp_saved.append(date_added)
        album_names.append(album_name)
        artist_names.append(artist_name)
        tracks.append(songs)

        count +=1

        if len(tracks) == 10:
            break

    saved_dict = {
        "Date Added" : timestamp_saved,
        "Album Name" : album_names,
        "Artist" : artist_names,
        "Song" : tracks
    }
    
    saved_df = pd.DataFrame(saved_dict, columns = ["Date Added", "Album Name", "Artist", "Song"])
    saved_df.index = np.arange(1,len(saved_df)+1)
    chart = saved_df.to_html()

    session["chart"] = chart

    return render_template('tochart.html')

#checks if the access token is expired and if it is, it gets a refreshed one
#checks if there are token data is not redirects to login page
def get_token():
    token_info = session.get(TOKEN_INFO, None) #gets value from the dictionary, if it doesnt exist, return NONE
    if not token_info: #if it is NONE, then do throw an exception
        raise "exception"
    # previously checked if we have token info and they are logged in
    # now check time-stamp on token
    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

clientId = clientId
clientSecret = clientSecret

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=clientId,
        client_secret=clientSecret,
        redirect_uri=url_for('redirectPage', _external=True),
        scope="user-read-recently-played user-read-private user-top-read user-read-currently-playing user-follow-read"
    )