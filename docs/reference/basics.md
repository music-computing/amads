# Classes Representing Basic Score Elements

::: amads.core.basics
    options: 
      members: []
      extra: 
        show_root_members: false
      # show_root_heading: false 

---------------

::: amads.core.basics.Event

---------------

::: amads.core.basics.Note

---------------

::: amads.core.basics.Rest

---------------

::: amads.core.basics.Measure 

---------------

::: amads.core.basics.Staff 

---------------

::: amads.core.basics.Part 

---------------

::: amads.core.basics.Score 
    options:
      extra:
        exclude-members: [staff, part, score]
      filters: ["!^staff$", "!^part$", "!^score$"]
