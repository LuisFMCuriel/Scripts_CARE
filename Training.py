#Here, we import and enable Tensorflow 1 instead of Tensorflow 2.
get_ipython().system('pip install tifffile')
get_ipython().system('pip install csbdeep')
get_ipython().system('pip install memory_profiler')
get_ipython().system('pip install tensorflow==1.15.2')
#%tensorflow_version 1.x
import tensorflow as tf
#import tensorflow.compat.v1 as tf
#tf.disable_v2_behavior()
print(tf.__version__)
print("Tensorflow enabled.")


#Here, we import all libraries necessary for this notebook.

import numpy as np
import sys 
import matplotlib.pyplot as plt
from tifffile import imread, imsave
from csbdeep.utils import download_and_extract_zip_file, plot_some, axes_dict, plot_history, Path, download_and_extract_zip_file
from csbdeep.data import RawData, create_patches 
from csbdeep.io import load_training_data, save_tiff_imagej_compatible
from csbdeep.models import Config, CARE
from csbdeep import data
from pathlib import Path
import os, random
import shutil
import pandas as pd
import csv

#%load_ext memory_profiler

print("Depencies installed and imported.")

def Show_loss_function(history):
  '''
  Plot the loss function

  Parameters
  ----------
  history : keras object

  Return
  ----------
  void
  '''
  # Create figure framesize
  errorfigure = plt.figure(figsize=(16,5))

  # Choose the values you wish to compare. 
  # For example, If you wish to see another values, just replace 'loss' to 'dist_loss'
  plot_history(history,['loss','val_loss']); 
  errorfigure.savefig(model_path+'/training evaluation.tif') 

  # convert the history.history dict to a pandas DataFrame:     
  hist_df = pd.DataFrame(history.history) 

  # The figure is saved into content/ as training evaluation.csv (refresh the Files if needed). 
  RESULTS = model_path+'/training evaluation.csv'
  with open(RESULTS, 'w') as f:
      for key in hist_df.keys():
          f.write("%s,%s\n"%(key,hist_df[key]))
  print("Remember you can also plot:")
  print(history.history.keys())

def Show_patches(X,Y):
  '''
  Visualize patches

  Parameters
  ----------
  X : (np.ndarray) array of patches
  Y : (np.ndarray) array of patches

  Returns
  ---------
  void

  '''
  #plot of training patches.
  plt.figure(figsize=(12,5))
  plot_some(X[:5],Y[:5])
  plt.suptitle('5 example training patches (top row: source, bottom row: target)');

  #plot of validation patches
  plt.figure(figsize=(12,5))
  plot_some(X_val[:5],Y_val[:5])
  plt.suptitle('5 example validation patches (top row: source, bottom row: target)');


