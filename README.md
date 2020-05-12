# Scripts_CARE
Automatization of the entire protocols for the preprocessing and training of the model
The script uses the DRIVE API to communicate with the cloud and store the preprocessed images. This is going to help us to have a backup and to set everything before the training. 
The script is going to process all the images in a folder called "Images". Therefore in your working directory you are going to have the script and the "Images" folder (inside of this are going to be the images).
The script is going to generate the credentials.json (for the authentication in drive), cont.txt, ID.txt and Images.txt.
The cont.txt is the ith image that you stored in the last time you run this script. The ID.txt is going to store the ID of the directory in the cloud and Images.txt contains all the images that you already processed.

CAREFULL
If you delete the folders in Google Drive, please remove the ID.txt file, so the script creates a new location to store your data.
