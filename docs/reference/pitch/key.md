The ``amads.pitch.key`` package implements MIDI Toolbox-style key finding and
related tools. Literature key profiles are defined in
[`profiles`](#amads.pitch.key.profiles) as :class:`~amads.pitch.key.profiles.KeyProfile`
objects (see ``source_list`` in that module). MIDI Toolbox ``refstat('kkmaj')``
and ``refstat('kkmin')`` correspond to
[`krumhansl_kessler`](#amads.pitch.key.profiles.krumhansl_kessler) ``.major`` /
``.minor`` weights; :func:`~amads.pitch.key.tonality.tonality` uses those via
:func:`~amads.pitch.key.keymode.keymode` instead of ``refstat``.

To convert MIDI Toolbox key codes (1--24) to text, use
[`keyname`](#amads.pitch.key.keyname.keyname).

::: amads.pitch.key.profiles
    options: 
      members: False 

----------------

::: amads.pitch.key.profiles.PitchProfile 

----------------

::: amads.pitch.key.profiles.KeyProfile

----------------

::: amads.pitch.key.transpose2c
    options:
      members: False 

----------------

::: amads.pitch.key.transpose2c.transpose2c 

----------------

::: amads.pitch.key.kkkey
    options:
      members: False 

----------------

::: amads.pitch.key.kkkey.kkkey

----------------

::: amads.pitch.key.keymode
    options:
      members: False 
      
----------------

::: amads.pitch.key.keymode.keymode

----------------

::: amads.pitch.key.keyname.keyname

----------------

::: amads.pitch.key.tonality.tonality

----------------

::: amads.pitch.key.key_cc 
    options:
      members: False 
      
----------------

::: amads.pitch.key.key_cc.key_cc

----------------

::: amads.pitch.key.kkcc 
    options: 
      members: False 

----------------

::: amads.pitch.key.kkcc.kkcc

----------------

::: amads.pitch.key.max_key_cc 
    options:
      members: False 

----------------

::: amads.pitch.key.max_key_cc.max_key_cc

----------------

::: amads.pitch.key.keysom 
    options:
      members: False 

----------------

::: amads.pitch.key.keysom.keysom

----------------

::: amads.pitch.key.keysomdata 
    options: 
      members: False 

----------------

::: amads.pitch.key.keysomdata.KeyProfileSOM

----------------

::: amads.pitch.key.keysomdata.pretrained_weights_script

----------------

::: amads.pitch.key.keysomdata.zero_SOM_init

----------------

::: amads.pitch.key.keysomdata.random_SOM_init

----------------

::: amads.pitch.key.keysomdata.handcrafted_SOM_init

----------------

::: amads.pitch.key.keysomdata.keysom_inverse_decay

----------------

::: amads.pitch.key.keysomdata.keysom_stepped_inverse_decay

----------------

::: amads.pitch.key.keysomdata.keysom_stepped_log_inverse_decay

----------------

::: amads.pitch.key.keysomdata.keysom_centroid_euclidean

----------------

::: amads.pitch.key.keysomdata.keysom_toroid_euclidean

----------------
::: amads.pitch.key.keysomdata.keysom_toroid_clamped


