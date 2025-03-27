"""
NAME:
===============================
Partimenti (partimenti.py)


BY:
===============================
Mark Gotham, 2019


LICENCE:
===============================
Creative Commons Attribution-ShareAlike 4.0 International License
https://creativecommons.org/licenses/by-sa/4.0/


ABOUT:
===============================
Partimenti from the literature (broadly Gjerdingen)
in simple dicts with keys for
    "name": e.g., "Romanesca",
    "when": e.g., "Opening",
    "strong_first": bool. True if the pattern starts strong-weak, False for the opposite. (They all alternate)
    "melody": the melodic part expressed in scale degrees (int 1--7).
    "bass": the bass part expressed in scale degrees (int 1--7).
    "figures": harmony as expressed in figured bass (see toolkit issue #8).
    "note": optional.
"""

# Opening

romanesca = {
    "name": "Romanesca",
    "when": "Opening",
    "strong_first": True,
    "melody": [1, 5, 1, 1],
    "bass": [1, 7, 6, 3],
    "figures": [5, 6, 5, 6],
}
do_re_mi = {
    "name": "Do-Re-Mi",
    "when": "Opening",
    "strong_first": True,
    "melody": [1, 2, 3],
    "bass": [1, 7, 1],
    "figures": [5, 6, 5],
    "note": "invertible",
}
sol_fa_mi = {
    "name": "Sol-Fa-Mi",
    "when": "Opening",
    "strong_first": False,
    "melody": [5, 4, 4, 3],
    "bass": [1, 2, 7, 1],
    "figures": [5, 5, "6,5", 5],
}
meyer = {
    "name": "Meyer",
    "when": "Opening",
    "strong_first": False,
    "melody": [1, 7, 4, 3],
    "bass": [1, 2, 7, 1],
    "figures": [5, "6,4,3", "6,5", 5],
}
aprile = {
    "name": "Aprile",
    "when": "Opening",
    "strong_first": True,
    "melody": [1, 7, 2, 1],
    "bass": [1, 2, 7, 1],
    "figures": [5, "6,4,3", "6,5", 5],
    "note": "Happy birthday!",
}
jupiter = {
    "name": "Jupiter",
    "when": "Opening",
    "strong_first": True,
    "melody": [1, 2, 4, 3],
    "bass": [1, 7, 5, 1],
    "figures": [5, 6, 5, 5],
}
pastorella = {
    "name": "Pastorella",
    "when": "Opening",
    "strong_first": True,
    "melody": [3, 2, 4, 3],
    "bass": [1, 5, 5, 1],
    "figures": [5, 6, 5, 5],
    "note": "Thirds",
}


# Answer/Process/Transition

prinner = {
    "name": "Prinner",
    "when": "Answer/Process/Transition",
    "strong_first": True,
    "melody": [6, 5, 4, 3],
    "bass": [4, 3, 2, 1],
    "figures": [5, 6, 7, 6, 5],
}
modulating_prinner = {
    "name": "Modulating Prinner",
    "when": "Answer/Process/Transition, e.g. end of A",
    "strong_first": True,
    "melody": [3, 2, 1, 7],
    "bass": [8, 7, 6, 5],
    "figures": [5, 6, 7, "#6", 5],
}
fonte = {
    "name": "Fonte",
    "when": "Answer/Process/Transition, e.g. start of B",
    "strong_first": False,
    "melody": [5, 4, 4, 3],
    "bass": ["#1", 2, 7, 1],
    "figures": ["6,5", 5, "6,5", 5],
    "note": "Cycle of 5ths. 6,5 due to melody",
}
monte = {
    "name": "Monte",
    "when": "Answer/Process/Transition, e.g. start of B",
    "strong_first": False,
    "melody": ["1", "b7", "6", "2", "1", "7"],
    "bass": [3, 4, "#4", 5],
    "figures": [6, 5, 6, 5],
}
ponte = {
    "name": "Ponte",
    "when": "Answer/Process/Transition",
    "strong_first": True,
    "melody": [5, 7, 2],
    "bass": [5, 5, 5],
    "figures": [5, 7, 7],
}


# "Pre-Cadential" (process / transition continued):

fenaroli = {
    "name": "Fenaroli",
    "when": "Pre-Cadential",
    "strong_first": True,
    "melody": [4, 3, 7, 1],
    "bass": [7, 1, 2, 3],
    "figures": [6, 5, 6, 6],
}
indugio = {
    "name": "Indugio",
    "when": "Pre-Cadential",
    "strong_first": True,
    "melody": [2, 4, 6, 1, 7],
    "bass": [4, 4, 4, "4#", 5],
    "figures": ["6,5", "6,5", "6,5", "6,5", 5],
}
passo_indietro = {
    "name": "Passo Indietro",
    "when": "Pre-Cadential",
    "strong_first": True,
    "melody": [7, 1],
    "bass": [4, 3],
    "figures": ["6,4,2", 6],
    "note": "Step back, before a significant cadence",
}
deceptive = {
    "name": "Deceptive Cadence",
    "when": "Pre-Cadential",
    "strong_first": False,
    "melody": [1, 2, 2, 1],
    "bass": [3, 4, 5, 6],
    "figures": [6, "6,5", 5, 5],
}
evaded = {
    "name": "Evaded Cadence",
    "when": "Pre-Cadential",
    "strong_first": False,
    "melody": [1, 2, 2, 1],
    "bass": [3, 4, 5, 3],
    "figures": [6, "6,5", 5, 6],
}


# Cadential

cadenza_semplice = {
    "name": "Cadenza Semplice",
    "when": "Cadence",
    "strong_first": False,
    "melody": [1, 2, 2, 1],
    "bass": [3, 4, 5, 1],
    "figures": [6, "6,5", 5, 5],
}
cadenza_composta = {
    "name": "Cadenza Composta",
    "when": "Cadence",
    "strong_first": True,
    "melody": [1, 2, 3, 2, 1],
    "bass": [3, 4, 5, 5, 1],
    "figures": [6, "6,5", "6,4", 7, 5],
}
cadenza_doppia = {
    "name": "Cadenza Doppia",
    "when": "Cadence",
    "strong_first": True,
    "melody": [4, 3, 2, 2, 1],
    "bass": [5, 5, 5, 5, 1],
    "figures": [5, "6,4", 4, 3, 5],
    "relatedTo": ["Comma", "Complete"],
}
complete = {
    "name": "Complete Cadence",
    "when": "Cadence",
    "strong_first": False,
    "melody": [3, 2, 2, 1],
    "bass": [1, 4, 5, 1],
    "figures": [5, "6,5", 5, 5],
}


# More Cadences (partial / incomplete)

comma = {
    "name": "Comma",
    "when": "Cadence",
    "strong_first": False,
    "melody": [4, 3],
    "bass": [7, 1],
    "figures": ["6,5", 5],
}
converging = {
    "name": "Converging Cadence",
    "when": "Cadence",
    "strong_first": False,
    "melody": [3, 2, 1, 7],
    "bass": ["3", "4", "#4", "5"],
    "figures": [6, "6,5", "6,5", 5],
}


# Post Cadence

quiescenza = {
    "name": "Quiescenza",
    "when": "Post-Cadential",
    "strong_first": False,
    "melody": ["b7", "6", "7", "1"],
    "bass": [1, 1, 1, 1],
    "figures": ["b7", "6,4", "7,4,2", 5],
}
