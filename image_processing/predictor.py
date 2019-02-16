import os, sys
import copy

from datetime import datetime, timedelta

import numpy as np
import tensorflow as tf

import cv2
import dlib
import imutils
from imutils.face_utils import FaceAligner
import inception_resnet_v1

MODULE_PATH = os.path.dirname(os.path.abspath(__file__))
FACE_DETECTION_MODEL_PATH = MODULE_PATH + '/models/mmod_human_face_detector'
SHAPE_PREDICTION_MODEL_PATH = MODULE_PATH + '/models/shape_predictor_68_face_landmarks'
FACE_RECOGNITION_MODEL_PATH = MODULE_PATH + '/models/dlib_face_recognition_resnet_model_v1'
AGE_AND_GENDER_MODEL_PATH = MODULE_PATH + '/models/age_gender'

# GPU PARAMS
#PROCESSING_SIZE = 1200
#UPSAMPLE_COUNT = 2
#BATCH_SIZE = 1
#ENABLE_AGEGENDER_DETECTION = True

# CPU PARAMS
PROCESSING_SIZE = 800
UPSAMPLE_COUNT = 0
BATCH_SIZE = 1
ENABLE_AGEGENDER_DETECTION = True

MESSAGE_EXPIRE_MS = timedelta(milliseconds=100)

