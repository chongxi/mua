import numpy as np
import seaborn as sns
from vispy import scene, app
from MyWaveVisual import MyWaveVisual
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
        self.fet_method = list(['hdbscan', 'dpc', 'kmeans', 'gmm'])
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

class Axis(scene.AxisWidget):
    """from scene.AxisWidget"""
    def glpos_to_time(self, gl_pos):
        '''
        get time from the x postion of y_axis
        Important: check the affine transformation in MyWaveVisual!
        '''
        xn = np.ceil((gl_pos / 0.95 + 1) * (self.npts - 1) / 2)
        t = (xn + self._time_slice * self._time_span) / self.fs
        return t

    def _view_changed(self, event=None):
        """Linked view transform has changed; update ticks.
        """
        tr = self.node_transform(self._linked_view.scene)
        p1, p2 = tr.map(self._axis_ends())
        if self.orientation in ('left', 'right'):
            self.axis.domain = (p1[1], p2[1])
        else:
            self.axis.domain = (self.glpos_to_time(p1[0]), self.glpos_to_time(p2[0]))


class Cross(object):
    def __init__(self, cursor_color):

        self.cross_state = False
        self._time_slice = 0
        self.x_axis = Axis(orientation='bottom', text_color=cursor_color, tick_color=cursor_color, axis_color=cursor_color)
        self.x_axis.stretch = (1, 0.1)
        self.y_axis = Axis(orientation='left', text_color=(1, 1, 1, 0), tick_color=cursor_color, axis_color=cursor_color)
        self.y_axis.stretch = (0, 1)
        self.y_axis_ref = Axis(orientation='left', text_color=(1, 1, 1, 0), tick_color=(1, 1, 1, 0), axis_color=(0, 1, 1))
        self.y_axis_ref.stretch = (0, 1)

    def set_params(self, npts, fs, time_slice, time_span):
        self.x_axis.unfreeze()
        self.x_axis.npts = npts
        self.x_axis.fs = fs
        self.x_axis._time_slice = 0
        self.x_axis._time_span = npts
        self.x_axis.freeze()

        self.y_axis.unfreeze()
        self.y_axis.npts = npts
        self.y_axis.fs = fs
        self.y_axis._time_slice = 0
        self.y_axis._time_span = npts
        self.y_axis.freeze()

        self.y_axis_ref.unfreeze()
        self.y_axis_ref.npts = npts
        self.y_axis_ref.fs = fs
        self.y_axis_ref._time_slice = 0
        self.y_axis_ref._time_span = npts
        self.y_axis_ref.freeze()

    def attach(self, parent):
        parent.add_widget(self.x_axis)
        parent.add_widget(self.y_axis)
        parent.add_widget(self.y_axis_ref)

    def link_view(self, view):
        self.x_axis.link_view(view)
        self.y_axis.link_view(view)
        self.y_axis_ref.link_view(view)
        self.y_axis_ref.visible = False
        self.parentview = view

    def moveto(self, pos):
        pos = pos - self.parentview.pos - self.parentview.margin
        self.x_axis.transform.translate = (0, pos[1])
        self.y_axis.transform.translate = (pos[0], 0)

    def flip_state(self):
        if self.cross_state is True:
            self.cross_state = False
        else:
            self.cross_state = True

    def ref_enable(self, pos):
        pos = pos - self.parentview.pos - self.parentview.margin
        self.y_axis_ref.transform.translate = (pos[0], 0)
        self.y_axis_ref.visible = True

    def ref_disable(self):
        self.y_axis_ref.visible = False

    @property
    def time_slice(self):
        return self._time_slice

    @time_slice.setter
    def time_slice(self, time_slice_no):
        self._time_slice = time_slice_no
        self.x_axis._time_slice = time_slice_no
        self.x_axis._view_changed()
        self.y_axis._time_slice = time_slice_no
        self.y_axis._view_changed()



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
            base_color = np.ones((len(fet), 3))
        else:
            base_color = np.asarray([current_palette[i] if i >= 0 else (0.5, 0.5, 0.5) for i in clu])
        if rho is None:
            transparency = np.ones((len(fet), 1)) * 0.5
            edge_color = np.hstack((base_color, transparency))
        else:
            transparency = rho.reshape(-1, 1)
            edge_color = np.hstack((base_color, transparency))

        self.scatter.set_data(fet[:, :3], size=3, edge_color=edge_color, face_color=edge_color)

    def attach(self, gui):
        self.unfreeze()
        gui.add_view(self)


