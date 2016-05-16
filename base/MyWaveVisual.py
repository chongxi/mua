# Define a simple vertex shader. We use $template variables as placeholders for
# code that will be inserted later on. In this example, $position will become
# an attribute, and $transform will become a function. Important: using
# $transform in this way ensures that users of this visual will be able to
# apply arbitrary transformations to it.
from vispy import app, gloo, visuals, scene, keys
from vispy.util import ptime
import numpy as np

VERT_SHADER = """
#version 120

// y coordinate of the position.
attribute float y;

// row, col, and time index.
attribute vec3 a_index;
varying vec3 v_index;

// Size of the table.
uniform vec2 u_size;

// Number of samples per signal.
uniform float u_npts;

// Vertical gap
uniform float u_gap;

// Color.
attribute vec4 a_color;
varying vec4 v_color;

void main() {
    float nrows = u_size.x;
    float ncols = u_size.y;

    // Compute the x coordinate from the time index.
    float x = -1 + 2*a_index.z / (u_npts-1);
    vec2 position = vec2(x, y);

    // Find the affine transformation for the subplots.
    vec2 a = vec2(1./ncols, 1./nrows)*.95;
    vec2 b = vec2(-1 + 2*(a_index.x+.5) / ncols,
                  -1 + 2*(a_index.y * u_gap+.5) / nrows);

    // Apply the static subplot transformation + scaling.
    gl_Position = $transform(vec4(a*position+b, 0.0, 1.0));
    gl_PointSize = 4.5;
    v_color = a_color;
    v_index = a_index;

}
"""

# Very simple fragment shader. Again we use a template variable "$color", which
# allows us to decide later how the color should be defined (in this case, we
# will just use a uniform red color).

FRAG_SHADER = """
#version 120

varying vec4 v_color;
varying vec3 v_index;

void main() {
    gl_FragColor = v_color;

    // Discard the fragments between the signals (emulate glMultiDrawArrays).
    if ((fract(v_index.x) > 0.) || (fract(v_index.y) > 0.))
        discard;

}
"""

