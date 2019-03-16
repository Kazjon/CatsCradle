import os, sys
import copy

from datetime import datetime, timedelta

import numpy as np
import tensorflow as tf

import cv2
import dlib
import imutils
from imutils.face_utils import FaceAligner

from sklearn.externals import joblib

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
FACE_DETECTION_MODEL_PATH = MODULE_PATH + '/models/mmod_human_face_detector'
SHAPE_PREDICTION_MODEL_PATH = MODULE_PATH + '/models/shape_predictor_68_face_landmarks'
FACE_RECOGNITION_MODEL_PATH = MODULE_PATH + '/models/dlib_face_recognition_resnet_model_v1'
AGE_GENDER_MODEL_PATH = MODULE_PATH + '/models/model_age_gender'

# GPU PARAMS
PROCESSING_SIZE = 1200
UPSAMPLE_COUNT = 2
BATCH_SIZE = 1

# CPU PARAMS
#PROCESSING_SIZE = 800
#UPSAMPLE_COUNT = 0
#BATCH_SIZE = 1

ENABLE_AGEGENDER_DETECTION = True

MESSAGE_EXPIRE_MS = timedelta(milliseconds=100)

GENDER_MAP = {0: 'M', 1: 'F'}
AGE_MAP = {0: 'child', 1: 'adult', 2: 'senior'}


def load_dlib_module():
    """
    Loads the dlib models for face detection and recognition. This function assumes that
    the model is in './models' directory.

    Returns:
        a dictionary containing cnn, shape_predictor, and recognition model.
    """

    cnn = dlib.cnn_face_detection_model_v1(FACE_DETECTION_MODEL_PATH)
    shape_predictor = dlib.shape_predictor(SHAPE_PREDICTION_MODEL_PATH)
    recognition_model = dlib.face_recognition_model_v1(FACE_RECOGNITION_MODEL_PATH)

    return {'cnn': cnn, 'shape_predictor': shape_predictor, 'recognition_model': recognition_model}


def load_age_and_gender_model():
    """
    Loads the Age and Gender Detection model. This function assumes that the model is in the
    './models' directory.

    Returns:
        predictor_age_gender (sklearn.??): the model for predicting age.
    """

    print("loading age and gender model.")
    predictor_age_gender = joblib.load(AGE_GENDER_MODEL_PATH)

    return predictor_age_gender


def detect_faces(color_image_list, gray_image_list, dlib_models):
    """
    Detects faces using Dlib's CNN model.

    Args:
        color_image_list (list): list of images. Each item is a frame read by the cv2 package.
        gray_image_list (list): list of images in grayscale. This list should contain the same images
            as the color_image_list, but in grayscale. This list is used by the CNN model.
        dlib_models (dict): a dictionary containing dlib cnn, shape_predictor, and recognition models.

    Returns:
        face_images (np.array): an array of images of detected faces.
        n_faces_list (list): a list of ints showing the number of detected faces in each frame.
        flat_face_rects (list): a list of dlib.rectangle objects containing rectangle info of each detected face.
        face_descriptors (list): list of face_descriptor. A face_descriptor is a lists of 128 dim vector that describes the face.

    Example:
        Given the following inputs
        color_image_list = [Img1 (has three faces), Img2 (has two faces)]
        gray_image_list = [Img1_grayscale (has three faces), Img2_grayscale (has two faces)]
        This function produces the following
        face_images = np.array([face1_img1, face2_img1, face3_img1, face4_img2, face5_img2])
        n_faces_list = [3, 2]
        flat_face_rects = [r1, r2, r3, r4, r5]
        Note that the face images are cropped from the original image in the arguments. So, in our
        example, face1_img1 has a smaller size of Img1, and face2_img1 might have a compeletely
        different size but again smaller than Img1.
    """

    mmod_rects = dlib_models['cnn'](gray_image_list, upsample_num_times=UPSAMPLE_COUNT)

    flat_face_rects = []
    flat_image_list_indices = []
    n_faces_list = []
    all_shapes_list = []
    # mmod_rects is a list of list of rectangles
    for i, image_detection_rects in enumerate(mmod_rects):
        rects = dlib.rectangles()

        # save rects into an array to use later
        rects.extend([d.rect for d in image_detection_rects])
        flat_face_rects.extend(rects)
        flat_image_list_indices.extend([i]*len(image_detection_rects))
        n_faces_list.append(len(image_detection_rects))

        # find shapes in the image -- this is used for face recognition
        faces = dlib.full_object_detections()
        for r in rects:
            shape = dlib_models['shape_predictor'](color_image_list[i], r)
            faces.append(shape)
        all_shapes_list.append(faces)

    # in the above example
    # flat_face_rects = [r1, r2, r3, r4, r5]
    # flat_image_list_indices = [0, 0, 0, 1, 1]
    # n_faces_list = [3, 2]
    # all_shapes_list = [dlib.full_object_detections, dlib.full_object_detections]

    # align detected rectangles to get faces for the next step
    fa = FaceAligner(dlib_models['shape_predictor'])
    face_images = []
    for i, rect in enumerate(flat_face_rects):
        image_index = flat_image_list_indices[i]
        aligned_image = fa.align(color_image_list[image_index], gray_image_list[image_index], rect)
        aligned_image = imutils.resize(aligned_image, width=160, height=160)
        face_images.append(aligned_image)

    # in the above example
    # face_images = [img1, img2, img3, img4, img5]

    # face encodings
    face_descriptors = dlib_models['recognition_model'].compute_face_descriptor(color_image_list, all_shapes_list)
    # face_descriptor is a lists of 128 dim vector that describes the face.
    # if two face descriptor vectors have a Euclidean distance between them less than 0.6
    # then they are from the same person
    # in the above example
    # face_descriptors = [[[0..127],[0..127],[0..127]],[[0..127],[0..127]]]

    return np.array(face_images), n_faces_list, flat_face_rects, face_descriptors


