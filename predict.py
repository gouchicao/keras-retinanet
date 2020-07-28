import keras

from keras_retinanet import models
from keras_retinanet.utils.image import read_image_bgr, preprocess_image, resize_image
from keras_retinanet.utils.visualization import draw_box, draw_caption
from keras_retinanet.utils.colors import label_color
from keras_retinanet.utils.gpu import setup_gpu

import cv2
import csv
import os
import sys
import numpy as np
import time
import shutil
import argparse


#gpu = 0
#setup_gpu(gpu)


def predict(model, class_names, image_file, predict_file):
    image = read_image_bgr(image_file)
    draw = image.copy()

    image = preprocess_image(image)
    image, scale = resize_image(image)

    start = time.time()
    boxes, scores, labels = model.predict_on_batch(np.expand_dims(image, axis=0))
    print("File {} Processing Time {:.3f}".format(image_file, time.time() - start))

    boxes /= scale

    for box, score, label in zip(boxes[0], scores[0], labels[0]):
        if score < 0.5:
            break

        color = label_color(label)

        b = box.astype(int)
        draw_box(draw, b, color=color)
        caption = "{} {:.3f}".format(class_names[label], score)
        draw_caption(draw, b, caption)

    cv2.imwrite(predict_file, draw)


def read_class_names(class_file):
    names = []
    with open(class_file, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            names.append(row[0])
    return names


def parse_args(args):
    parser = argparse.ArgumentParser(description="Object Detection.")

    parser.add_argument(
        "--model", help="model path.", required=True, type=str
    )
    parser.add_argument(
        "--class_csv", help="class path.", required=True, type=str
    )
    parser.add_argument(
        "--data_dir", help="data dir.", required=True, type=str
    )
    parser.add_argument(
        "--predict_dir", help="predict dir", required=True, type=str
    )

    return parser.parse_args(args)


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    args = parse_args(args)

    data_dir = args.data_dir
    predict_dir = args.predict_dir

    if os.path.exists(predict_dir):
        shutil.rmtree(predict_dir)
    os.makedirs(predict_dir)

    image_list = list(
        filter(
            lambda x: (x.startswith(".") or x.endswith("jpg")),
            os.listdir(data_dir),
        )
    )

    class_names = read_class_names(args.class_csv)
    model = models.load_model(args.model, backbone_name='resnet50')
    for image in image_list:
        image_file = os.path.join(data_dir, image)
        predict_file = os.path.join(predict_dir, image)
        predict(model, class_names, image_file, predict_file)


if __name__ == "__main__":
    main()
