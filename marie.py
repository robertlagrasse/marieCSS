# Author: Robert LaGrasse - robert.lagrasse@gmail.com
# ============================================
# DISCLAIMER:
#
# The code provided in this file is for educational and/or experimental purposes only.
# It is not intended for use in production environments or for any commercial purpose.
#
# The author(s) of this code are not responsible for any consequences, direct or indirect,
# resulting from the use or misuse of this code.
#
# Use at your own risk.
# ============================================


# The Cloud Storage Service relies on client_credentials authorization
# You need a bearer token from the auth server to make CSS API requests

# The skunkworksCSS library was created to provide a simple set of interfaces
# for the CSS API. It contains a set of functions that manage the API calls,
# and return data to your program or write it to a file.

# These code samples demonstrate each of the functions, and are easy
# blueprints to modify for your own purposes.


import json
import sys
import time
import random


from skunkworksAuth import clientCredentialsAuthorize
from skunkworksCSS import getCSS_ObjectsList
from skunkworksCSS import getCSS_ObjectMetaData
from skunkworksCSS import initiateCSS_BulkDownload
from skunkworksCSS import getCSS_BulkStatus
from skunkworksCSS import getCSS_BulkContent
from skunkworksCSS import clearCSS_BulkRequests
from skunkworksCSS import getCSS_ObjectContent

# The credentials generated in the Admin console should live in the file specified here.
# Use an external file like this, or an enviornment variable. Don't put keys in your code.

credentials = 'creds.json'

# Feed the credentials to the clientCredentialsAuthorize() function, which will
# use them to build a request to the authentication server. If the request is successful,
# a bearer token in returned. The accompanies any requests to the CSS endpoint.

response = clientCredentialsAuthorize(credentials=credentials)

if 'Error' in response.keys():
    print(json.dumps(response, indent=4, sort_keys=True))
    print('There was an error authenticating')
    exit()

token = response['access_token']
expiration = int(response['issued_at']) + int(response['expires_in'])


## Ask CSS for a list of objects using getCSS_ObjectsList(). Filtering is available here.
## I'm filtering here by type (callrecording), and looking for a +1 in the
## name of the recorded object. The name piece is looking for the +1 that
## prepends the telephone number. It's a hack, but it saves you parsing a longer
## list returned by the server which would include extension to extension calls.

objectList = getCSS_ObjectsList(
    token, filter='type==callrecording,name==+1', sortDirection='DESC')
print('getCSS_ObjectsList returned', len(objectList), 'items.')

# Individual objects can be downloaded by passing a token and an object id  to getCSS_ObjectContent()
# If you're downloading multiple objects, it's more efficient to pass a token and a list
# of objects to initiateCSS_BulkDownload(). The server will zip the files and make them
# available to download in a single request. The process is detailed below...


################################################################################
# BULK DOWNLOADS (Multi Stage Process!)
# How bulk downloads work:
# Identify the object id for each object you want, and add it to a list []
# Send a token and the list to the API using initiateCSS_BulkDownload()
# initiateCSS_BulkDownload will return list of json objects formatted like this:
# [{'zipName': 'cd209587-b204-4934-b879-d1e2920ca2a3.zip', 'status': 'DONE'}, {'zipName': 'c59920c2-dd89-49db-9e09-bf901f81d2bd.zip', 'status': 'DONE'}, {'zipName': 'f9fa7e80-d220-4bc0-83c1-dd4697da4935.zip', 'status': 'NOT_STARTED'}]
# each of these is a zipfile and a status.
# It takes time to generate the zip file itself.
# Generate the request
# Wait until status on all files is DONE
# Retrieve each file using getCSS_BulkContent()
# Clean up after yourself
# Downloading the zip file doesn't remove it from the server.
# Pass your token to clearCSS_BulkRequests()
# Wait
# Check Status with getCSS_BulkStatus()

################################################################################

# identify the objects to download
if len(objectList) > 0:
    ids = []
    for index, item in enumerate(objectList):
        ids.append(objectList[index]['id'])

# initiate the download request
    print('\n Initiating bulk download request.\n')
    status = initiateCSS_BulkDownload(token, ids)
    print('API Returned:\n')
    print(json.dumps(status.text, indent=4, sort_keys=True))

# periodically check on the status of your download request
print('Waiting for zipfiles...\n')
unfinished = True
while unfinished:
    time.sleep(1)
    unfinished = False
    response = json.loads(getCSS_BulkStatus(token).text)

    for item in response:
        print(item['zipName'], item['status'])
        if item['status'] != "DONE":
            unfinished = True

# when your files are ready, retrieve them
print('Zip file(s) ready on server. Initiating download.')
for item in response:
    print('Downloading: ' + item['zipName'])
    filesize = getCSS_BulkContent(token, item['zipName'], item['zipName'])
    print('Complete. Filesize: ' + str(filesize))

# clean up the zip files from the server
print('Downloads complete. Clearing bulk requests from server.')
response = clearCSS_BulkRequests(token)
print(response)

print('Finished.')
