#Run in Python2.7
#GENERAL IMPORTS
#TODO: standardize camelCase vs underscored var names
import os
import sys
import numpy as np
from collections import deque

#FACE RECOGNITION IMPORTS
import cv2
import face_recognition

#RUDE CARNIE IMPORTS
sys.path.append("age_and_gender_detection")
# import tensorflow as tf
from model import select_model, get_checkpoint
from utils import *
from guess import classify_one_multi_crop

from MathUtils import *
from BodyPartDetector import *
from Person import *
from Sensor import *
from threading import Lock, Thread
import time

RESIZE_FINAL = 227
GENDER_LIST =['M','F']
AGE_LIST = ['(0, 2)','(4, 6)','(8, 12)','(15, 20)','(25, 32)','(38, 43)',\
    '(48, 53)','(60, 100)']

AGE_MAP = {'(0, 2)':"child",'(4, 6)':"child",'(8, 12)':"child",'(15, 20)':"teen",'(25, 32)':"adult",'(38, 43)':"adult",'(48, 53)':"adult",'(60, 100)':"senior"}
MAX_BATCH_SZ = 128
WHITE = [255,255, 255]

TARGET_IMG_HEIGHT = 231
TARGET_IMG_WIDTH = 231
SECOND_PROB_THRESHOLD = 0.3

def detectUndetectedPersons(outfile, undetected_persons):
    #RUDE CARNIE DEFAULTS

    print("starting the process to detect people's age and gender...")

    gender_model_dir = "./age_and_gender_detection/pretrained_checkpoints/gender/"
    age_model_dir = "./age_and_gender_detection/pretrained_checkpoints/age/"
    # What processing unit to execute inference on
    device_id = '/device:GPU:0'
    # Checkpoint basename
    checkpoint = 'checkpoint'
    model_type = 'inception'

    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.1)
    config = tf.ConfigProto(allow_soft_placement=True)
        # gpu_options=gpu_options)
    # config = tf.ConfigProto(allow_soft_placement=True)

    with tf.Session(config=config) as sess:
        #Age detection model
        n_ages = len(AGE_LIST)
        age_model_fn = select_model(model_type)

        #Gender detection model
        n_genders = len(GENDER_LIST)
        gender_model_fn = select_model(model_type)

        print("initializing the model to detect age and gender")

        with tf.device(device_id):
            print "initializing the model to detect age and gender using ", str(device_id)
            images = tf.placeholder(tf.float32, [None, RESIZE_FINAL, RESIZE_FINAL, 3])
            requested_step = None
            init = tf.global_variables_initializer()

            #age model
            age_logits = age_model_fn("age", n_ages, images, 1, False)
            age_checkpoint_path, global_step = get_checkpoint(age_model_dir, requested_step, checkpoint)
            age_vars = set(tf.global_variables())
            saver_age = tf.train.Saver(list(age_vars))
            saver_age.restore(sess, age_checkpoint_path)
            age_softmax_output = tf.nn.softmax(age_logits)


            #gender_model
            gender_logits = gender_model_fn("gender", n_genders, images, 1, False)
            gender_checkpoint_path, global_step = get_checkpoint(gender_model_dir, requested_step, checkpoint)
            gender_vars = set(tf.global_variables()) - age_vars
            saver_gender = tf.train.Saver(list(gender_vars))
            saver_gender.restore(sess, gender_checkpoint_path)
            gender_softmax_output = tf.nn.softmax(gender_logits)

            coder = ImageCoder()

            writer = None

            print("starting the loop for detecting age and gender in each frame")
            time.sleep(15) # sleep to allow the tensor flow/rude carnie stuff to load
            for person_name, person_img in undetected_persons:
                outfile.write("%s%s%s"%(person_name, getAgeAndGender(person_name, person_img, sess, coder, images,\
                        writer, AGE_LIST, GENDER_LIST, age_softmax_output,\
                        gender_softmax_output), '\n'))

