#!/usr/bin/env python
# coding: utf-8

# In[1]:

#!/bin/bash
from __future__ import print_function
import pickle
import os.path
get_ipython().system('pip install tifffile')
get_ipython().system('pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib')
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload
from tifffile import imread, imsave
import os
import os.path
from os import path
import sys
import numpy as np

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def createmydir(new_path): #Create paths (windows os)
    if not os.path.exists(new_path):
        os.makedirs(new_path);

def Register(filename,path_r,path_Ms,path_Ls,M_id,L_id,cont,S):
	CONT = 0;
	print(os.path.join(path_r,filename))
	a = imread(os.path.join(path_r,filename))
	pixels_h = 24
	n,h,w = a.shape
	register = 8
	c = int(h/2)
	low_r = np.zeros((n,c,w),dtype=np.uint16)
	low = np.zeros((n,c-pixels_h,w),dtype=np.uint16)
	high = np.zeros((n,c-pixels_h,w),dtype=np.uint16)
	high[:,:,:] = a[:,pixels_h:c,:]
	low_r[:,register:,:] = a[:,c:w-register,:]
	low[:,:,:] = low_r[:,pixels_h:,:]
	imsave(os.path.join(str(path_Ms),filename), high[:,:,:])
	imsave(os.path.join(str(path_Ls),filename),low[:,:,:])
	n,h,w = high.shape
	for i in range(0,n):
		#Save the ith image, upload it with a number in the name and delete it
		#High exposure image
		imsave(os.path.join(str(path_Ms),str(cont+i+1)+".tif"),high[i,:,:]) #Save it
		Upload(S,M_id,os.path.join(str(path_Ms),str(cont+i+1)+".tif"), str(cont+i+1)+".tif") #Upload it
		os.remove(os.path.join(str(path_Ms),str(cont+i+1)+".tif")) #Delete it 
		#Low exposure image
		imsave(os.path.join(str(path_Ls),str(cont+i+1)+".tif"),low[i,:,:]) #Save it
		Upload(S,L_id,os.path.join(str(path_Ls),str(cont+i+1)+".tif"), str(cont+i+1)+".tif") #Upload it
		os.remove(os.path.join(str(path_Ls),str(cont+i+1)+".tif")) #Delete it
		CONT += 1
	cont += CONT
	return cont


def Authenticate():

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    #Authentication part
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

    service = build('drive', 'v3', credentials=creds)
    return service

def Drive_Directories(service):
    #Creates directories
    ################################################
    
    file_metadata = {
    'name': 'Invoices', #This is the name of the folder 
    'mimeType': 'application/vnd.google-apps.folder'
    }
    Folder_Father = service.files().create(body=file_metadata,
                                    fields='id').execute()
    print('Folder ID: %s' % Folder_Father.get('id'))

    file_metadata = {
    'name': 'Low', #This is the name of the folder
    'parents': [Folder_Father.get('id')],
    'mimeType': 'application/vnd.google-apps.folder'
    }
    Folder_L = service.files().create(body=file_metadata,
                                    fields='id').execute()
    print('Folder ID: %s' % Folder_L.get('id'))

    file_metadata = {
    'name': 'Max', #This is the name of the folder
    'parents': [Folder_Father.get('id')],
    'mimeType': 'application/vnd.google-apps.folder'
    }
    Folder_M = service.files().create(body=file_metadata,
                                    fields='id').execute()
    print('Folder ID: %s' % Folder_M.get('id'))

    return service, Folder_L.get('id'), Folder_M.get('id')

def Upload(service,F_id, path, Name):
    #Upload files
    ################################################
    file_metadata = {
      'name': Name,
        'parents': [F_id]#[folder_id]
    }
    media = MediaFileUpload(path,
                        mimetype='image/tif',
                        resumable=True)
    file = service.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id').execute()
    print ('File ID: %s' % file.get('id'))

def Read_txt_Image(Name): #To know which files have already been processed you write and read this files
	try:
		with open(Name, 'r') as f: #If the file already exists
			x = f.readlines()
	except: 
		with open(Name, 'w') as f: #If the file does not exist
			#x = f.read()
			x = []
	return x #This is the list that contains all the information for the file

def Read_txt_cont(Name):
	try:
		with open(Name, 'r') as f: #If the file already exists
			x = f.read()
	except: 
		with open(Name, 'w') as f: #If the file does not exist
			x = 0#f.read()
	return x #This is the list that contains all the information for the file


#Local Directory part
R = sys.path[0] + r"\\" + "Images"
L = "Low"
M = "Max"
createmydir(L)
createmydir(M)
S = Authenticate() #Get credentials from API Cloud
#Drive Directory part
#We want that this path is created only once, so we need to keep a track of the Direcotrie's ID
#If you delete handly the directory  in the cloud, please remove the file "ID.txt"
if os.path.isfile("ID.txt"): #If the file already exists
	with open("ID.txt", 'r') as f: 
		x = f.readlines()
	L_id = x[0]
	L_id = L_id[:-1]
	print(L_id)
	M_id = x[1]
	print(M_id)
else: #If the file does not exist
	S, L_id, M_id = Drive_Directories(S)
	open("ID.txt", 'w').write(L_id + "\n")
	open("ID.txt", 'a').write(M_id)
#Read text cont
Cont = Read_txt_cont("cont.txt");
cont = int(Cont)
#Read text Images
List = Read_txt_Image("Images.txt")
for filename in os.listdir(R): 
	if os.path.isdir(filename): #If the file is a directory dont process it
		continue
	else: #If the file is not a directory then process it
		Already_processed = filename + "\n" in List #Then we need to check if the file has alredy ben processed
		if Already_processed: #If the file is alredy in the drive then don't do anythin
			continue
		else: #If not cut, register, detach and upload the images
			cont = Register(filename, R, M, L, M_id, L_id, cont, S) #This is the counther for the name of the images
			file = open("Images.txt", "a").write(filename + "\n") #Once you uploaded the file, take note of that image

#After process the images update the information for the counter
file = open("cont.txt","w").write(str(cont))
#Uploading files
#Upload(S,L_id,M_id,"1.tif")

