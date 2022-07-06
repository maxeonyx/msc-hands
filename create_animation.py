#!/usr/bin/env python

import pickle
import os

import tensorflow as tf
from tensorflow import keras
from matplotlib import pyplot as plt

from ml import predict, decoders

import config

try:
    run_name = os.environ["RUN_NAME"]
except KeyError:
    print()
    print("RUN_NAME not set. Must provide a name to run 'create_animation.py'.")
    exit(1)

model = keras.models.load_model(f"models/{run_name}", compile=False)

cfg = config.get()

x = {
    "angles": tf.zeros([cfg.test_batch_size, 0], dtype=tf.float32),
    "frame_idxs": tf.zeros([cfg.test_batch_size, 0], dtype=tf.int32),
    "hand_idxs": tf.zeros([cfg.test_batch_size, 0], dtype=tf.int32),
    "dof_idxs": tf.zeros([cfg.test_batch_size, 0], dtype=tf.int32),
}
predict_fn = predict.create_predict_fn(cfg, decoders.von_mises_dist, model)
y_pred_mean_batch, y_pred_sample_batch = predict_fn(x, 30)

from ml import viz

for y_pred_mean, y_pred_sample in zip(y_pred_mean_batch, y_pred_sample_batch):
    viz.show_animations(cfg, [y_pred_mean, y_pred_sample])
plt.show()
