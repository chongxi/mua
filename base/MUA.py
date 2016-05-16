import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import mmap
import numexpr as ne
from sklearn.neighbors import NearestNeighbors

class RAW(object):
    def __init__(self, filename, nCh=32, fs=25000, numbytes=4):
        f = open(filename)
        self.fid = f
        self.filename = filename
        self.nCh = nCh
        self.fs  = fs*1.0
        self.numbytes = numbytes
        self.dtype = 'i'+str(self.numbytes)
        data = np.fromfile(self.filename, 
                           dtype=self.dtype).reshape(-1,self.nCh)
        self.spk_peak_pos = np.asarray(np.where(ne.evaluate("abs(data)%2==1"))).T
        self.data = data/float(2**14)
        self.data = self.data.astype('float32')
        self.npts = len(self.data)
        self.t    = np.linspace(0, self.npts/self.fs, self.npts)



class MUA(RAW):
    def __init__(self, filename, nCh=32, fs=25000, numbytes=4):
        super(MUA, self).__init__(filename, nCh, fs, numbytes)
        self.mm = mmap.mmap(self.fid.fileno(),0,access=mmap.ACCESS_READ)
        self.mm.seek(0)
    
    def seek(self, n):
        self.mm.seek(n)
    
    def get_data(self, npts):
        x = self.mm.read(npts*self.nCh*self.numbytes)
        return np.frombuffer(x, dtype='i'+str(self.numbytes)).reshape(-1,self.nCh)
    
    def get_near_ch(self, ch, span, chmax):
        start = ch-span if ch-span>=0 else 0
        end   = ch+span if ch+span<chmax else chmax
        return np.arange(start,end+1,1)
    
    def tospk(self, chspan=1):
        spkdict = {}
        # for ch in arange(self.nCh):
        for ch in range(self.nCh):
            spk = []
            for n,_ in self.spk_peak_pos[self.spk_peak_pos[:,1]==ch]:
                near_ch = self.get_near_ch(ch, chspan, self.nCh-1)
                spk.append(self.data[n-10:n+10, near_ch])
            spk = np.asarray(spk)
            spkdict[ch] = spk
        return SPK(spkdict)


class SPK():
    def __init__(self, spkdict):
        self.spk = spkdict
        self.spkNo = 1
        
    def __getitem__(self,i):
        return self.spk[i]
    
    def tofet(self,method):
        fet = {}
        if isinstance(method, int):
            for i in range(len(self.spk)):
                spk = self.spk[i]
                if spk.shape[0] > 0:
                    fet[i] = spk[:,method,:]
                else:
                    fet[i] = 0
        elif method == 'peak':
            for i in range(len(self.spk)):
                spk = self.spk[i]
                if spk.shape[0] > 0:
                    # TODO: 9:13?
                    fet[i] = spk[:,9:13,:].min(axis=1).squeeze()  
                else:
                    fet[i] = 0
            self.fet = fet
        elif method == 'pca':
            from sklearn.decomposition import PCA
            for i in range(len(self.spk)):
                pca = PCA(n_components=6)
                spk = self.spk[i]
                if spk.shape[0] > 0:
                    # TODO: 8:17?
                    X = np.concatenate((spk[:,8:17,:].transpose(2,1,0)),axis=0).T   #
                    temp_fet = pca.fit_transform(X)
                    fet[i] = temp_fet/(temp_fet.max()-temp_fet.min()) # scale down to (-1,1)
                else:
                    fet[i] = 0
            self.fet = fet
        else:
            print 'method = {peak, pca or some integer}'
        return fet


def get_rho(fet):
    nbrs = NearestNeighbors(algorithm='ball_tree', metric='euclidean',
                            n_neighbors=25).fit(fet)

    dismat = np.zeros(fet.shape[0])
    for i in range(fet.shape[0]):
        dis,_ = nbrs.kneighbors(fet[i].reshape(1,-1), return_distance=True)
        dismat[i] = dis.mean()

    rho = 1/dismat
    rho = (rho-rho.min())/(rho.max()-rho.min())
    return rho