import numpy as np

from amads.core.basics import Score
from amads.pitch.key import keysomdata as ksom
from amads.pitch.key import profiles as prof
from amads.pitch.keysom import keysom


def training_ksom_demo(test_obj):
    training_profile = prof.krumhansl_kessler
    test_obj.train_SOM(training_profile)
    return


# ! I STG they reorganized the weights or did some *very* heavy deterministic
# ! training or pretraining...
# In the current training configuration. We get the proper toroid shapes,
# and the correct "local" features, namely circle of fifths are close to each
# other as well as the thirds for major and minor.
# However, the training itself still yields labels that are super messed up
# globally (not as neat as the grid-like structure presented)
def main():
    test_SOM = ksom.KeyProfileSOM()

    training_ksom_demo(test_SOM)
    c_major_scale = np.array([60, 62, 64, 65, 67, 69, 71, 72])
    for i in range(3):
        score = Score.from_melody(list(c_major_scale + i))
        keysom(score, test_SOM)


if __name__ == "__main__":
    main()
