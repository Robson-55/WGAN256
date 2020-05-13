# -*- coding: utf-8 -*-
"""painting_256x256.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lcwuSIWF9HUxNsSnbQytVxOz0rZx7mY_

**Load Google Drive**
"""

#from google.colab import drive
#drive.mount('/content/drive')

"""**Import python libraries**"""
import os
from numpy import expand_dims
from numpy import mean
from numpy import ones
from numpy.random import randn
from numpy.random import randint
from keras.preprocessing.image import ImageDataGenerator
from keras import backend
from keras.optimizers import RMSprop
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Reshape
from keras.layers import Flatten
from keras.layers import Conv2D
from keras.layers import Conv2DTranspose
from keras.layers import LeakyReLU
from keras.layers import BatchNormalization
from keras.initializers import RandomNormal
from keras.constraints import Constraint
from matplotlib import pyplot

"""**Gets color images from a folder of images that is in the same directory as the python file**"""

base_url = "C:/Users/RobeR/Desktop/Tienda Online/Informacion/GAN-Fiverr/" 
data_url = base_url+"Ukiyo_e/" 
output_url = base_url+"output/" 

from os import listdir
from numpy import asarray
from numpy import vstack
from keras.preprocessing.image import img_to_array
from keras.preprocessing.image import load_img
from numpy import savez_compressed

"""**load image from directory, resize to 256x256, convert to grey scale, convert to numpy array**"""

def load_images(path, size=(256,256)):
	data_list = list()
	# enumerate filenames in directory, assume all are images
	for filename in listdir(path):
		# load and resize the image
		pixels = load_img(path + filename, target_size=size, color_mode='rgb') #grayscale
		# convert to numpy array
		pixels = img_to_array(pixels)
		# store
		data_list.append(pixels)
	return asarray(data_list)

"""**Load images from directory**"""

dataA1 = load_images(data_url)
print('Loaded dataA: ', dataA1.shape)

"""**Data Augmentation**"""

train_datagen = ImageDataGenerator(
        rescale=1./255,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True)



"""**Clip model weights to a given hypercube**"""

class ClipConstraint(Constraint):
	# set clip value when initialized
	def __init__(self, clip_value):
		self.clip_value = clip_value

	# clip model weights to hypercube
	def __call__(self, weights):
		return backend.clip(weights, -self.clip_value, self.clip_value)

	# get the config
	def get_config(self):
		return {'clip_value': self.clip_value}

"""**Calculate wasserstein loss**"""

def wasserstein_loss(y_true, y_pred):
	return backend.mean(y_true * y_pred)

"""**Define the standalone critic model**"""

def define_critic(in_shape=(256,256,3)):
	# weight initialization
	init = RandomNormal(stddev=0.02)
	# weight constraint
	const = ClipConstraint(0.01)
	# define model
	model = Sequential()
	# downsample to 14x14
	model.add(Conv2D(64, (4,4), strides=(2,2), padding='same', kernel_initializer=init, kernel_constraint=const, input_shape=in_shape))
	model.add(BatchNormalization())
	model.add(LeakyReLU(alpha=0.2))
	# downsample to 7x7
	model.add(Conv2D(64, (4,4), strides=(2,2), padding='same', kernel_initializer=init, kernel_constraint=const))
	model.add(BatchNormalization())
	model.add(LeakyReLU(alpha=0.2))
	# scoring, linear activation
	model.add(Flatten())
	model.add(Dense(1))
	# compile model
	opt = RMSprop(lr=0.00005)
	model.compile(loss=wasserstein_loss, optimizer=opt)
	return model

"""**Define the standalone generator model**"""

