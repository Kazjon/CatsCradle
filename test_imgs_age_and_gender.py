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

def detectUndetectedPersons(undetected_persons):
    #RUDE CARNIE DEFAULTS

    print("starting the process to detect people's age and gender...")

    gender_model_dir = "./age_and_gender_detection/pretrained_checkpoints/gender/"
    age_model_dir = "./age_and_gender_detection/pretrained_checkpoints/age/"
    # What processing unit to execute inference on
    device_id = '/cpu:0'
    # Checkpoint basename
    checkpoint = 'checkpoint'
    model_type = 'inception'

    config = tf.ConfigProto(allow_soft_placement=True)

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
                print(person_name, getAgeAndGender(person_name, person_img, sess, coder, images,\
                        writer, AGE_LIST, GENDER_LIST, age_softmax_output,\
                        gender_softmax_output))

def getAgeAndGender(person_number, target_image, sess, coder, images,\
    writer, age_list, gender_list, age_softmax_output,\
    gender_softmax_output):

    (ageRange, ageRange_prob) = classify_one_multi_crop(sess, age_list,\
        age_softmax_output, coder, images, target_image,\
        writer)
    (gender, gender_prob) = classify_one_multi_crop(sess,\
        gender_list, gender_softmax_output, coder,\
        images, target_image, writer)

    return AGE_MAP[ageRange], gender

def _prepare_image(image):
    """Resize the image to a maximum height of `self.height` and maximum
    width of `self.width` while maintaining the aspect ratio. Pad the
    resized image to a fixed size of ``[self.height, self.width]``."""
    img = tf.image.decode_png(image, channels=1)
    dims = tf.shape(img)

    max_width = tf.to_int32(tf.ceil(tf.truediv(dims[1], dims[0]) * self.height_float))
    max_height = tf.to_int32(tf.ceil(tf.truediv(self.width, max_width) * self.height_float))

    resized = tf.cond(
        tf.greater_equal(self.width, max_width),
        lambda: tf.cond(
            tf.less_equal(dims[0], self.height),
            lambda: tf.to_float(img),
            lambda: tf.image.resize_images(img, [self.height, max_width],
                                           method=tf.image.ResizeMethod.BICUBIC),
        ),
        lambda: tf.image.resize_images(img, [max_height, self.width],
                                       method=tf.image.ResizeMethod.BICUBIC)
    )

    padded = tf.image.pad_to_bounding_box(resized, 0, 0, self.height, self.width)
    return padded


if __name__ == '__main__':
    raw_undetected_persons = list(map(lambda filename: os.path.join("imgs",
        filename), os.listdir("imgs/")))
    raw_undetected_persons.remove("imgs/.DS_Store")
    undetected_persons = []
    for i, img_name in enumerate(raw_undetected_persons):
        img = cv2.imread(img_name)
        height, width, channels = img.shape
        vertical_padding = int(max(0, (TARGET_IMG_HEIGHT - height)/2))
        horizontal_padding = int(max(0, (TARGET_IMG_WIDTH - width)/2))
        new_img = cv2.copyMakeBorder(img, vertical_padding, vertical_padding,\
            horizontal_padding, horizontal_padding,\
            cv2.BORDER_CONSTANT,value=WHITE)
        undetected_persons.append((img_name, new_img))

    detectUndetectedPersons(undetected_persons)
