import numpy as np

from amads.core.basics import Score
from amads.pitch.key import keysomdata as ksom
from amads.pitch.key import profiles as prof
from amads.pitch.keysom import keysom
from amads.pitch.pcdist1 import pcdist1


def training_ksom_demo():
    test_SOM = ksom.KeyProfileSOM()
    training_profile = prof.krumhansl_kessler
    test_SOM.train_SOM(training_profile)
    return test_SOM


def handcrafted_ksom_demo():
    return ksom.pretrained_weights_script()


def from_pretrained_weights_demo():
    return ksom.KeyProfileSOM.from_trained_SOM()


def project_and_visualize_demo(test_SOM, score_list):
    for score in score_list:
        keysom(score, test_SOM)


def project_and_animate_demo(test_SOM, score_list):
    pcdist_list = [tuple(pcdist1(score)) for score in score_list]
    # this is to test outliers
    projection_list, animation = test_SOM.project_and_animate(pcdist_list)


def main():
    test_SOM = from_pretrained_weights_demo()

    c_major_scale = np.array([60, 62, 64, 65, 67, 69, 71, 72])
    score_list = [Score.from_melody(list(c_major_scale + i)) for i in range(12)]
    project_and_visualize_demo(test_SOM, score_list[:2])


if __name__ == "__main__":
    main()
