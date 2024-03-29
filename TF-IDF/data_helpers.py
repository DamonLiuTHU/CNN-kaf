# encoding=utf-8
# coding=utf-8
# -*- coding: utf-8 -*-
import numpy as np
import re
import itertools
from collections import Counter

"""
Original taken from https://github.com/dennybritz/cnn-text-classification-tf
"""


def clean_str(string):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Original taken from https://github.com/yoonkim/CNN_sentence/blob/master/process_data.py
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " \( ", string)
    string = re.sub(r"\)", " \) ", string)
    string = re.sub(r"\?", " \? ", string)
    string = re.sub(r"\s{2,}", " ", string)
    return string.strip().lower()


def load_data_and_labels():
    """
    Loads MR polarity data from files, splits the data into words and generates labels.
    Returns split sentences and labels.
    """
    # Load data from files
    positive_examples = list(open("./data/rt-polarity.pos").readlines())
    positive_examples = [s.strip() for s in positive_examples]
    negative_examples = list(open("./data/rt-polarity.neg").readlines())
    negative_examples = [s.strip() for s in negative_examples]
    # Split by words
    x_text = positive_examples + negative_examples
    x_text = [clean_str(sent) for sent in x_text]
    x_text = [s.split(" ") for s in x_text]
    # Generate labels
    positive_labels = [[0, 1] for _ in positive_examples]
    negative_labels = [[1, 0] for _ in negative_examples]
    y = np.concatenate([positive_labels, negative_labels], 0)
    return [x_text, y]


def pad_sentences(sentences, padding_word="<PAD/>"):
    """
    Pads all sentences to the same length. The length is defined by the longest sentence.
    Returns padded sentences.
    """
    sequence_length = max(len(x) for x in sentences)
    padded_sentences = []
    for i in range(len(sentences)):
        sentence = sentences[i]
        num_padding = sequence_length - len(sentence)
        new_sentence = sentence + [padding_word] * num_padding
        padded_sentences.append(new_sentence)
    return padded_sentences


def build_vocab(sentences):
    """
    Builds a vocabulary mapping from word to index based on the sentences.
    Returns vocabulary mapping and inverse vocabulary mapping.
    """
    # Build vocabulary
    word_counts = Counter(itertools.chain(*sentences))
    # Mapping from index to word
    vocabulary_inv = [x[0] for x in word_counts.most_common()]
    # Mapping from word to index
    vocabulary = {x: i for i, x in enumerate(vocabulary_inv)}
    return [vocabulary, vocabulary_inv]


import math


def get_TF_IDF(word, vocabulary, N, N1, sentence):
    if word == '<PAD>': return 0
    TF = 0.0
    sentence_length = 0;
    for tmp in sentence:
        if tmp != '<PAD>':
            sentence_length += 1
        if tmp == word:
            TF += 1.0
    TF /= sentence_length
    IDF = math.log(float(N) / float(N1), math.e)
    return TF * IDF


sentence_count_dic = {}


def get_sentence_count(target, sentences):
    return sentence_count_dic.get(target)


def get_sentence_vector(sentence,vocabulary,sentences):
    vec = np.zeros(100, dtype=np.float)
    for word in sentence:
        tf_idf = get_TF_IDF(word, vocabulary, len(sentences), get_sentence_count(word, sentences), sentence)
        vec += (tf_idf * get_vector_for_unicode_word(word))
    vec /= len(sentence)
    return vec

# def get_vector_for_sentence(sentence):
#     vec = np.zeros(100, dtype=np.int)
#     for word in sentence:
#         vec += get_vector_for_unicode_word(word)
#     vec /= len(sentence)
#     return vec

def build_input_data(sentences, labels, vocabulary):
    """
    Maps sentencs and labels to vectors based on a vocabulary.
    """
    for sentence in sentences:
        tmp_set = set()
        for word in sentence:
            if word == '<PAD>':
                break
            tmp_set.add(word)
        for word in tmp_set:
            if word in sentence_count_dic:
                sentence_count_dic[word] += 1
            else:
                sentence_count_dic[word] = 1
    print 'construct word in how many sentences finished'

    x = np.array([get_sentence_vector(sentence,vocabulary,sentences) for sentence in sentences])
    y = np.array(labels)
    return [x, y]


def build_input_data_for_sentences(sentences, vocabulary):
    """
    Maps sentencs and labels to vectors based on a vocabulary.
    """
    x = np.array([[vocabulary[word] for word in sentence] for sentence in sentences])
    return x


def load_data():
    """
    Loads and preprocessed data for the MR dataset.
    Returns input vectors, labels, vocabulary, and inverse vocabulary.
    """
    # Load and preprocess data
    sentences, labels = load_data_and_labels()
    sentences_padded = pad_sentences(sentences)
    vocabulary, vocabulary_inv = build_vocab(sentences_padded)
    x, y = build_input_data(sentences_padded, labels, vocabulary)
    return [x, y, vocabulary, vocabulary_inv]


def batch_iter(data, batch_size, num_epochs):
    """
    Generates a batch iterator for a dataset.
    """
    data = np.array(data)
    data_size = len(data)
    num_batches_per_epoch = int(len(data) / batch_size) + 1
    for epoch in range(num_epochs):
        # Shuffle the data at each epoch
        shuffle_indices = np.random.permutation(np.arange(data_size))
        shuffled_data = data[shuffle_indices]
        for batch_num in range(num_batches_per_epoch):
            start_index = batch_num * batch_size
            end_index = min((batch_num + 1) * batch_size, data_size)
            yield shuffled_data[start_index:end_index]


