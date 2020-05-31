#!/usr/bin/env python
# coding: utf-8

# In[1]:

#!/bin/bash
from __future__ import print_function
import pickle
get_ipython().system('pip install tifffile')
get_ipython().system('pip install imreg')
get_ipython().system('pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib')
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload
from tifffile import imread, imsave
from imreg import translation
import os
import webbrowser
import time
import sys
import numpy as np

# Permission for the cloud
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']


def Create_my_dir(new_path): #Create paths (windows os)
    """
    Create a new directory

    Parameters
    ----------
    new_path : (str) Path where the new dir is going to be created

    Returns
    -------
    Void
    """
    if not os.path.exists(new_path):
        os.makedirs(new_path);

def Register(filename,path_r,path_Ms,path_Ls,M_id,L_id,cont,S):
	"""
    Register and upload images to Drive

    Parameters
    ----------
    filename
    filename : (str) name of the image to be processed
	path_r : (str) Path where the images are going to be readed
	path_Ms : (str) Path where the target images are 
	path_Ls : (str) Path where the noisy images are
	M_id : (str) ID of the folder in Drive where the target images are going to be saved
	L_id : (str) ID of the folder in Drive where the noisy images are going to be saved
	cont : (int) counter of the images uploaded
	S : (str) credentials for the cloud services
    Returns
    -------
    cont : (int) counter of the images uploaded
    """
	img_in_stack = 0;
	print(os.path.join(path_r,filename))
	Image = imread(os.path.join(path_r,filename))
	pixels_h = 24
	number,height,widht = Image.shape
	half_image = int(height/2)
	register, t1 = translation(Image[0,pixels_h:half_image,:], Image[0,pixels_h+half_image:,:]) #Compare the first frame of the stack and find registration number
	print(register)
	low_r = np.zeros((number,half_image,widht),dtype=np.uint16)
	low = np.zeros((number,half_image-pixels_h,widht),dtype=np.uint16)
	high = np.zeros((number,half_image-pixels_h,widht),dtype=np.uint16)
	high_r = np.zeros((number,half_image,widht), dtype=np.uint16)
	high[:,:,:] = Image[:,pixels_h:half_image,:]
	low[:,:,:] = Image[:,half_image+pixels_h:,:]
	print(Image[:,half_image:,:].shape)
	if register == 0:
		low_r[:,register:,:] = Image[:,half_image:,:]
		low[:,:,:] = low_r[:,pixels_h:,:]
	elif register < 0:
		high_r[:,-register:,:] = Image[:,-register:half_image,:]
		high[:,:,:] = high_r[:,pixels_h:,:]
	else:
		low_r[:,register:,:] = Image[:,half_image:-register,:]
		low[:,:,:] = low_r[:,pixels_h:,:]
	imsave(os.path.join(str(path_Ms),"P_" + filename), high[:,:,:])
	imsave(os.path.join(str(path_Ls),"P_" + filename),low[:,:,:])
	for i in range(0,number):
		#Save the ith image, upload it with a number in the name and delete it
		#High exposure image
		print(cont+i+1)
		imsave(os.path.join(str(path_Ms),str(cont+i+1)+".tif"),high[i,:,:]) #Save it
		Upload(S,M_id,os.path.join(str(path_Ms),str(cont+i+1)+".tif"), str(cont+i+1)+".tif") #Upload it
		os.remove(os.path.join(str(path_Ms),str(cont+i+1)+".tif")) #Delete it
		#Low exposure image
		imsave(os.path.join(str(path_Ls),str(cont+i+1)+".tif"),low[i,:,:]) #Save it
		Upload(S,L_id,os.path.join(str(path_Ls),str(cont+i+1)+".tif"), str(cont+i+1)+".tif") #Upload it
		os.remove(os.path.join(str(path_Ls),str(cont+i+1)+".tif")) #Delete it
		img_in_stack += 1
	cont += img_in_stack
	return cont

def Credentials(): 
	"""
    Generate the credentials.json, so the next time you upload images you don't have to authenticate

    Parameters
    ----------
    void

    Returns
    -------
    void
    """
	if not os.path.isfile("credentials.json"):
		webbrowser.open('https://developers.google.com/drive/api/v3/quickstart/python?authuser=2')
		credentials = os.path.isfile("credentials.json")
		while not credentials:
			time.sleep(1)
			credentials = os.path.isfile("credentials.json")

def Authenticate():
	"""
    The file token.pickle stores the user's access and refresh tokens, and is
    created automatically when the authorization flow completes for the first
    time.

    Parameters
    ----------
    void

    Returns
    -------
    servide : (str) credentials for the cloud
    """
	creds = None

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

