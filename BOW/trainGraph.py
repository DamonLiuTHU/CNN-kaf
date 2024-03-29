"""

Just Forcus on these kind of comments begin with three ". 

The following description of the evaluations is based on MR database. 
For the 5 classification task, we got 76-77% after 100 epoch on 'CNN-non-static'
"""

"""
Train convolutional network for sentiment analysis. Based on
"Convolutional Neural Networks for Sentence Classification" by Yoon Kim
http://arxiv.org/pdf/1408.5882v2.pdf

For 'CNN-non-static' gets to 82.1% after 61 epochs with following settings:
embedding_dim = 20          
filter_sizes = (3, 4)
num_filters = 3
dropout_prob = (0.7, 0.8)
hidden_dims = 100

For 'CNN-rand' gets to 78-79% after 7-8 epochs with following settings:
embedding_dim = 20          
filter_sizes = (3, 4)
num_filters = 150
dropout_prob = (0.25, 0.5)
hidden_dims = 150

For 'CNN-static' gets to 75.4% after 7 epochs with following settings:
embedding_dim = 100          
filter_sizes = (3, 4)
num_filters = 150
dropout_prob = (0.25, 0.5)
hidden_dims = 150

* it turns out that such a small data set as "Movie reviews with one
sentence per review"  (Pang and Lee, 2005) requires much smaller network
than the one introduced in the original article:
- embedding dimension is only 20 (instead of 300; 'CNN-static' still requires ~100)
- 2 filter sizes (instead of 3)
- higher dropout probabilities and
- 3 filters per filter size is enough for 'CNN-non-static' (instead of 100)
- embedding initialization does not require prebuilt Google Word2Vec data.
Training Word2Vec on the same "Movie reviews" data set is enough to 
achieve performance reported in the article (81.6%)

** Another distinct difference is slidind MaxPooling window of length=2
instead of MaxPooling over whole feature map as in the article
"""

import numpy as np
from keras.layers import Activation, Dense, Dropout, Embedding, Flatten, Input, Merge, Convolution1D, MaxPooling1D
from keras.models import Sequential, Model
from keras.utils import np_utils

import data_helpers
from w2v import train_word2vec

np.random.seed(2)

# A monkey patch to fix a bug in Keras with a higher version of Tensorflow (maybe in the near future keras can fix it)
import tensorflow as tf

tf.python.control_flow_ops = tf

# Parameters
# ==================================================
#
# Model Variations. See Kim Yoon's Convolutional Neural Networks for 
# Sentence Classification, Section 3 for detail.

"""
Model Setting and Parameters
"""

model_variation = 'CNN-non-static'  # CNN-rand | CNN-non-static | CNN-static
print('Model variation is %s' % model_variation)

# Model Hyperparameters
embedding_dim = 20
filter_sizes = (3, 4)
num_filters = 3
dropout_prob = (0.7, 0.8)
hidden_dims = 100
sequence_length = 81

# Training parameters
batch_size = 32
num_epochs = 10
val_split = 0.1

# Word2Vec parameters, see train_word2vec
min_word_count = 1  # Minimum word count                        
context = 10  # Context window size

# Data Preparatopn
# ==================================================
#
# Load data

"""
Load data. 
For the usage of load_data_chinese, please refer to the data_helper.py.
For the usage of w2c word training and interfering, refer to w2c.py
"""

print("Loading data...")
x, y, vocabulary, vocabulary_inv = data_helpers.load_data_chinese()

"""
x -> two dimensions. [sentence][word]
y -> one dimension. [sentence]
"""

if model_variation == 'CNN-non-static' or model_variation == 'CNN-static':
    embedding_weights = train_word2vec(x, vocabulary_inv, embedding_dim, min_word_count, context)
    if model_variation == 'CNN-static':
        x = embedding_weights[0][x]
elif model_variation == 'CNN-rand':
    embedding_weights = None
else:
    raise ValueError('Unknown model variation')

# Shuffle data
"""
reorganize the order of sentences in random.
"""
shuffle_indices = np.random.permutation(np.arange(len(y)))
x_shuffled = x[shuffle_indices]
y_shuffled = y[shuffle_indices]

# Convert class vectors to binary class matrices
"""
from [0,5} -> [0-1], [0-1] ... (print the y_shuffled to ensure that)
You can find why use this kind of conversion in future
"""
nb_classes = 5
y_origin = y_shuffled
y_shuffled = np_utils.to_categorical(y_shuffled, nb_classes)

print("Vocabulary Size: {:d}".format(len(vocabulary)))

# Building model
# ==================================================
#
# graph subnet with one input and one output,
# convolutional layers concateneted in parallel

"""
CNN is built here.
you can omit the code from "graph_in" to the "main sequential model"
"""

"""
graph_in is actually the stacks of convolution layers and pooling layers 
"""
graph_in = Input(shape=(sequence_length, embedding_dim))
convs = []
for fsz in filter_sizes:
    # highly recommand to put Batch Normalization here
    conv = Convolution1D(nb_filter=num_filters,
                         filter_length=fsz,
                         border_mode='valid',
                         activation='relu',
                         subsample_length=1)(graph_in)
    pool = MaxPooling1D(pool_length=2)(conv)
    flatten = Flatten()(pool)
    convs.append(flatten)

if len(filter_sizes) > 1:
    out = Merge(mode='concat')(convs)
else:
    out = convs[0]

graph = Model(input=graph_in, output=out)

# main sequential model

"""
The main structure of this CNN is:
input
embedding layer (to get the vector of the word maybe)
dropout
graph implemented before
make the feture vector short (in Dense, Dropout, Dence...)
softmax for classification
"""

model = Sequential()
if not model_variation == 'CNN-static':
    model.add(Embedding(len(vocabulary), embedding_dim, input_length=sequence_length,
                        weights=embedding_weights))
model.add(Dropout(dropout_prob[0], input_shape=(sequence_length, embedding_dim)))
model.add(graph)
model.add(Dense(hidden_dims))
model.add(Dropout(dropout_prob[1]))
model.add(Activation('relu'))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))

"""
compile the model
"""
model.compile(loss='categorical_crossentropy', optimizer='rmsprop', metrics=['accuracy'])

# # Training model
# # ==================================================
# """
# train the model, validation_split shows the division of dataset, one val_split of dataset is used for validation while the rest is used for training
# """
model.fit(x_shuffled, y_shuffled, batch_size=batch_size,
          nb_epoch=num_epochs, validation_split=val_split, verbose=1)

# """
# Save the net configuration and the trained model for future fine-tuning
# """
# model.save('simple_net.h5') # this model is generated using wordvec as sentence representation.
#
# """
# you can predict the sentence in that way.
# """

from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, KFold

from sklearn.ensemble import RandomForestClassifier

kf = KFold(n_splits=10)
for train_index, test_index in kf.split(x_shuffled):
    # print "train : ", train_index, "test:", test_index
    X_train, X_test = x_shuffled[train_index], x_shuffled[test_index]
    y_train, y_test = y_origin[train_index], y_origin[test_index]
    clf = RandomForestClassifier()
    model = clf.fit(X_train, y_train)
    print 'RandomForest Score: ', model.score(X_test, y_test)

X_train, X_test, y_train, y_test = train_test_split(x_shuffled, y_origin, test_size=0.2, random_state=0)
clf = SVC()
model = clf.fit(X_train, y_train)
print 'SVC : ', model.score(X_test, y_test)

# from sklearn import model_selection as ms
# score = ms.cross_val_score(model, x_shuffled, y_shuffled, cv=10, n_jobs=-1, verbose=1)

# x = load_data_chinese() #(change the input file, implement a flexible one in future)
