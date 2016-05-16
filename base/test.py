from MUA import *
from xview import view_scatter_3d
from phy.plot import View
from hdbscan import HDBSCAN
import phy
from phy.gui import GUI
import seaborn as sns
import vispy.scene
from vispy.scene import visuals
from vispy.visuals.transforms import STTransform
phy.gui.create_app()


mua = MUA(filename='S:/pcie.bin')
spk = mua.tospk()
fet = spk.tofet('pca')


# spike sort a channel centered spiking events
ch = 26
min_cluster_size = 5
leaf_size = 10

hdbcluster = HDBSCAN(min_cluster_size=min_cluster_size, 
                     leaf_size=leaf_size,
                     gen_min_span_tree=True, 
                     algorithm='boruvka_kdtree')
clu = hdbcluster.fit_predict(fet[ch])
print 'get clusters', np.unique(clu)


#
from phy.gui import GUI, create_app, run_app
create_app()
gui = GUI(position=(400, 200), size=(600, 400))

scatter_view = view_scatter_3d()
scatter_view.attach(gui)
scatter_view.set_data(fet[ch], clu)


nclu = len(np.unique(clu))
view = View(layout='grid',  shape=(3, nclu))
gui.add_view(view)
palette = sns.color_palette()

view.clear()
for chNo in range(3):
    for clu_id in np.unique(clu):
        color = palette[clu_id] if clu_id>=0 else np.array([1,1,1])
        view[chNo,clu_id+1].plot(y=spk[ch][clu==clu_id,:,chNo].squeeze(),
                                              color = np.hstack((color, 0.2)),
                                              data_bounds=(-2, -1800, 2, 800))
view.build()


gui.show()
run_app()