def Drive_Directories(service,Ans_name):
	"""
    Creates directories in cloud
    Here we create 3 directories:
    The first one is the father, which contains the other 2 folders (for target images and noisy images)

    Parameters
    ----------
    service : (str) Credentials for the cloud

    Returns
    -------
    servide : (str) credentials for the cloud
    Folder_L.get('id') : (str) id noisy images directory
    Folder_M.get('id') : (str) id target images directory
    """

	file_metadata = {
    'name': Ans_name, #This is the name of the folder 
    'mimeType': 'application/vnd.google-apps.folder'
    }
	Folder_Father = service.files().create(body=file_metadata,
                                    fields='id').execute()
	print('Folder ID: %s' % Folder_Father.get('id'))
    #The second folder is the folder which contains the noisy images
	file_metadata = {
    'name': 'Low', #This is the name of the folder
    'parents': [Folder_Father.get('id')],
    'mimeType': 'application/vnd.google-apps.folder'
    }
	Folder_L = service.files().create(body=file_metadata,
                                    fields='id').execute()
	print('Folder ID: %s' % Folder_L.get('id'))

    #The third folder is the folder which contains the target images
	file_metadata = {
    'name': 'Max', #This is the name of the folder
    'parents': [Folder_Father.get('id')],
    'mimeType': 'application/vnd.google-apps.folder'
    }
	Folder_M = service.files().create(body=file_metadata,
                                    fields='id').execute()
	print('Folder ID: %s' % Folder_M.get('id'))
    #We return the id folders because we want to create them only once, so the next run
	#we don't create them again
	return service, Folder_L.get('id'), Folder_M.get('id')

def Upload(service,F_id, path, Name):
	"""
    Upload images

    Parameters
    ----------
    service : (str) Credentials for the cloud
    F_id : (str) ID of the directory where the image is going to be stored
    path : (str) Where the image is located
    Name : (str) The name you will use in the cloud for that file

    Returns
    -------
    servide : (str) credentials for the cloud
    Folder_L.get('id') : (str) id noisy images directory
    Folder_M.get('id') : (str) id target images directory
    """
	file_metadata = {
      'name': Name,
        'parents': [F_id]#[folder_id] put them in the correct directory (depending on the folder ID)
    }
	media = MediaFileUpload(path,
                        mimetype='image/tif', chunksize = 5000000000000, #How much data you are going to upload?
                        resumable=True)
	file = service.files().create(body=file_metadata,
                                    media_body=media,
                                    fields='id').execute()
	print ('File ID: %s' % file.get('id'))

def Read_txt_Image(Name):
	"""
    Read .txt file (multiple rows of information)
	This is to know which files have already been processed you write and read this files

    Parameters
    ----------
    Name : (str) Name of the file

    Returns
    -------
    x : (list) Contains the name of the images that you already uploaded
    """
	try:
		with open(Name, 'r') as f: #If the file already exists
			x = f.readlines() #Readd all the rows and put them in a list
	except: 
		with open(Name, 'w') as f: #If the file does not exist
			x = [] #Create an empty list
	return x #This is the list that contains all the information for the file

def Read_txt_cont(Name):
	"""
    Read .txt file (only one row of information)
	This is where the cont variable are stored. This program stores the images with numbers as names: 1.tif, 2.tif
	this is because the CARE program needs 2 images (target and noisy) to have the same name. The counter
	stores the last number you uploaded in order to keep uploading to the same directory and avoid loss of information 

    Parameters
    ----------
    Name : (str) Name of the file

    Returns
    -------
    x : (int) Contains the number of the last image uploaded
    """
	try:
		with open(Name, 'r') as f: #If the file already exists
			x = f.read() #Read the file
			if x == '': #If the file is empty
				x = 0 #Start on 0
	except: 
		with open(Name, 'w') as f: #If the file does not exist
			x = 0 #Start on 0
	return x #This is the list that contains all the information for the file

def Main():
	#Local Directory part
	Base_dir = os.path.join(sys.path[0],"Images")# + r"\\" + "Images"
	Low_dir = "Low"
	Max_dir = "Max"
	Create_my_dir(Low_dir)
	Create_my_dir(Max_dir)
	Credentials()
	cred = Authenticate() #Get credentials from API Cloud
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
		print("What name would you like to use for your main dir?")
		Ans = input()
		cred, L_id, M_id = Drive_Directories(cred,Ans)
		open("ID.txt", 'w').write(L_id + "\n")
		open("ID.txt", 'a').write(M_id)
	#Read text cont
	Cont = Read_txt_cont("cont.txt");
	cont = int(Cont)
	#Read text Images
	List = Read_txt_Image("Images.txt")
	for filename in os.listdir(Base_dir): 
		if os.path.isdir(filename): #If the file is a directory dont process it
			continue
		else: #If the file is not a directory then process it
			Already_processed = filename + "\n" in List #Then we need to check if the file has alredy ben processed
			if Already_processed: #If the file is alredy in the drive then don't do anythin
				continue
			else: #If not cut, register, detach and upload the images
				cont = Register(filename, Base_dir, Max_dir, Low_dir, M_id, L_id, cont, cred) #This is the counther for the name of the images
				file = open("Images.txt", "a").write(filename + "\n") #Once you uploaded the file, take note of that image

		#After process the images update the information for the counter
		file = open("cont.txt","w").write(str(cont))





#Start
Main()

