# Benchmarks for the solid solution class
import os.path, sys
sys.path.insert(1,os.path.abspath('../..'))

import burnman
from burnman import minerals
from burnman.processchemistry import *

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

atomic_masses=read_masses()


'''
Solvus shapes (a proxy for Gibbs free energy checking
'''

# van Laar parameter
# Figure 2a of Holland and Powell, 2003

# Temperature dependence
# Figure 2b of Holland and Powell, 2003

# A specific solvus example: sanidine-high albite
# Includes asymmetry and pressure, temperature dependence
# Figure 3 of Holland and Powell, 2003


'''
Excess properties
'''
# Configurational entropy
# Navrotsky and Kleppa, 1967
class o_d_spinel(burnman.SolidSolution):
    def __init__(self):
        # Name
        self.name='orthopyroxene'

        # Endmembers (cpx is symmetric)
        endmembers = [[minerals.HP_2011_ds62.sp(), '[Mg][Al]2O4'],[minerals.HP_2011_ds62.sp(), '[Al][Mg1/2Al1/2]2O4']]

        # Interaction parameters
        enthalpy_interaction=[[0.0]]

        burnman.SolidSolution.__init__(self, endmembers, \
                          burnman.solutionmodel.SymmetricRegularSolution(endmembers, enthalpy_interaction) )

comp = np.linspace(0.001, 0.999, 100)
sp=o_d_spinel()
sp_entropies = np.empty_like(comp)
sp_entropies_NK1967= np.empty_like(comp)
for i,c in enumerate(comp):
        molar_fraction=[1.0-c, c]
        sp.set_composition( np.array(molar_fraction) )
        sp.set_state( 1e5, 298.15 )
        sp_entropies[i] = sp.solution_model._configurational_entropy( molar_fraction )
        sp_entropies_NK1967[i] = -8.3145*(c*np.log(c) + (1.-c)*np.log(1.-c) + c*np.log(c/2.) + (2.-c)*np.log(1.-c/2.)) # eq. 7 in Navrotsky and Kleppa, 1967.

#fig1 = mpimg.imread('configurational_entropy.png')  # Uncomment these two lines if you want to overlay the plot on a screengrab from SLB2011
#plt.imshow(fig1, extent=[0.0, 1.0,0.,17.0], aspect='auto')
plt.plot( comp, sp_entropies_NK1967, 'b-', linewidth=3.)
plt.plot( comp, sp_entropies, 'r--', linewidth=3.)
plt.xlim(0.0,1.0)
plt.ylim(0.,17.0)
plt.ylabel("Configurational entropy of solution (J/K/mol)")
plt.xlabel("fraction inverse spinel")
plt.show()

# Configurational entropy
# Figure 3b of Stixrude and Lithgow-Bertelloni, 2011


class orthopyroxene_red(burnman.SolidSolution):
    def __init__(self):
        # Name
        self.name='orthopyroxene'

        # Endmembers (cpx is symmetric)
        endmembers = [[minerals.SLB_2011.enstatite(), 'Mg[Mg][Si]SiO6'],[minerals.SLB_2011.mg_tschermaks(), 'Mg[Al][Al]SiO6'] ]

        # Interaction parameters
        enthalpy_interaction=[[0.0]]

        burnman.SolidSolution.__init__(self, endmembers, \
                          burnman.solutionmodel.SymmetricRegularSolution(endmembers, enthalpy_interaction) )
class orthopyroxene_blue(burnman.SolidSolution):
    def __init__(self):
        # Name
        self.name='orthopyroxene'

        # Endmembers (cpx is symmetric)
        endmembers = [[minerals.SLB_2011.enstatite(), 'Mg[Mg]Si2O6'],[minerals.SLB_2011.mg_tschermaks(), 'Mg[Al]AlSiO6'] ]

        # Interaction parameters
        enthalpy_interaction=[[0.0]]

        burnman.SolidSolution.__init__(self, endmembers, \
                          burnman.solutionmodel.SymmetricRegularSolution(endmembers, enthalpy_interaction) )

