"""
Root analysis (after Parncutt)
==============================

This example demonstrates how we can analyze the root of a chord using the `parncutt` module.
"""

# %%
from amads.harmony.root_finding.parncutt import ParncuttRootAnalysis

# %%
c_major_triad = ParncuttRootAnalysis([60, 64, 67])
print(f"Root: {c_major_triad.root}")
print(f"Root ambiguity: {c_major_triad.root_ambiguity}")
plt, fig = c_major_triad.visualize()
plt.show()

# %%
f_minor_triad = ParncuttRootAnalysis([60, 65, 67])
print(f"Root: {f_minor_triad.root}")
print(f"Root ambiguity: {f_minor_triad.root_ambiguity}")
plt, fig = f_minor_triad.visualize()
plt.show()

# %%
d_diminished_triad = ParncuttRootAnalysis([62, 65, 68])
print(f"Root: {d_diminished_triad.root}")
print(f"Root ambiguity: {d_diminished_triad.root_ambiguity}")
plt, fig = d_diminished_triad.visualize()
plt.show()