class view_multiwave(scene.SceneCanvas):
    def __init__(self, data, fs=25000.0, ncols=1):
        scene.SceneCanvas.__init__(self, keys=None)
        self.unfreeze()
        self.grid1 = self.central_widget.add_grid(spacing=0, bgcolor='gray',
                                                 border_color='k')
        self.view1 = self.grid1.add_view(row=0, col=0, col_span=1, margin=10, bgcolor=(0, 0, 0, 1),
                              border_color=(1, 0, 0))
        self.view1.camera = scene.cameras.PanZoomCamera()
        self.view1.camera.set_range()
        self.view1.camera.interactive = False
        self.view2 = self.grid1.add_view(row=0, col=1, col_span=8, margin=10, bgcolor=(0, 0, 0, 1),
                              border_color=(0, 1, 0))

        self.view2.camera = scene.cameras.PanZoomCamera()

        self.cursor_color = '#0FB6B6'
        self.cursor_text = scene.Text("", pos=(0, 0), italic=False, bold=True, anchor_x='left', anchor_y='center',
                                 color=self.cursor_color, font_size=24, parent=self.view2.scene)
        self.cursor_text_ref = scene.Text("", pos=(0, 0), italic=True, bold=False, anchor_x='left', anchor_y='center',
                                     color=(0, 1, 1, 1), font_size=24, parent=self.view2.scene)

        self.cursor_rect = scene.Rectangle(center=(0, 0, 0), height=1.,
                                      width=1.,
                                      radius=[0., 0., 0., 0.],
                                      color=(0.1, 0.3, 0.3, 0.5),
                                      border_width=0,
                                      border_color=(0, 0, 0, 0),
                                      parent=self.view2.scene)
        self.cursor_rect.visible = False

        self._gap_value = 1
        wav_visual = scene.visuals.create_visual_node(MyWaveVisual)
        if data.ndim == 1:
            data = data.reshape(-1,1)
        npts = data.shape[0]  # Number of samples per channel.
        nCh = data.shape[1]  # 32 channel number
        nrows = nCh / ncols
        self.waves1 = wav_visual(data, nrows, ncols, npts, ls='-', parent=self.view2.scene, gap=self._gap_value)
        self.view2.camera.set_range(x=(-1, 1), y=(-1, -0.90 + self._gap_value * 1.90))

        self.grid2 = self.view2.add_grid(spacing=0, bgcolor=(0, 0, 0, 0), border_color='k')

        self.cross = Cross(cursor_color=self.cursor_color)
        self.cross.set_params(npts,fs,0,0)
        self.cross.attach(self.grid2)
        self.cross.link_view(self.view2)

        self.timer_cursor = app.Timer(connect=self.update_cursor, interval=0.01, start=True)
        self.timer_cursor.start()

    def set_data(self, data, time_slice=0):
        self.cross.time_slice = time_slice
        self.waves1.set_data(data)


    @property
    def gap_value(self):
        return self._gap_value

    @gap_value.setter
    def gap_value(self, value):
        self._gap_value = value
        self.waves1.set_gap(self._gap_value)
        self.view2.camera.set_range(x=(-1, 1), y=(-1, -0.90 + self._gap_value * 1.90))

    def attach(self, gui):
        self.unfreeze()
        gui.add_view(self)

    def update_cursor(self, ev):
        pos = (self.cross.y_axis.pos[0], 0)
        gl_pos = self.view2.camera.transform.imap(pos)[0]
        t = self.cross.y_axis.glpos_to_time(gl_pos)
        n = np.ceil(t*self.cross.y_axis.fs)
        self.cursor_text.text = "   t0=%.6f sec, n=%d point" % (t,n)
        offset_x = self.view2.camera.transform.imap(self.cross.y_axis.pos)[0]
        _pos = self.view2.pos[1] + self.view2.size[1]*0.99 # bottom
        offset_y = self.view2.camera.transform.imap((0,_pos))[1]
        self.cursor_text.pos = (offset_x, offset_y)

        if self.cross.y_axis_ref.visible is True:
            # 1. cursor_text
            self.cursor_text_ref.visible = True
            pos_ref = (self.cross.y_axis_ref.pos[0], 0)
            gl_pos = self.view2.camera.transform.imap(pos_ref)[0]
            t_ref = self.cross.y_axis_ref.glpos_to_time(gl_pos)
            # calculate the time difference between t_ref and t
            delta_t = (t_ref - t)*1000
            self.cursor_text_ref.text = "   t1-t0=%.2f ms" % delta_t
            offset_x = self.view2.camera.transform.imap(self.cross.y_axis_ref.pos)[0]
            offset_y = self.view2.camera.transform.imap(self.cross.x_axis.pos)[1]
            self.cursor_text_ref.pos = (offset_x, offset_y)

            # 2. cursor_rect
            self.cursor_rect.visible = True
            y_axis_pos = (self.cross.y_axis.pos[0]+self.view2.margin,0)
            start_x = self.view2.camera.transform.imap(y_axis_pos)[0]
            self.cursor_rect.center = (start_x+self.cursor_rect._width/2.+self.cursor_rect._border_width ,0, 0)
            y_axis_ref_pos = (self.cross.y_axis_ref.pos[0]+self.view2.margin,0)
            end_x   = self.view2.camera.transform.imap(y_axis_ref_pos)[0]
            width = end_x - start_x
            if width <= 0:
                width = 1e-15
            self.cursor_rect.width = width
            height = self.view2.camera.transform.imap((0,-self.view2.size[1]))[1]
            self.cursor_rect.height = height*2
        else:
            self.cursor_text_ref.visible = False
            self.cursor_rect.visible = False

    def on_key_press(self, event):
        # if event.key.name == 'PageDown':
        #     print 'next page'
        if event.text == 'r':
            self.view2.camera.set_range(x=(-1, 1), y=(-1, -0.90 + self._gap_value * 1.90))
        if event.text == 'c':
            self.cross.flip_state()

    def on_mouse_move(self, event):
        modifiers = event.modifiers
        if 1 in event.buttons and modifiers is not ():
            p1 = event.press_event.pos
            p2 = event.last_event.pos
            if modifiers[0].name == 'Shift':
                self.cross.ref_enable(p2)

        elif self.cross.cross_state:
            if event.press_event is None:
                self.cross.moveto(event.pos)
                self.cross.ref_disable()


