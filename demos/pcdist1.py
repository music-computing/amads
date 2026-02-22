from amads.all import pitch_class_distribution_1, read_score
from amads.music import example

# for some reason, could not open file with just the relative path
my_midi_file = example.fullpath("midi/sarabande.mid")
assert my_midi_file is not None

print("------- input from partitura")
myscore = read_score(my_midi_file, show=False)
myscore.show()
print("------- finished input from partitura")


print("------- Calculate pitch-class distribution")
pcd = pitch_class_distribution_1(myscore)
plot = pcd.plot(show=False)
plot.show()