GENDER_MAP = {1: 'M', 0: 'F'}


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
    Loads the Age and Gender Detection model. This function assumes that the model is in
    './models' directory.
    
    Returns:
        logits (list): two logits -- age and gender
        feed_dict (dict): two tf.placeholders in a dict for running the model.
    """
    
    print("loading age and gender model.")
    images_pl = tf.placeholder(tf.float32, shape=[None, 160, 160, 3], name='input_image')
    images = tf.map_fn(lambda frame: tf.reverse_v2(frame, [-1]), images_pl) #BGR TO RGB
    images_norm = tf.map_fn(lambda frame: tf.image.per_image_standardization(frame), images)
    age_logits, gender_logits, _ = inception_resnet_v1.inference(images_norm, keep_probability=0.8,
                                                                 phase_train=False,
                                                                 weight_decay=1e-5)
    gender = tf.argmax(tf.nn.softmax(gender_logits), 1)
    age_ = tf.cast(tf.constant([i for i in range(0, 101)]), tf.float32)
    age = tf.reduce_sum(tf.multiply(tf.nn.softmax(age_logits), age_), axis=1)
    
    logits = [age, gender, tf.nn.softmax(age_logits), tf.nn.softmax(gender_logits)]
    feed_dict = {"image_placeholder": images_pl}
    
    print("creating the session.")
    
    config = tf.ConfigProto()
    config.gpu_options.allow_growth=True
    sess = tf.Session(config=config)
    
    saver = tf.train.Saver()
    ckpt = tf.train.get_checkpoint_state(AGE_AND_GENDER_MODEL_PATH)
    if ckpt and ckpt.model_checkpoint_path:
        saver.restore(sess, ckpt.model_checkpoint_path)
        print("restoring the model...")
    else:
        print("Cannot find the age/gender model")
        sys.exit(0)
    print("initialized.")
    
    return sess, logits, feed_dict


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


def process_batch_frames(color_image_list, gray_image_list, sess, logits, feed_dict, dlib_models):
    """
    Processes a batch of images to detect faces and if ENABLE_AGEGENDER_DETECTION is True it also
    predicts ages and genders of each detected faces.
    
    Args:
        color_image_list (list): list of images. Each item is a frame read by the cv2 package.
        gray_image_list (list): list of images in grayscale. This list should contain the same images
            as the color_image_list, but in grayscale. This list is used by the CNN model.
        sess (tf.Session): the tensorflow session that has the age/gender detection model already loaded.
            if ENABLE_AGEGENDER_DETECTION is False, then this argument can be None since the age/gender
            detection is disabled.
        logits (list): list of the two logits for age and gender. This is coming from the load_age_and_gender_model.
        feed_dict (dict): the dictionary of tf.placeholders coming from the load_age_and_gender_model.
        dlib_models (dict): a dictionary containing dlib cnn, shape_predictor, and recognition models.
    
    Returns:
        n_faces_list (list): list of ints containing the number of detected faces for each frame. So, the
            length of this list is equal to the length if color_image_list and gray_image_list.
        ages (list): lists of detected ages. If ENABLE_AGEGENDER_DETECTION is False, then this list is empty.
            The length of this list is equal to the number of detected faces and genders list.
        genders (list): lists of detected genders. If ENABLE_AGEGENDER_DETECTION is False, then this list is empty.
            The length of this list is equal to the number of detected faces and ages list.
        face_rects (list): lists of rectangle of faces. Each rectangle is a dlib.rectangle object.
    """
    
    # detect faces
    face_images_array, n_faces_list, face_rects, face_descriptors = detect_faces(color_image_list, gray_image_list, dlib_models)

    # detect age and gender for all frames
    ages = []
    genders = []
    ages_proba = []
    genders_proba = []
    if ENABLE_AGEGENDER_DETECTION:
        if len(face_images_array) > 0:
            
            ## debug: write images to disk for inspection
#            for img in face_images_array:
#                fname = "img" + str(frame_number) + ".png"
#                print("writing to file: " + fname)
#                cv2.imwrite(fname, img)

            # this init should not happen here
#            init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
#            sess.run(init_op)

            ages, genders, ages_proba, genders_proba = sess.run(logits,
                        feed_dict={feed_dict['image_placeholder']: face_images_array})

    return n_faces_list, ages, genders, face_rects, face_descriptors, [ages_proba, genders_proba]


def process_image(frame_queue, prediction_queue):
    """
    The main function for the prediction process. This will process frames to
    detect faces, ages and genders.
    """
    
    dlib_models = load_dlib_module()
    sess, logits, feed_dict = load_age_and_gender_model()
        
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
        n_faces_list, ages, genders, face_rects, face_descriptors, probas = process_batch_frames(
            batch_color_image_list,
            batch_gray_image_list,
            sess,
            logits,
            feed_dict,
            dlib_models
        )
            
        # since we processed the batch, we should empty lists for the next batch
        batch_counter = 0
        batch_color_image_list = []
        batch_gray_image_list = []

        # display results on the terminal
#        display_results(n_faces_list, ages, genders, probas)

        # update the last_faces_rects and update the frame to display
        last_face_index = sum(n_faces_list) - n_faces_list[-1]
        if ENABLE_AGEGENDER_DETECTION:
            last_frame_predictions = list(zip(face_rects[last_face_index:],
                                              ages[last_face_index:],
                                              genders[last_face_index:],
                                              face_descriptors[len(face_descriptors)-1],
                                              probas[0][last_face_index:],
                                              probas[1][last_face_index:]))
        else:
            last_frame_predictions = list(zip(face_rects[last_face_index:],
                                              [None]*len(face_rects[last_face_index:]),
                                              [None]*len(face_rects[last_face_index:]),
                                              face_descriptors[len(face_descriptors)-1],
                                              [None]*len(face_rects[last_face_index:]),
                                              [None]*len(face_rects[last_face_index:])))
        
        # set the results for display in the main thread
        prediction_queue.put(last_frame_predictions, False)
    
    print("-----------\n")
    print("done.")


def display_results(n_faces_list, ages, genders, probas):
    """
    Display results in the terminal.
    
    Args:
        n_faces_list (list): list of ints -- number of detected faces.
        ages (list): list of floats -- len(ages) = sum(n_faces_list)
        genders (list): list of 0 or 1 -- len(genders) = sum(n_faces_list)
    """
    
    flat_counter = 0
    for counter in range(len(n_faces_list)):
        n_faces = n_faces_list[counter]
        print("\nFound " + str(n_faces) + " faces.")
        if ENABLE_AGEGENDER_DETECTION:
            for i in range(n_faces):
                print("Age: " + str(int(ages[flat_counter])) + " (" + str(max(probas[0][flat_counter])) + "), gender: " + GENDER_MAP[genders[flat_counter]] + " (" + str(max(probas[1][flat_counter])) + ")")
                flat_counter = flat_counter + 1