def train( Training_source = ".",
                Training_target = ".",
                model_name = "No_name",
                model_path = ".",
                Visual_validation_after_training = True,
                number_of_epochs =  100,
                patch_size =  64,
                number_of_patches =   10,
                Use_Default_Advanced_Parameters = True,
                number_of_steps =  300,
                batch_size =  32,
                percentage_validation =  15):
  OutputFile = Training_target+"/*.tif"
  InputFile = Training_source+"/*.tif"
  base = "/content/"
  training_data = base+"/my_training_data.npz"
  if (Use_Default_Advanced_Parameters): 
    print("Default advanced parameters enabled")
    batch_size = 64
    percentage_validation = 10

  percentage = percentage_validation/100
  #here we check that no model with the same name already exist, if so delete
  if os.path.exists(model_path+'/'+model_name):
    shutil.rmtree(model_path+'/'+model_name)

  # The shape of the images.
  x = imread(InputFile)
  y = imread(OutputFile)

  print('Loaded Input images (number, width, length) =', x.shape)
  print('Loaded Output images (number, width, length) =', y.shape)
  print("Parameters initiated.")

  # This will display a randomly chosen dataset input and output
  random_choice = random.choice(os.listdir(Training_source))
  x = imread(Training_source+"/"+random_choice)

  os.chdir(Training_target)
  y = imread(Training_target+"/"+random_choice)

  f=plt.figure(figsize=(16,8))
  plt.subplot(1,2,1)
  plt.imshow(x, interpolation='nearest')
  plt.title('Training source')
  plt.axis('off');

  plt.subplot(1,2,2)
  plt.imshow(y, interpolation='nearest')
  plt.title('Training target')
  plt.axis('off');

  #protection for next cell
  if (Visual_validation_after_training):
    Cell_executed = 0

  if (Visual_validation_after_training):
    if Cell_executed == 0 :

  #Create a temporary file folder for immediate assessment of training results:
  #If the folder still exists, delete it
      if os.path.exists(Training_source+"/temp"):
        shutil.rmtree(Training_source+"/temp")

      if os.path.exists(Training_target+"/temp"):
        shutil.rmtree(Training_target+"/temp")

      if os.path.exists(model_path+"/temp"):
        shutil.rmtree(model_path+"/temp")

  #Create directories to move files temporarily into for assessment
      os.makedirs(Training_source+"/temp")
      os.makedirs(Training_target+"/temp")
      os.makedirs(model_path+"/temp")
      #list_source = os.listdir(os.path.join(Training_source))
      #list_target = os.listdir(os.path.join(Training_target))
  #Move files into the temporary source and target directories:
      shutil.move(Training_source+"/"+random_choice, Training_source+'/temp/'+random_choice)
      shutil.move(Training_target+"/"+random_choice, Training_target+'/temp/'+random_choice)

  # RawData Object

  # This object holds the image pairs (GT and low), ensuring that CARE compares corresponding images.
  # This file is saved in .npz format and later called when loading the trainig data.

  raw_data = data.RawData.from_folder(
      basepath=base,
      source_dirs=[Training_source], 
      target_dir=Training_target, 
      axes='CYX', 
      pattern='*.tif*')

  X, Y, XY_axes = data.create_patches(
      raw_data, 
      patch_filter=None, 
      patch_size=(patch_size,patch_size), 
      n_patches_per_image=number_of_patches)

  print ('Creating 2D training dataset')
  training_path = model_path+"/rawdata"
  rawdata1 = training_path+".npz"
  np.savez(training_path,X=X, Y=Y, axes=XY_axes)

  # Load Training Data
  (X,Y), (X_val,Y_val), axes = load_training_data(rawdata1, validation_split=percentage, verbose=True)
  c = axes_dict(axes)['C']
  n_channel_in, n_channel_out = X.shape[c], Y.shape[c]
  #Show_patches(X,Y)

  #Here we automatically define number_of_step in function of training data and batch size
  if (Use_Default_Advanced_Parameters): 
    number_of_steps= int(X.shape[0]/batch_size)+1

  print(number_of_steps)

  #Here we create the configuration file

  config = Config(axes, n_channel_in, n_channel_out, probabilistic=False, train_steps_per_epoch=number_of_steps, train_epochs=number_of_epochs, unet_kern_size=5, unet_n_depth=3, train_batch_size=batch_size, train_learning_rate=0.0004)

  print(config)
  vars(config)

  # Compile the CARE model for network training
  model_training= CARE(config, model_name, basedir=model_path)


  if (Visual_validation_after_training):
    Cell_executed = 1


  import time
  start = time.time()

  #@markdown ##Start Training

  # Start Training
  history = model_training.train(X,Y, validation_data=(X_val,Y_val))

  print("Training, done.")

def Predict_a_image:
  if (Visual_validation_after_training):
    if Cell_executed == 1:
  #Here we predict one image
      validation_image = imread(Training_source+"/temp/"+random_choice)
      validation_test = model_training.predict(validation_image, axes='YX')
      os.chdir(model_path+"/temp/")
      imsave(random_choice+"_predicted.tif",validation_test)
  #Source
      I = imread(Training_source+"/temp/"+random_choice)
  #Target
      J = imread(Training_target+"/temp/"+random_choice)
  #Prediction
      K = imread(model_path+"/temp/"+random_choice+"_predicted.tif")
  #Make a plot
      f=plt.figure(figsize=(24,12))
      plt.subplot(1,3,1)
      plt.imshow(I, interpolation='nearest')
      plt.title('Source')
      plt.axis('off');

      plt.subplot(1,3,2)
      plt.imshow(J, interpolation='nearest')
      plt.title('Target')
      plt.axis('off');

      plt.subplot(1,3,3)
      plt.imshow(K, interpolation='nearest')
      plt.title('Prediction')
      plt.axis('off');

  #Move the temporary files back to their original folders
      shutil.move(Training_source+'/temp/'+random_choice, Training_source+"/"+random_choice)
      shutil.move(Training_target+'/temp/'+random_choice, Training_target+"/"+random_choice)

  #Delete the temporary folder
      shutil.rmtree(Training_target+'/temp')
      shutil.rmtree(Training_source+'/temp')

  #protection against removing data
    Cell_executed = 0


  # Displaying the time elapsed for training
  dt = time.time() - start
  min, sec = divmod(dt, 60) 
  hour, min = divmod(min, 60) 
  print("Time elapsed:",hour, "hour(s)",min,"min(s)",round(sec),"sec(s)")

  #Show_loss_function(history)
  