def getAgeAndGender(person_number, target_image, sess, coder, images,\
    writer, age_list, gender_list, age_softmax_output,\
    gender_softmax_output):

    (age_range, age_range_prob), (age_range_guess_2, age_range_guess_2_prob) =\
        classify_one_multi_crop(sess, age_list, age_softmax_output, coder,\
        images, target_image, writer)
    (gender, gender_prob) = classify_one_multi_crop(sess, gender_list,\
        gender_softmax_output, coder, images, target_image, writer)

    first_age_guess = AGE_MAP[age_range]
    second_age_guess = AGE_MAP[age_range_guess_2]
    final_age_guess = first_age_guess

    if first_age_guess != second_age_guess and age_range_guess_2_prob > SECOND_PROB_THRESHOLD:
        final_age_guess = second_age_guess
        # print('first_age_guess', first_age_guess)
        # print('second_age_guess', second_age_guess)
        # print('final_age_guess', final_age_guess)

    return final_age_guess, gender


if __name__ == '__main__':
    img_folder = "imgs/"
    raw_undetected_persons = list(map(lambda filename: os.path.join(img_folder,
        filename), sorted(os.listdir(img_folder))))
    raw_undetected_persons = list(filter(lambda filename: ".jpg" in filename, raw_undetected_persons))#[:2]

    undetected_persons = []
    with open(os.path.join(img_folder, "guesses.txt"), "wb") as guesses_file:
        for i, img_name in enumerate(raw_undetected_persons):
            img = cv2.imread(img_name)
            height, width, channels = img.shape
            # img = cv2.resize(img, (0, 0),
            #         fx=1.5, fy=1.5)
            vertical_padding = int(max(0, (TARGET_IMG_HEIGHT - height)/2))
            horizontal_padding = int(max(0, (TARGET_IMG_WIDTH - width)/2))
            new_img = cv2.copyMakeBorder(img, vertical_padding, vertical_padding,\
                horizontal_padding, horizontal_padding,\
                cv2.BORDER_CONSTANT,value=WHITE)
            undetected_persons.append((img_name, new_img))

        detectUndetectedPersons(guesses_file, undetected_persons)

    correct_age_guesses = 0
    correct_age_guess_list = []

    correct_gender_guesses = 0
    correct_gender_guess_list = []

    correct_both_guesses = 0
    correct_both_guess_list = []

    test_set_size = 0

    with open(os.path.join(img_folder, "guesses.txt"), "rb") as guesses_file:
        with open(os.path.join(img_folder, "correct_guesses.txt"), "rb") as correct_guesses_file:
            correct_guess_lines = correct_guesses_file.readlines()
            for i, rude_carnie_guess in enumerate(guesses_file.readlines()):
                img_id = rude_carnie_guess[:rude_carnie_guess.index('(')]
                assert img_id == correct_guess_lines[i][:correct_guess_lines[i].index('(')]

                rude_carnie_guess = rude_carnie_guess[rude_carnie_guess.index('(')+1:\
                    rude_carnie_guess.index(')')]
                [rude_carnie_guess_age, rude_carnie_guess_gender] =\
                    rude_carnie_guess.split(',')

                correct_guess = correct_guess_lines[i][correct_guess_lines[i]\
                    .index('(')+1:correct_guess_lines[i].index(')')]
                [correct_guess_age, correct_guess_gender, ] =\
                    correct_guess.split(',')


                # print("*****************************************************")
                # print(rude_carnie_guess_age, rude_carnie_guess_gender)
                # print(correct_guess_age, correct_guess_gender)
                # print("*****************************************************")


                if correct_guess_age in rude_carnie_guess_age:
                    correct_age_guesses += 1
                    correct_age_guess_list.append(img_id)

                if correct_guess_gender in rude_carnie_guess_gender:
                    correct_gender_guesses += 1
                    correct_gender_guess_list.append(img_id)

                if correct_guess_age in rude_carnie_guess_age and \
                    correct_guess_gender in rude_carnie_guess_gender:
                    correct_both_guesses += 1
                    correct_both_guess_list.append(img_id)

                test_set_size += 1

            print "test set size", test_set_size

            print "correct_age_guesses", correct_age_guesses
            # print "correct_age_guess_list", correct_age_guess_list

            print "correct_gender_guesses", correct_gender_guesses
            # print "correct_gender_guess_list", correct_gender_guess_list

            print "correct_both_guesses", correct_both_guesses
            # print "correct_both_guess_list", correct_both_guess_list
