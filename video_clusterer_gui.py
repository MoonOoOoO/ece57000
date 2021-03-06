from gui import *
from distances import *
from medoid_classifier import *
import cv2
import numpy as np

videos = []
points = []
labels = []
medoids = []

distance = dtw(bidirectional(chamfer(L2_vector(L2_scalar)), plus))

def process(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    v = np.median(gray)
    sigma = 0.33
    lower_thresh = int(max(0, (1.0-sigma)*v))
    upper_thresh = int(min(255, (1.0+sigma)*v))
    edge = cv2.Canny(gray, lower_thresh, upper_thresh)
    return edge

def edge_pixels(image):
    m, n = image.shape
    pixels = []
    for i in range(0, m, 10):
        for j in range(0, n, 10):
            if image[i, j]>0:
                pixels.append([i,j])
    return pixels

def start_recording():
    message("")
    global camera
    camera = cv2.VideoCapture(0)
    global stop, video
    stop = False
    video = []
    def internal():
        if not stop:
            return_value, image = camera.read()
            if show_edges():
                edge = process(image)
                get_window().show_image(cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR))
            else:
                get_window().show_image(image)
            video.append(image)
            get_window().after(10, internal)
    internal()

def stop_recording():
    global stop
    stop = True
    camera.release()
    return video, [edge_pixels(process(video[i]))
                   for i in range(0, len(video), 5)]

def clear_command():
    global videos, points, labels, medoids
    videos = []
    points = []
    labels = []
    medoids = []
    message("")

def record_command():
    message("")
    video, edge_pixel_frames = stop_recording()
    videos.append(video)
    points.append(edge_pixel_frames)
    labels.append(-1)

def random_labels_command():
    global labels, medoids
    labels = random_labels(points, 2)
    medoids = []
    message("")

def train_command():
    def internal():
        global medoids
        medoids = train(distance, points, labels)
        message("{:.3f}".format(cost(distance, points, labels, medoids)))
    if not all_labels(labels, 2):
        message("Missing class")
    elif not all_labeled(labels):
        message("Random labels first")
    else:
        message("Training")
        get_window().after(10, internal)

def reclassify_all_command():
    def internal():
        global labels
        labels = reclassify_all(distance, points, medoids)
        message("{:.3f}".format(cost(distance, points, labels, medoids)))
    if len(medoids)==0:
        message("Train first")
    else:
        message("Reclassifying all")
        get_window().after(10, internal)

def loop_command():
    def internal(last_cost):
        global labels, medoids
        medoids = train(distance, points, labels)
        labels = reclassify_all(distance, points, medoids)
        this_cost = cost(distance, points, labels, medoids)
        message("{:.3f}".format(this_cost))
        if this_cost<last_cost:
            get_window().after(500, lambda: internal(this_cost))
        else:
            message("Done")
    if not all_labeled(labels):
        message("Random labels first")
    elif not all_labels(labels, 2):
        message("Missing class")
    else:
        infinity = float("inf")
        internal(infinity)

def play(i, j):
    if i<len(videos):
        if labels[i]==0:
            message("Pick Up")
        elif labels[i]==1:
            message("Put Down")
        else:
            message("Unlabeled")
        if j<len(videos[i]):
            if show_edges():
                edge = process(videos[i][j])
                get_window().show_image(cv2.cvtColor(edge, cv2.COLOR_GRAY2BGR))
            else:
                get_window().show_image(videos[i][j])
            get_window().after(int((1.0/fps)*1000), lambda: play(i, j+1))
        else:
            get_window().after(1000, lambda: play(i+1, 0))

def play_command():
    play(0, 0)

add_button(0, 0, "Clear", clear_command, nothing)
show_edges = add_checkbox(0, 1, "Edges?", nothing)
add_button(0, 2, "Record", start_recording, record_command)
add_button(0, 3, "Random labels", random_labels_command, nothing)
add_button(1, 0, "Train", train_command, nothing)
add_button(1, 1, "Reclassify all", reclassify_all_command, nothing)
add_button(1, 2, "Loop", loop_command, nothing)
add_button(1, 3, "Play", play_command, nothing)
add_button(1, 4, "Exit", done, nothing)
message = add_message(2, 0, 5)
camera = cv2.VideoCapture(0)
width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = camera.get(cv2.CAP_PROP_FPS)
camera.release()
start_video(width, height, 3, 5)