# Start the new Visual class.
# By convention, all Visual subclass names end in 'Visual'.
# (Custom visuals may ignore this convention, but for visuals that are built
# in to vispy, this is required to ensure that the VisualNode subclasses are
# generated correctly.)
class MyWaveVisual(visuals.Visual):
    """Visual that draws a red rectangle.

    Parameters
    ----------
    x : float
        x coordinate of rectangle origin
    y : float
        y coordinate of rectangle origin
    w : float
        width of rectangle
    h : float
        height of rectangle

    All parameters are specified in the local (arbitrary) coordinate system of
    the visual. How this coordinate system translates to the canvas will
    depend on the transformation functions used during drawing.
    """

    # There are no constraints on the signature of the __init__ method; use
    # whatever makes the most sense for your visual.
    def __init__(self, data, nrows, ncols, npts, color=None, ls='-', gap=1):
        # Initialize the visual with a vertex shader and fragment shader
        visuals.Visual.__init__(self, VERT_SHADER, FRAG_SHADER)

        nCh = nrows*ncols
        self.unfreeze()
        self.nCh = nCh
        self.npts = npts
        # self._scale = float(2**14)*300.0  # 14 bits binary point (14 bits represent fractional part)
                                          # -200 uV = -1 unit in this y-axis  
        # index is (#cols*#rows*#npts, 3)
        # each row of index is (col_idx, row_idx, npts_idx) 
        # (col,row):
        # (0,0)->(0,1)->(0,2)->(0,3)->(0,4)-...->(0,7)->(1,0)->(1,1)-...->(1,7)
        # index = np.c_[np.repeat(np.repeat(np.arange(ncols), nrows), npts),
        #               np.repeat(np.tile(np.arange(nrows), ncols), npts),
        #               np.tile(np.arange(npts), nCh)].astype(np.float32)

        # (col,row):
        # (0,0)->(1,0)->(0,1)->(1,1)->(0,2)->(1,2)...->(0,7)->(1,7)
        index = np.c_[np.repeat(np.tile(np.arange(ncols), nrows), npts),
                      np.repeat(np.arange(nrows), ncols*npts),
                      np.tile(np.arange(npts), nCh)].astype(np.float32)
        
        if color is 'random':
            self.color = np.repeat(np.random.uniform(size=(nCh, 4), low=.2, high=.9),
                              npts, axis=0).astype(np.float32)            
        elif color is None:
            self.color = np.repeat(np.ones((nCh,4)),
                              npts, axis=0).astype(np.float32)
        else:
            self.color = color

        data = data.astype('float32')
        self._scale = -data.min()*.5
        self.data = data.T.ravel()/self._scale
        # print 'max:',data.max()
        self.shared_program['y'] = self.data
        self.shared_program['a_color'] = self.color
        self.shared_program['a_index'] = index
        self.shared_program['u_size'] = (nrows, ncols)
        self.shared_program['u_npts'] = npts
        self.shared_program['u_gap'] = gap
        # self.shared_program['clip'] = 1.0

        # self.shared_program.vert['position'] = self.vbo
        # self.shared_program.frag['color'] = (0, 1, 0, 1)
        if ls == '.':
            self._draw_mode = 'points' 
        elif ls == '-':
            self._draw_mode = 'line_strip'

        # self.pcie_open = False
        # self.pcie_read_open()
        # self.timer0 = app.Timer(interval=0, connect=self._timer_data, start=False)
        self.timer1 = app.Timer(interval=0, connect=self._timer_show, start=False)
        # self._last_time = 0
        self.freeze()

    def _prepare_transforms(self, view):
        # This method is called when the user or the scenegraph has assigned
        # new transforms to this visual (ignore the *view* argument for now;
        # we'll get to that later). This method is thus responsible for
        # connecting the proper transform functions to the shader program.

        # The most common approach here is to simply take the complete
        # transformation from visual coordinates to render coordinates. Later
        # tutorials detail more complex transform handling.
        view.view_program.vert['transform'] = view.get_transform()

    def _timer_show(self, ev):
        self.data = self.data.astype('float32')
        self.shared_program['y'] = self.data.reshape(-1,self.nCh).T.ravel()/300
        self.update()

    def highlight(self, spacial_code, temporal_code, highlight_color=None):
        '''
        highlight segment of the signals in one or several channels
        group of channels is defined in spacial_code: (0,2,4,6) means ch0,ch2,ch4,ch6
        segment of signal is defined in temporal_code: (n0, n1) means from point n0 to point n1
        there can be many rows of temporal_code coressponding to several segments: [[n0,n1],[n2,n3]...]
        '''
        if highlight_color is None:
            highlight_color = (0,1,0,1)
        # npts = self.color.shape[0]/self.nCh
        for chNo in spacial_code:
            for nrange in temporal_code:
                n0, n1 = nrange   # from n0 to n1
                start  = n0+chNo*self.npts
                end    = n1+chNo*self.npts
                self.color[start:end,:] = np.asarray(highlight_color)       
        self.shared_program['a_color'] = self.color
        self.update()

    # def highlight_ch(self, ch, highlight_color=None):
    #     '''
    #     highlight segment of the signals in one or several channels
    #     group of channels is defined in spacial_code: (0,2,4,6) means ch0,ch2,ch4,ch6
    #     segment of signal is defined in temporal_code: (n0, n1) means from point n0 to point n1
    #     there can be many rows of temporal_code coressponding to several segments: [[n0,n1],[n2,n3]...]
    #     '''
    #     if highlight_color is None:
    #         highlight_color = (1,1,1,1)
    #     npts = self.color.shape[0]/self.nCh
    #     for chNo in spacial_code:
    #         for nrange in temporal_code:
    #             n0, n1 = nrange
    #             start  = n0+chNo*npts
    #             end    = n1+chNo*npts
    #             self.color[start:end,:] = np.asarray(highlight_color)
    #             self.shared_program['a_color'] = self.color
    #             self.update()


    def highlight_cancel(self):
        self.color = np.repeat(np.ones((self.nCh,4)),
                                        self.npts, axis=0).astype(np.float32)
        self.shared_program['a_color'] = self.color
        self.update()

    def highlight_spikes(self, highlight_list, color=(0,1,0,1)):
        pre_peak  = 5
        post_peak = 5
        for tup in highlight_list:
            temporal_code = [[tup[0]-pre_peak, tup[0]+post_peak]]
            # print temporal_code
            spacial_code = [tup[1],]
            # print spacial_code
            self.highlight(spacial_code, temporal_code, color)

    def set_data(self, data):
        self.data = data.astype('float32')
        self.shared_program['y'] = self.data.T.ravel()/self._scale
        self.update()
        self.highlight_cancel()
        # self.shared_program['a_color'] = np.repeat(np.ones((self.nCh,3)),
        #                                  self.npts, axis=0).astype(np.float32)
        self.update()



    def append_data(self, data):
        newdata = data.astype('float32')
        newdata = newdata.T.ravel()/self._scale
        self.shared_program['y'] = np.hstack((self.data, newdata))
        self.update()
        
    def set_gap(self, gap):
        self.shared_program['u_gap'] = gap
        self.update()
