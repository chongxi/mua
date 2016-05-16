import seaborn as sns
import numpy as np
from vispy import scene
from PyQt4 import QtGui, QtCore

class ObjectWidget(QtGui.QWidget):
    """
    Widget for editing OBJECT parameters
    """
    signal_objet_changed = QtCore.pyqtSignal(name='objectChanged')

    def __init__(self, parent=None):
        super(ObjectWidget, self).__init__(parent)

        l_fet_method = QtGui.QLabel("feature")
        self.fet_method = list(['pca', 'peak'])
        self.fet_combo = QtGui.QComboBox(self)
        self.fet_combo.addItems(self.fet_method)
        self.fet_combo.currentIndexChanged.connect(self.update_param)

        l_clu_method = QtGui.QLabel("clutering")
        self.fet_method = list(['hdbscan', 'dpc','kmeans', 'gmm'])
        self.clu_combo = QtGui.QComboBox(self)
        self.clu_combo.addItems(self.fet_method)
        self.clu_combo.currentIndexChanged.connect(self.update_param)
        
        l_ch = QtGui.QLabel("Channel")
        self.ch = QtGui.QSpinBox()
        self.ch.setMinimum(0)
        self.ch.setMaximum(31)
        self.ch.setValue(26)
        self.ch.valueChanged.connect(self.update_param)

        gbox = QtGui.QGridLayout()
        gbox.addWidget(l_fet_method, 0, 0)
        gbox.addWidget(self.fet_combo, 0, 1)
        gbox.addWidget(l_clu_method, 1, 0)
        gbox.addWidget(self.clu_combo, 1, 1)        
        gbox.addWidget(l_ch, 2, 0)
        gbox.addWidget(self.ch, 2, 1)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(gbox)
        vbox.addStretch(1.0)

        self.setLayout(vbox)

    def update_param(self, option):
        self.signal_objet_changed.emit()


class view_scatter_3d(scene.SceneCanvas):

    def __init__(self):
        scene.SceneCanvas.__init__(self, keys=None)
        self.unfreeze()
        self.view = self.central_widget.add_view()
        self.view.camera = 'turntable'
        self.scatter = scene.visuals.Markers()
        self.view.add(self.scatter)
        self.freeze()

        # Add a 3D axis to keep us oriented
        scene.visuals.XYZAxis(parent=self.view.scene)

    def set_data(self, fet, clu, rho=None):
        current_palette = sns.color_palette()
        # set the color for density and clustering
        if clu is None:
            base_color = np.ones((len(fet),3))
        else:
            base_color = np.asarray([current_palette[i] if i>=0 else (0.5,0.5,0.5) for i in clu])
        if rho is None:
            transparency = np.ones((len(fet),1))*0.7
            edge_color = np.hstack((base_color, transparency))
        else:
            transparency = rho.reshape(-1,1)
            edge_color = np.hstack((base_color, transparency))
            
        self.scatter.set_data(fet[:,:3], size=3, edge_color=edge_color, face_color=edge_color)


