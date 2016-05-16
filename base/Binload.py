import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class Binload(object):
    '''
    load bin file data with file format
    init the nCh and fs when create the instance

    bf = Binload(nCh=16,fs=30000)
    bf.load('./137_36_shankD_116.dat')

    There are two ways to view the data: use time or points
    bf.plot(t=(1.2,2.5), chNo=slice(0,16))   # [1.2, 2.5)
    bf.plot(n=(0,2000),chNo=3)               # [#0, #2000)

    To output bytearray for writing to PCIE or other hardware
    buf = bf.tobytearray(n)                  # n is the #points per channel

    To numpy array, two ways:
    t, data = bf.tonumpyarray(n=(0,1000))
    or
    t, data = bf.tonumpyarray(t=(0,2))
    '''
    def __init__(self, nCh=16, fs=30000):
        self._nCh = nCh
        self.fs = float(fs)

    def load(self, file_name, dtype='int16', seekpos=0):
        '''
        bin.load('filename','int16')
        bin.load('filename','float32')
        '''
        file = open(file_name,'r')
        if dtype in ('int16','i2'):
            file.seek(seekpos*self._nCh*2)
        elif dtype in ('float32','int32','i4'):
            file.seek(seekpos*self._nCh*4)
        self.datastream = np.fromfile(file,dtype=dtype) 
        self._npts = len(self.datastream)/self._nCh #full #pts/ch
        self.info0 = '{0} loaded, it contains: \n'.format(file_name)
        self.info1 = '{0} * {1} points \n'.format(self._npts, self._nCh)
        self.info2 = '{0} channels with sampling rate of {1:.4f} \n'.format(self._nCh, self.fs)
        self.info3 = '{0:.3f} secs ({1:.3f} mins) of data'.format(self._npts/self.fs, self._npts/self.fs/60)
        print "#############  load data  ###################"
        print self.info0 + self.info1 + self.info2 + self.info3
        print "#############################################"

        self.data = self.datastream.reshape(-1,self._nCh)
        dt = 1/self.fs
        self.t = np.linspace(0,self._npts*dt,self._npts,endpoint='false')

    def __repr__(self):
        return self.info0 + self.info1 + self.info2 + self.info3

    def plot(self, n=(0,0), t=(0,0), chNo=0):
        if n==(0,0):
            n = (0,self._npts)
        if t==(0,0):
            _n = np.arange(self._npts)
            mask = np.logical_and(_n>=n[0],_n<n[1])
            plt.plot(self.t[mask],self.data[mask, chNo])   
            plt.show()
        else:
            mask = np.logical_and(self.t>=t[0], self.t<t[1])
            plt.plot(self.t[mask],self.data[mask, chNo])   
            plt.show()

    def tonumpyarray(self, n=(0,0), t=(0,0), chNo=-1):
        if chNo == -1:
            chNo = slice(self._nCh)
        if n==(0,0):
            n = (0,self._npts)
        if t==(0,0):
            n = slice(n[0],n[1])
            time = self.t[n],
            time = time[0]
            data = self.data[n, chNo]
        else:
            mask = np.logical_and(self.t>=t[0], self.t<t[1])
            time = self.t[mask]
            data = self.data[mask, chNo]
        return time, data

    def get_spk_pos(self):
        spk_peak_pos = np.asarray(np.where(self.data%2==1)).T
        return spk_peak_pos

    def tobytearray(self, n=0):
        if n==0:
            n = self._npts
        buf = self.datastream[:n*self._nCh].astype('int32')
        return bytearray(buf)  #pcie fifo is 32bits wide


if __name__ == '__main__':
    bf = Binload(nCh=16)
    bf.load('./137_36_shankD_116.dat')
    ##### test1 matplotlib plot #######
    # bf.plot(t=(1.2,2.5), chNo=slice(0,16))
    # bf.plot(n=(0,10000),chNo=3)

    ##### test2 to numpy array ########
    # time, data = bf.tonumpyarray(t=(0,1/bf.fs*1000))
    # time, data = bf.tonumpyarray(n=(0,1000), chNo=3)
    # print time.shape
    # print data.shape
    # plt.plot(time,data)
    # plt.show()


    #### test3 to byte array ###########
    buf = bf.tobytearray(n=1000)
    # send buf to pcie
    # ...
    # read buf from pcie
    data = np.frombuffer(buf, dtype='i4').reshape(-1,bf._nCh)
    plt.plot(data)
    plt.show()
    print data.shape
    

