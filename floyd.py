get_ipython().system('pip install tifffile')
get_ipython().system('pip install imreg')
import subprocess
import os
import numpy as np
import sys
import shutil
from tifffile import imread, imsave
from imreg import translation


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

def Register(filename,path_r,path_Ms,path_Ls,cont):
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
	#imsave(os.path.join(str(path_Ms),"P_" + filename), high[:,:,:])
	#imsave(os.path.join(str(path_Ls),"P_" + filename),low[:,:,:])
	for i in range(0,number):
		#Save the ith image, upload it with a number in the name and delete it
		#High exposure image
		print(cont+i+1)
		imsave(os.path.join(str(path_Ms),str(cont+i+1)+".tif"),high[i,:,:]) #Save it
		#Upload(S,M_id,os.path.join(str(path_Ms),str(cont+i+1)+".tif"), str(cont+i+1)+".tif") #Upload it
		#os.remove(os.path.join(str(path_Ms),str(cont+i+1)+".tif")) #Delete it
		#Low exposure image
		imsave(os.path.join(str(path_Ls),str(cont+i+1)+".tif"),low[i,:,:]) #Save it
		#Upload(S,L_id,os.path.join(str(path_Ls),str(cont+i+1)+".tif"), str(cont+i+1)+".tif") #Upload it
		#os.remove(os.path.join(str(path_Ls),str(cont+i+1)+".tif")) #Delete it
		img_in_stack += 1
	cont += img_in_stack
	return cont

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
	Base_dir = os.path.join(sys.path[0],"Images")# + r"\\" + "Images"
	Low_dir = "Low"
	Max_dir = "Max"
	Create_my_dir(Low_dir)
	Create_my_dir(Max_dir)

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
				cont = Register(filename, Base_dir, Max_dir, Low_dir, cont) #This is the counther for the name of the images
				file = open("Images.txt", "a").write(filename + "\n") #Once you uploaded the file, take note of that image

		#After process the images update the information for the counter
		file = open("cont.txt","w").write(str(cont))

	subprocess.call("pip install floyd-cli")
	subprocess.call("floyd login")
	os.chdir("Low")
	print("Insert the name dataset in floydhub for the low SNR images")
	Ans = input()
	subprocess.call("floyd data init nmsblab/" + Ans)
	subprocess.call("floyd data upload")
	os.chdir(sys.path[0])
	os.chdir("Max")
	print("Insert the name dataset in floydhub for the high SNR images")
	Ans = input()
	subprocess.call("floyd data init nmsblab/" + Ans)

	subprocess.call("floyd data upload")

	flag = True
	while flag == True:
		print("Do you want me to erase the files in your local computer? (y/n)")
		erase = input()

		if erase == "y":
			shutil.rmtree(Low_dir)
			shutil.rmtree(Max_dir)
			flag = False
		if erase == "n":
			print("Keeping the files")
			flag = False
		print("Input not understood")
Main()