class orthopyroxene_long_dashed(burnman.SolidSolution):
    def __init__(self):
        # Name
        self.name='orthopyroxene'

        # Endmembers (cpx is symmetric)
        endmembers = [[minerals.SLB_2011.enstatite(), 'Mg[Mg]Si2O6'],[minerals.SLB_2011.mg_tschermaks(), '[Mg1/2Al1/2]2AlSiO6'] ]

        # Interaction parameters
        enthalpy_interaction=[[10.0e3]]

        burnman.SolidSolution.__init__(self, endmembers, \
                          burnman.solutionmodel.SymmetricRegularSolution(endmembers, enthalpy_interaction) )

class orthopyroxene_short_dashed(burnman.SolidSolution):
    def __init__(self):
        # Name
        self.name='orthopyroxene'

        # Endmembers (cpx is symmetric)
        endmembers = [[minerals.SLB_2011.enstatite(), 'Mg[Mg][Si]2O6'],[minerals.SLB_2011.mg_tschermaks(), 'Mg[Al][Al1/2Si1/2]2O6'] ]

        # Interaction parameters
        enthalpy_interaction=[[0.0]]

        burnman.SolidSolution.__init__(self, endmembers, \
                          burnman.solutionmodel.SymmetricRegularSolution(endmembers, enthalpy_interaction) )

comp = np.linspace(0, 1.0, 100)
opx_models=[orthopyroxene_red(), orthopyroxene_blue(), orthopyroxene_long_dashed(), orthopyroxene_short_dashed()]
opx_entropies = [ np.empty_like(comp) for model in opx_models ]
for idx, model in enumerate(opx_models):
    for i,c in enumerate(comp):
        molar_fraction=[1.0-c, c]
        model.set_composition(np.array(molar_fraction))
        model.set_state(0., 0.)
        opx_entropies[idx][i] = model.solution_model._configurational_entropy(molar_fraction)

fig1 = mpimg.imread('configurational_entropy.png')  # Uncomment these two lines if you want to overlay the plot on a screengrab from SLB2011
plt.imshow(fig1, extent=[0.0, 1.0,0.,17.0], aspect='auto')
plt.plot( comp, opx_entropies[0], 'r--', linewidth=3.)
plt.plot( comp, opx_entropies[1], 'b--', linewidth=3.)
plt.plot( comp, opx_entropies[2], 'g--', linewidth=3.)
plt.plot( comp, opx_entropies[3], 'g-.', linewidth=3.)
plt.xlim(0.0,1.0)
plt.ylim(0.,17.0)
plt.ylabel("Configurational entropy of solution (J/K/mol)")
plt.xlabel("cats fraction")
plt.show()

# Excess volume of solution

# Excess enthalpy of solution
# Figure 5 of Stixrude and Lithgow-Bertelloni, 2011
class clinopyroxene(burnman.SolidSolution):
    def __init__(self):
        # Name
        self.name='clinopyroxene'

        # Endmembers (cpx is symmetric)
        endmembers = [[minerals.SLB_2011.diopside(), '[Ca][Mg][Si]2O6'],[minerals.SLB_2011.ca_tschermaks(), '[Ca][Al][Si1/2Al1/2]2O6'] ]

        # Interaction parameters
        enthalpy_interaction=[[26.e3]]
        alphas = np.array( [1.0, 3.5] ) 

        burnman.SolidSolution.__init__(self, endmembers, \
                          burnman.solutionmodel.AsymmetricRegularSolution(endmembers, alphas, enthalpy_interaction) )



cpx = clinopyroxene()

comp = np.linspace(0, 1.0, 100)
gibbs = np.empty_like(comp)

for i,c in enumerate(comp):
   cpx.set_composition( np.array([1.0-c, c]) )
   cpx.set_state( 0., 0. )
   gibbs[i] = cpx.excess_gibbs


fig1 = mpimg.imread('dicats.png')  # Uncomment these two lines if you want to overlay the plot on a screengrab from SLB2011
plt.imshow(fig1, extent=[0.0, 1.0,-2.,8.0], aspect='auto')

plt.plot( comp, gibbs/1000., 'b--', linewidth=3.)
plt.xlim(0.0,1.0)
plt.ylim(-2.,8.0)
plt.ylabel("Excess enthalpy of solution (kJ/mol)")
plt.xlabel("cats fraction")
plt.show()
