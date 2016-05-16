# -*- coding: utf-8 -*-
"""
Created on Thu May 12 13:44:39 2016

@author: chongxi lai
"""

#%%
from MUA import *
from Vis import ObjectWidget, view_scatter_3d
from phy.plot import View
from phy.plot.interact import Grid
from hdbscan import HDBSCAN
import phy
from phy.gui import GUI
import seaborn as sns

mua = MUA(filename='S:/pcie.bin', nCh=32, fs=25000, numbytes=4)
spk = mua.tospk()
fet = spk.tofet('pca')



#%%
gui = GUI(position=(0, 0), size=(600, 400), name='GUI')
props = ObjectWidget()
gui.add_view(props,position='left', name='params')
scatter_view = view_scatter_3d()
scatter_view.unfreeze()
gui.add_view(scatter_view)
spk_view = View('grid')
gui.add_view(spk_view)