def define_generator(latent_dim):
	# weight initialization
	init = RandomNormal(stddev=0.02)
	# define model
	model = Sequential()
	# foundation for 8x8 image
	n_nodes = 64 * 8 * 8
	model.add(Dense(n_nodes, kernel_initializer=init, input_dim=latent_dim))
	model.add(LeakyReLU(alpha=0.2))
	model.add(Reshape((8, 8, 64)))
	# upsample to 16x16
	model.add(Conv2DTranspose(64, (4,4), strides=(2,2), padding='same', kernel_initializer=init))
	model.add(BatchNormalization())
	model.add(LeakyReLU(alpha=0.2))
	# upsample to 32x32
	model.add(Conv2DTranspose(64, (4,4), strides=(2,2), padding='same', kernel_initializer=init))
	model.add(BatchNormalization())
	model.add(LeakyReLU(alpha=0.2))
  # upsample to 64x64
	model.add(Conv2DTranspose(64, (4,4), strides=(2,2), padding='same', kernel_initializer=init))
	model.add(BatchNormalization())
	model.add(LeakyReLU(alpha=0.2)) 
  # upsample to 128x128
	model.add(Conv2DTranspose(64, (4,4), strides=(2,2), padding='same', kernel_initializer=init))
	model.add(BatchNormalization())
	model.add(LeakyReLU(alpha=0.2))  
  # upsample to 256x256
	model.add(Conv2DTranspose(256, (4,4), strides=(2,2), padding='same', kernel_initializer=init))
	model.add(BatchNormalization())
	model.add(LeakyReLU(alpha=0.2)) 
	# output 256x256x3
	model.add(Conv2D(3, (7,7), activation='tanh', padding='same', kernel_initializer=init))
	return model

"""**Define the combined generator and critic model, for updating the generator**"""

def define_gan(generator, critic):
	# make weights in the critic not trainable
	critic.trainable = False
	# connect them
	model = Sequential()
	# add generator
	model.add(generator)
	# add the critic
	model.add(critic)
	# compile model
	opt = RMSprop(lr=0.00005)
	model.compile(loss=wasserstein_loss, optimizer=opt)
	return model

"""**Select real samples**"""

def generate_real_samples(dataset, n_samples):
	# choose random instances
	ix = randint(0, dataset.shape[0], n_samples)
	# select images
	X = dataset[ix]
	# generate class labels, -1 for 'real'
	y = -ones((n_samples, 1))
	return X, y

"""**Generate points in latent space as input for the generator**"""

def generate_latent_points(latent_dim, n_samples):
	# generate points in the latent space
	x_input = randn(latent_dim * n_samples)
	# reshape into a batch of inputs for the network
	x_input = x_input.reshape(n_samples, latent_dim)
	return x_input

"""**Use the generator to generate n fake examples, with class labels**"""

def generate_fake_samples(generator, latent_dim, n_samples):
	# generate points in latent space
	x_input = generate_latent_points(latent_dim, n_samples)
	# predict outputs
	X = generator.predict(x_input)
	# create class labels with 1.0 for 'fake'
	y = ones((n_samples, 1))
	return X, y

"""**After every 50 epochs, it has to print an image which contains 4x4 image generations (the print is a 1024x1024 image containing 16 images)**"""

import matplotlib

def summarize_performance(step, g_model, latent_dim, n_samples=100):
	# prepare fake examples
	X, _ = generate_fake_samples(g_model, latent_dim, n_samples)
	# scale from [-1,1] to [0,1]
	X = (X + 1) / 2.0
	# plot images
	for i in range(4 * 4):
		# define subplot		
		pyplot.subplot(4, 4, 1 + i)
		# turn off axis
		pyplot.axis('off')
		# plot raw pixel data		
		pyplot.imshow(X[i, :, :, 0], cmap='gray_r')
	# save plot to file
	figure = pyplot.gcf()
	figure.set_size_inches(10,10)
	filename1 = output_url+'generated_plot_50epochs_%04d.png' % (step+1)
	pyplot.savefig(filename1, dpi=100)
	pyplot.close()

"""**After every 100 epochs it has to print an image which contains 8x8 image generations (the print is a 2048x2048 image containing 64 images)**"""

def summarize_performance_100(step, g_model, latent_dim, n_samples=100):
	# prepare fake examples
	X, _ = generate_fake_samples(g_model, latent_dim, n_samples)
	# scale from [-1,1] to [0,1]
	X = (X + 1) / 2.0
	# plot images
	for i in range(8 * 8):
		# define subplot		
		pyplot.subplot(8, 8, 1 + i)
		# turn off axis
		pyplot.axis('off')
		# plot raw pixel data		
		pyplot.imshow(X[i, :, :, 0], cmap='gray_r')
	# save plot to file
	figure = pyplot.gcf()  
	figure.set_size_inches(20,20)
	image_100_epochs = output_url+'generated_plot_100epochs_%04d.png' % (step+1)
	pyplot.savefig(image_100_epochs, dpi=100)
	pyplot.close()
	# save the generator model every 100 epochs
	model_100_epochs = output_url+'model_100epochs_%04d.h5' % (step+1)
	g_model.save(model_100_epochs)
	print('>Saved: %s and %s' % (image_100_epochs, model_100_epochs))

