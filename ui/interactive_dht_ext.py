from httplib import HTTPConnection
import os, sys, time
import urllib
import threading
class idht_ext(threading.Thread):
    def __init__(self,call_b,buttons, data_path):
        self.data_path = data_path
        threading.Thread.__init__(self)
        print "Intialized"
        self.Counter=0
        self.running1=True
        self.running2=True
        self.call_b=call_b
        self.buttons=buttons
        self.daemon = True
        self._lock = threading.RLock()
        self.pages = [
            'all',
            # audio
#            '100', '199',
#            '101', '102', '103', '104',
            # video
#            '200', '299',
#            '201', '202', '203', '204', '205', '206', '207', '208',
            # apps
#            '300', '399',
#            '301', '302', '303', '304',
            # games
#            '400', '499',
#            '401', '402', '403', '404', '405', '406',
#            # pr0n
#            '501', '502', '503', '504', '505', '506',
            # other
#            '600', '699',
#            '601', '602', '603', '604',
            ]
        self.final_path = os.path.join(self.data_path, 'torrent_pages')
        try:
            os.mkdir(self.final_path)
        except (OSError):
            pass # directory already exists
    def get_html(self,page):
        html_filename = os.path.join(self.final_path, page+'.html')
        print 'Retrieving', page, 'to', html_filename, '...',
        sys.stdout.flush()
        
        html_file = open(html_filename, 'w')
        
        conn = HTTPConnection('thepiratebay.org')
    
        conn.request('GET', '/top/'+page)
        response = conn.getresponse()
        data = response.read()
        html_file.write(data)
        print 'DONE'
        time.sleep(1)
        html_file.close()
        return html_filename
    
    def parse(self,html_file,header):
        information=[]
        for line in html_file:
            i = line.find(header)
            if i >= 0:
                begin = len(header) + i
                end = begin + 40
                infohash = line[begin:end]
                i=line.find("&dn=")
                j=line.find("&tr=udp")
                begin = 4+i
                end = j
                torrent_name=line[begin:end]
                torrent_name=urllib.unquote_plus(torrent_name)
                a=infohash,torrent_name
                information.append(a)
        self.call_b(information,self._lock)

    def Run_Single(self):
        page=self.pages[self.Counter]
        html_filename = self.get_html(page)
        header = 'magnet:?xt=urn:btih:'
        self.parse(open(html_filename),header)
        self.Counter=self.Counter+1
        if self.running2==True:
            if self.Counter==len(self.pages):
                self.running1=False
            else:
                self.running1=True
        else:
            self.running1=False
    
    def run(self):
        while(self.running1):
            self.Run_Single()
        self.buttons[0].Enable()
        self.buttons[1].Disable()
    def stop(self):
        self.running2=False
        self.join()
        if self.isAlive():
            raise Exception, 'Thread is still alive!'
