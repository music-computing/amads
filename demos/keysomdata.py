from amads.core.basics import Score
from amads.pitch.key import keysomdata as ksom
from amads.pitch.key import profiles as prof

# TODO: Demo for keysomdata here
from amads.pitch.keysom import keysom


def training_ksom_demo(test_obj):
    training_profile = prof.krumhansl_kessler
    test_obj.train_SOM(training_profile)
    return


# ! I STG they reorganized the weights or did some *very* heavy deterministic
# ! training or pretraining...
# in the current training configuration, we get a fairly decent result with
# regards to the heatmap highlighting towards the correct key
# However, the organization of the labels is very very random.
# The original probably had some very particular weights before training.
# Extra care needs to be taken in initializing the pretrained weights in a way
# that allows the labels to take a very neat configuration post training...
def main():
    test_SOM = ksom.KeyProfileSOM()

    training_ksom_demo(test_SOM)
    score = Score.from_melody([60, 62, 64, 65, 67, 69, 71, 72])
    keysom(score, test_SOM)


if __name__ == "__main__":
    main()