def process_batch_frames(color_image_list, gray_image_list, predictor_age_gender, dlib_models):
    """
    Processes a batch of images to detect faces and if ENABLE_AGEGENDER_DETECTION is True it also
    predicts ages and genders of each detected faces.

    Args:
        color_image_list (list): list of images. Each item is a frame read by the cv2 package.
        gray_image_list (list): list of images in grayscale. This list should contain the same images
            as the color_image_list, but in grayscale. This list is used by the CNN model.
        predictor_age_gender (sklearn.??): the model for predicting age and gender.
        dlib_models (dict): a dictionary containing dlib cnn, shape_predictor, and recognition models.

    Returns:
        n_faces_list (list): list of ints containing the number of detected faces for each frame. So, the
            length of this list is equal to the length if color_image_list and gray_image_list.
        face_rects (list): lists of rectangle of faces. Each rectangle is a dlib.rectangle object.
        face_descriptors (list): list of face_descriptor. A face_descriptor is a lists of 128 dim vector that describes the face.
        age_genders_proba (list): list of probas of age/gender. First item is proba of child, second is proba of adult male, third is for adult female and last is senior.
    """

    # detect faces
    face_images_array, n_faces_list, face_rects, face_descriptors = detect_faces(color_image_list, gray_image_list, dlib_models)

    # detect age and gender for all frames
    age_genders_probas = []
    if ENABLE_AGEGENDER_DETECTION:
        # no support for batch yet
        encodings = np.array(face_descriptors)[0]
        if len(encodings) > 0:
            age_genders_probas = predictor_age_gender.predict_proba(encodings)

            ## debug: write images to disk for inspection
#            for img in face_images_array:
#                fname = "img" + str(frame_number) + ".png"
#                print("writing to file: " + fname)
#                cv2.imwrite(fname, img)

    return n_faces_list, face_rects, face_descriptors, age_genders_probas


def process_image(frame_queue, prediction_queue):
    """
    The main function for the prediction process. This will process frames to
    detect faces, ages and genders.
    """

    dlib_models = load_dlib_module()
    predictor_age_gender = load_age_and_gender_model()

    print("model initialized.")

    batch_counter = 0
    batch_color_image_list = []
    batch_gray_image_list = []

    # this includes the last predicted faces rects plus ages and genders to display on frames
    last_frame_predictions = []

    print("starting predictions...")

    # this thread waits in this infinite loop until the main thread exits
    while True:

        # get one frame to process; wait if necessary for a new frame to process
        message = frame_queue.get(True)
        # check if the frame is expired
        if datetime.now() - message['time'] > MESSAGE_EXPIRE_MS:
            # continue to get another message
            continue

        # process the message
        frame = copy.deepcopy(message['frame'])

        # resize the frame
        resized_frame = imutils.resize(frame, width=PROCESSING_SIZE)

        # convert the color to grayscale
        gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

        # append to the batch image list
        batch_color_image_list.append(resized_frame)
        batch_gray_image_list.append(gray_frame)

        # check the batch counter
        batch_counter = batch_counter + 1
        if batch_counter < BATCH_SIZE:
            continue

        # time to process the frame to detect face/age/gender
        n_faces_list, face_rects, face_descriptors, age_genders_probas = process_batch_frames(
            batch_color_image_list,
            batch_gray_image_list,
            predictor_age_gender,
            dlib_models
        )

        # since we processed the batch, we should empty lists for the next batch
        batch_counter = 0
        batch_color_image_list = []
        batch_gray_image_list = []

        # display results on the terminal
        # display_results(n_faces_list, age_genders_probas)

        # update the last_faces_rects and update the frame to display
        last_face_index = sum(n_faces_list) - n_faces_list[-1]
        if ENABLE_AGEGENDER_DETECTION:
            last_frame_predictions = list(zip(face_rects[last_face_index:],
                                              face_descriptors[len(face_descriptors)-1],
                                              age_genders_probas[last_face_index:]))
        else:
            last_frame_predictions = list(zip(face_rects[last_face_index:],
                                              face_descriptors[len(face_descriptors)-1],
                                              [None]*len(face_rects[last_face_index:])))

        # set the results for display in the main thread
        prediction_queue.put(last_frame_predictions, False)

    print("-----------\n")
    print("done.")


def display_results(n_faces_list, age_genders_probas):
    """
    Display results in the terminal.

    Args:
        n_faces_list (list): list of ints -- number of detected faces.
        age_genders_probas (list): list of probas
    """

    flat_counter = 0
    for counter in range(len(n_faces_list)):
        n_faces = n_faces_list[counter]
        print("\nFound " + str(n_faces) + " faces.")
        if ENABLE_AGEGENDER_DETECTION:
            for i in range(n_faces):
                print("probas: " + str(age_genders_probas))
                flat_counter = flat_counter + 1