"""**After every 200 epochs it prints a single image generation**"""

def summarize_performance_200(step, g_model, latent_dim, n_samples=100):
	# prepare fake examples
	X, _ = generate_fake_samples(g_model, latent_dim, n_samples)
	# scale from [-1,1] to [0,1]
	X = (X + 1) / 2.0
	# plot images
	for i in range(1 * 1):
		# define subplot		
		pyplot.subplot(1, 1, 1 + i)
		# turn off axis
		pyplot.axis('off')
		# plot raw pixel data		
		pyplot.imshow(X[i, :, :, 0], cmap='gray_r')
	# save plot to file
	figure = pyplot.gcf()  
	figure.set_size_inches(10,10)
	image_200_epochs = output_url+'generated_plot_200epochs_%04d.png' % (step+1)
	pyplot.savefig(image_200_epochs, dpi=100)
	pyplot.close()

"""**Create a line plot of loss for the gan and save to file**"""

def plot_history(d1_hist, d2_hist, g_hist):
	# plot history
	pyplot.plot(d1_hist, label='crit_real')
	pyplot.plot(d2_hist, label='crit_fake')
	pyplot.plot(g_hist, label='gen')
	pyplot.legend()
	pyplot.savefig(output_url+'plot_line_plot_loss.png')
	pyplot.close()

"""**Train the generator and critic**"""

def train(g_model, c_model, gan_model, dataset, latent_dim, n_epochs=5, n_batch=64, n_critic=5):
	# calculate the number of batches per training epoch
	bat_per_epo = int(dataset.shape[0] / n_batch)
	# calculate the number of training iterations
	n_steps = bat_per_epo * n_epochs
	# calculate the size of half a batch of samples
	half_batch = int(n_batch / 2)
	# lists for keeping track of loss
	c1_hist, c2_hist, g_hist = list(), list(), list()
	# manually enumerate epochs
	for i in range(n_steps):
		# update the critic more than the generator
		c1_tmp, c2_tmp = list(), list()
		for _ in range(n_critic):
			# get randomly selected 'real' samples
			X_real, y_real = generate_real_samples(dataset, half_batch)
			# update critic model weights
			c_loss1 = c_model.train_on_batch(X_real, y_real)
			c1_tmp.append(c_loss1)
			# generate 'fake' examples
			X_fake, y_fake = generate_fake_samples(g_model, latent_dim, half_batch)
			# update critic model weights
			c_loss2 = c_model.train_on_batch(X_fake, y_fake)
			c2_tmp.append(c_loss2)
		# store critic loss
		c1_hist.append(mean(c1_tmp))
		c2_hist.append(mean(c2_tmp))
		# prepare points in latent space as input for the generator
		X_gan = generate_latent_points(latent_dim, n_batch)
		# create inverted labels for the fake samples
		y_gan = -ones((n_batch, 1))
		# update the generator via the critic's error
		g_loss = gan_model.train_on_batch(X_gan, y_gan)
		g_hist.append(g_loss) 		
		# summarize loss on this batch
		print('>%d, c1=%.3f, c2=%.3f g=%.3f' % (i+1, c1_hist[-1], c2_hist[-1], g_loss))
		# evaluate the model performance every '50 epoch'
		# print((i+1) * 5)
		if (i+1) % 900 == 0: # 50 epochs
			summarize_performance(i, g_model, latent_dim)
		if (i+1) % 1800 == 0: # 100 epochs
				summarize_performance_100(i, g_model, latent_dim)
		if (i+1) % 3600 == 0: # 200 epochs
				summarize_performance_200(i, g_model, latent_dim)	  
	# line plots of loss
	plot_history(c1_hist, c2_hist, g_hist)

"""**Load images**"""

# size of the latent space
latent_dim = 50
# create the critic
critic = define_critic()
# create the generator
generator = define_generator(latent_dim)
# create the gan
gan_model = define_gan(generator, critic)
# load image data
dataset = dataA1 #load_real_samples()
print(dataset.shape)

"""**Train model**"""

train(generator, critic, gan_model, dataset, latent_dim)

dataset.shape[0]



