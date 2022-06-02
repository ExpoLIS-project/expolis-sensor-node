import math
import numpy as np
import paho.mqtt.client as mqtt
from pykalman import KalmanFilter

import configuration


class PMKalman:
    def __init__ (self):
        self.tr_mat = np.ones ((1, 1))
        self.obs_mat = np.ones ((1, 1))
        self.init_state_mean = [0]
        self.init_state_cov = [1000]
        self.tr_cov_mat = np.ones ((1, 1))
        self.obs_cov_mat = np.ones ((1, 1))
        self.filtered_state_means = np.zeros ((2, 1))
        self.filtered_state_covariances = np.zeros ((2, 1))
        self.obs = np.zeros ((2, 1))
        self.kf = KalmanFilter (
            transition_matrices=self.tr_mat,
            observation_matrices=self.obs_mat,
            transition_covariance=self.tr_cov_mat,
            observation_covariance=self.obs_cov_mat,
            initial_state_mean=self.init_state_mean,
            initial_state_covariance=self.init_state_cov,
            n_dim_state=1,
            n_dim_obs=1)
        self.iteration = 1

    # noinspection PyBroadException
    def step (self, value):
        self.obs[0] = self.obs[1]
        self.obs[1] = value
        try:
            if self.iteration > 1:
                max_obs = max (self.obs[1], self.obs[0])
                min_obs = min (self.obs[1], self.obs[0])
                self.obs_cov_mat[0] = kp + kd * math.log (max_obs / min_obs, 10)
            self.filtered_state_means[0] = self.filtered_state_means[1]
            self.filtered_state_covariances[0] = self.filtered_state_covariances[1]
            self.filtered_state_means[1], self.filtered_state_covariances[1] = self.kf.filter_update (
                self.filtered_state_means[0],
                self.filtered_state_covariances[0],
                self.obs[1],
                transition_covariance=self.tr_cov_mat,
                observation_covariance=self.obs_cov_mat)
            result = round (self.filtered_state_means[1][0], 3)
            if math.isnan (result):
                self.__init__()
                result = -1
            else:
                self.iteration += 1
        except Exception:
            self.__init__ ()
            result = -1
        return result


kp = 0
kd = 0

kp_base = 0
kd_base = 0

pm_1_kf = PMKalman ()
pm_2_5_kf = PMKalman ()
pm_10_kf = PMKalman ()


def init_kalman_filters ():
    global kp_base, kd_base

    kp_base = float (configuration.config['BASE']['kp'])
    kd_base = float (configuration.config['BASE']['kd'])


def step_kalman_filters (pm_1_value: float, pm_2_5_value: float, pm_10_value: float, sampling_period: int):
    global kp, kd

    kd = kd_base / sampling_period
    kp = kp_base / sampling_period

    return [
        pm_1_kf.step (pm_1_value),
        pm_2_5_kf.step (pm_2_5_value),
        pm_10_kf.step (pm_10_value),
    ]


def command_test_filter (mqtt_client: mqtt.Client, kp_s: str, kd_s: str):
    global kp_base, kd_base

    kp_base = float (kp_s)
    kd_base = float (kd_s)
    print ('Received test filter kp={}, kd={}'.format (kp_s, kd_s))
    mqtt_client.publish (configuration.TOPIC_LOG, 'received test filter kp={}, kd={}'.format (kp_s, kd_s), qos =2)


def command_save_filter (mqtt_client: mqtt.Client, kp_s: str, kd_s: str):
    global kp_base, kd_base

    kp_base = float (kp_s)
    kd_base = float (kd_s)
    configuration.config['BASE']['kp'] = kp_s
    configuration.config['BASE']['kd'] = kd_s
    configuration.save_config()
    print ('Received save filter kp={}, kd={}'.format (kp_s, kd_s))
    mqtt_client.publish (configuration.TOPIC_LOG, 'Received save filter kp={}, kd={}'.format (kp_s, kd_s), qos=2)