import jieba
import csv

dic = {u'好评': 3,
       u'中评': 2,
       u'差评': 1,
       u'其他': 0}


def load_data_and_labels_chinese():
    """
    x_text = [[word, word, word...], [word, word...], ...]
    y = [label, label...]
    """
    dirs = ['../data/business.csv',
            '../data/service.csv',
            '../data/others.csv',
            '../data/product.csv',
            '../data/platform.csv']

    x_text = []
    y = []

    label = -1
    for dir in dirs:
        label += 1
        with open(dir, 'rb') as f:
            reader = csv.reader(f)
            all_list = list(reader)
        for sentence in all_list:
            if sentence[3] == 'sentence':
                continue
            seq_list = jieba.cut(sentence[3])
            x_text.append(list(seq_list))
            comment = sentence[3]
            # print type(sentence[4])
            # tmp = sentence[4].decode('GBK')   #sentence 4 means : emotion

            # label = dic[tmp]
            y.append(label)
    return x_text, y


def pad_sentences_chinese(x_text, pad_word='<PAD>'):
    """
    x_text = [[word, word, ... <PAD>, <PAD>], ...]
    """
    pad_x_text = []
    sequence_length = max(len(x) for x in x_text)
    for i in range(len(x_text)):
        x = x_text[i]
        padding = sequence_length - len(x)
        new_x = x + [pad_word] * padding
        pad_x_text.append(new_x)
    return pad_x_text


def my_pad_sentences_chinese(x_text, pad_word='<PAD>'):
    """
    x_text = [[word, word, ... <PAD>, <PAD>], ...]
    """
    pad_x_text = []
    sequence_length = 81
    for i in range(len(x_text)):
        x = x_text[i]
        padding = sequence_length - len(x)
        new_x = x + [pad_word] * padding
        pad_x_text.append(new_x)
    return pad_x_text


def build_vocab_chinese(x_text):
    """
    vocabulary_inv: a list of word in the order of frequency
    vocabulary: a dict {index of vocabulary_inv: word, ...}
    """
    word_counts = Counter(itertools.chain(*x_text))
    vocabulary_inv = [x[0] for x in word_counts.most_common()]
    vocabulary = {x: i for i, x in enumerate(vocabulary_inv)}
    return vocabulary, vocabulary_inv


import gensim, numpy
import os

path = '../data/review.model.bin'
print path

model = gensim.models.Word2Vec.load(path)


def get_vector_for_unicode_word(word):
    # if model.have
    if word == '<PAD>':
        vec = np.zeros(100, dtype=np.float)
        return vec

    if word not in model.vocab:
        return np.zeros(100, dtype=np.float)

    return model[word]





def build_input_data_chinese(sentences, labels, vocabulary):
    """
    list -> ndarray
    """
    # x = np.array([[vocabulary[word] for word in sentence] for sentence in sentences])
    # x = np.array([[get_vector_for_unicode_word(word) for word in sentence] for sentence in sentences])
    x = np.array([get_vector_for_sentence(sentence) for sentence in sentences])
    y = np.array(labels)
    return x, y


import pandas as pd


def load_split_data_from_labeled_review_csv():
    x_text = []  # the list for reviews cut apart already and this list's elements are lists
    y = []  # the list of labels
    csv_path = './data/labeledreview.csv'
    with open(csv_path, 'rb') as f:
        reader = csv.reader(f)
        all_list = list(reader)
    for sentence in all_list:
        review_split_result = sentence[2]
        review_split_result = review_split_result.decode('gbk').encode('utf-8')
        review_label = sentence[4]
        cut_result = review_split_result.strip().split(' ')
        x_text.append(cut_result)
        y.append(review_label)
    return x_text, y


def load_data_chinese():
    sentences, labels = load_data_and_labels_chinese()
    # sentences, labels = load_split_data_from_labeled_review_csv()
    sentences_padded = pad_sentences_chinese(sentences)
    vocabulary, vocabulary_inv = build_vocab_chinese(sentences_padded)
    x, y = build_input_data(sentences_padded, labels, vocabulary)
    print x[0]
    print y[0]
    return x, y, vocabulary, vocabulary_inv


def generate_input_for_sentence(sentence):  # sentence is just a raw comment created by buyer
    cut_result = jieba.cut(sentence)
    sequence_length = 81
    padding = sequence_length - len(cut_result)
    new_x = cut_result + ['<PAD>'] * padding
    return new_x


import xlrd

utf8 = 'utf8'


def load_sentences_in_xlsx_file(file_path, column_index):  # this method returns a list of raw comment
    print 'begin load sentence file'
    result = []
    xlrd.Book.encoding = utf8
    data = xlrd.open_workbook(file_path)
    table = data.sheets()[0]
    nrows = table.nrows
    for i in range(nrows):
        comment = table.row_values(i)[column_index:column_index + 1]
        str_c = str(comment[0])
        str_c = str_c.encode(utf8)
        cut_result = jieba.cut(str_c)
        result.append((list(cut_result)))
    print 'load sentence file success'
    return result


def my_get_input_sentence():
    raw_comment_cut = load_sentences_in_xlsx_file('./data/comment_origin_simp.xlsx', 1)
    sentence_padded = my_pad_sentences_chinese(raw_comment_cut)
    vocabulary, vocabulary_inv = build_vocab_chinese(sentence_padded)
    x = build_input_data_for_sentences(sentence_padded, vocabulary)
    return x
