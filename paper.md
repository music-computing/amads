---
title: Algorithms for Music Analysis and Data Science (AMADS)
tags:
  - music
  - scores
  - algorithms
  - data science
authors:
  - name: Mark R. H. Gotham
    orcid: 
    corresponding: true # (This is how to denote the corresponding author)
    equal-contrib: true
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Peter Harrison
    orcid: 
    equal-contrib: true
    affiliation: 2
  - name: Tuomas Eerola
    orcid: 
    equal-contrib: true
    affiliation: 3
  - name: Roger Dannenberg
    orcid: 
    equal-contrib: true
    affiliation: 4
affiliations:
 - name: KCL, England
   index: 1
 - name: Cambridge, England
   index: 2
 - name: Durham, England
   index: 3
 - name: CMU, United States of America
   index: 4
date: 2024
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
aas-doi: 10.3847/xxxxx <- update this with the DOI from AAS once you know it.
aas-journal: Astrophysical Journal <- The name of the AAS journal.
---


# Summary

A great deal of our musical heritage exists survives 
in sheet music: scores with notes, rests, dynamics, articulation, and the like.
The equivalent digital encoding is generally called "symbolic" music.
And while some may associate this with Western classical music,
it serves styles and repertoires far beyond that (jazz leadsheets, Korean traditional music, …).

The last few decades have seen a growing body of work focused on this data,
and therefore the emergence of several algorithms.
Algorithms for Music Analysis and Data Science (AMADS)
aims to provide a summary of those algorithms,
bringing them together in a coherent way in relation to new standards for encoding.
In so doing, it also fills in some gaps that this process identifies,
and expands into some new areas.


# Statement of need

We begin with some high-level observations will serve to provide the context and motivation for this topic.
* Music computing is not a large field. There are wonderful, enthusiastic practitioners, 
    but rather few of us relatively to more populous fields.
* Related, music computing is somewhat disparate, with those practitioners spread out across the world, 
    and with sub-fields like MIR, music theory, and music psychology having rather limited interaction, 
    at least relative to the clearly shared goals, tasks, and data.
* Educational resources can serve not only as material for preparing specific classes,
    but also as a vehicle for consolidating the field
    e.g., textbooks can function both for teaching and as reference books for experts.
* Code libraries can likewise serve as another gathering point,
    supporting both newcomers with 'how to' guides and consolidating the field for expert practitioners.

While some parts of the music computing landscape
are relatively well served with code libraries
(e.g., tool-based libraries for extracting data from audio),
relatively little exists by way of libraries consolidating algorithms for research,
and the coverage varies across music computing.

There are several promising initiatives that draw together algorithms in a particular area.
These include
"OMNISIA" (Meredith et al. for pattern finding in Java),
"synpy" (Song et al., for rhythmic syncopation in Python).
and the ["midi toolbox"](https://www.jyu.fi/hytk/fi/laitokset/mutku/en/research/materials/miditoolbox)
(Toiviainen and Eerola, for melodic contour and more in Matlab).
These are welcome efforts, but they all come from 
different research groups,
are expressed in different code languages,
and in at least some cases, are no longer maintained.

Then there are larger libraries that could serve to draw this together.
At one time [humdrum](https://www.humdrum.org/) was a/the central point of reference. 
That continues to be used and maintained (an impressive 40 years later!),
but there are downsides, e.g., the 'language neutral' set up is commendable,
but not very inviting for newcomers with the expectations based on the landscape of 2024.

Later, along came [music21](https://github.com/cuthbertLab/music21).
First published in 2010/11, this too continues to be maintained and used.
That said, the creator-maintainer recently made the
[explicit decision (announced/reported here)](https://groups.google.com/g/music21list/c/HF3tgkMvNWI/m/7vaIHr88BAAJ)
that it is _not_ / _no longer_ there to provide the holistic directory function stated here.
Instead, it specifically invites niche projects to go solo, with or without music21 as a dependency.

[Partitura](https://partitura.readthedocs.io/en/latest/)
is arguably one such project,
though it explicitly suggests using music21 instead if
“you are working in computational musicology”.

Students and researchers wishing to "get into" a topic,
therefore have to do a lot of "spade-work" to compare any new algorithm with existing work,
or even to make use of those existing algorithms.
In short, 
given this state of affairs, and following conversation with the maintainers of all those code libraries,
it is clear that we need a new coordination effort
drawing together the work cited above at a higher level.

AMADS seeks to address this need, serving primarily to bring together these algorithms.
We seek to be user-friendly as possible,
serving as a welcoming introduction to those new to the field,
and a helpful reference library for those already active.

Moreover, we aim to:
* credit that previous work carefully,
* "fill in the gaps" with new implementations where none are readily available, and 
* expand into uncharted territory (alongside ongoing, separately published research).


# Acknowledgements

We strive to cite all involved in the research gathered here.
All contributors to the new repository appear in the commit history
and are generally listed as authors of the respective files.
The design of this code library is informed by conversations with all relevant precedents
(including those cited above).
Many thanks to those developers, and to the new ones.
Finally, we thank Dagstuhl for supporting
[seminar number 24302](https://www.dagstuhl.de/en/seminars/seminar-calendar/seminar-details/24302)
which helped advance these plans.


# References