if __name__ == '__main__':
    from phy.gui import GUI, create_app, run_app
    create_app()
    gui = GUI(position=(0, 0), size=(600, 400), name='GUI')
    ##############################################
    ### Test scatter_view
    from sklearn.preprocessing import normalize
    n = 1000000
    fet = np.random.randn(n,3)
    fet = normalize(fet,axis=1)
    print fet.shape
    clu = np.random.randint(3,size=(n,1))
    scatter_view = view_scatter_3d()
    scatter_view.attach(gui)
    scatter_view.set_data(fet, clu)
    #############################################################################################
    from Binload import Binload
    ### Set Parameters ###
    filename  = 'S:/pcie.bin'
    nCh       = 32
    fs        = 25000
    numbyte   = 4
    time_span = 1 # 1 seconds
    global time_slice
    time_slice = 0
    span = time_span * fs
    highlight = True
    lf = Binload(nCh=nCh, fs=fs)
    lf.load(filename,'i'+str(numbyte), seekpos=0)
    t, data = lf.tonumpyarray()
    wave_view = view_multiwave(data[time_slice*span:(time_slice+1)*span,:], fs=25000)
    wave_view.gap_value = 0.9
    wave_view.attach(gui)

    ############################################################################################
    from phy.gui import Actions
    actions = Actions(gui)

    @actions.add(shortcut=',')
    def page_up():
        global time_slice
        time_slice -= 1
        if time_slice >= 0:
            wave_view.set_data(data[time_slice*span:(time_slice+1)*span,:], time_slice)
        else:
            time_slice = 0

    @actions.add(shortcut='.')
    def page_down():
        global time_slice
        time_slice += 1
        wave_view.set_data(data[time_slice*span:(time_slice+1)*span,:], time_slice)

    gui.show()
    run_app()


