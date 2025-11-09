from amads.pitch.key import keysomdata as ksom
from amads.pitch.key import profiles as prof

# TODO: Demo for keysomdata here
# from amads.pitch.keysom import keysom


def training_ksom_demo():
    # TODO: write a demo training KeyProfileSOM on KrumhanslKessler
    training_profile = prof.krumhansl_kessler
    test = ksom.KeyProfileSOM()
    test.train_SOM(training_profile)
    return
