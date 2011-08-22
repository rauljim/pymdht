import wx

import core.ptime as time
import sys, os
from optparse import OptionParser

import logging
import core.logging_conf as logging_conf

logs_level = logging.DEBUG # This generates HUGE (and useful) logs
#logs_level = logging.INFO # This generates some (useful) logs
#logs_level = logging.WARNING # This generates warning and error logs

import core.identifier as identifier
import core.pymdht as pymdht
import time
import interactive_dht_ext as idht_ext

import pymdht.core.message as message

import gui.mainclass as mainclass

import gui.graphical_display as gdisplay

import cPickle

class Interactive_GUI(wx.Frame):
    MainList=[]
    def __init__(self, parent, mytitle, list, Size):
        wx.Frame.__init__(self, parent, wx.ID_ANY, mytitle, pos=(0, 0), size=Size)
        self.dht=None
        self.init_main_of_idht()        
        self.counter1=0
        self.counter2=0
        self.packets=[]
        self.load_controls()
#        obj=GraphicalGUI.Graphical_GUI(None,"Graphical display_on_grid of DHT",None,(1440,900))
#        obj.Show()
#        self.Close(True)
#        obj=mainclass.MainClass()
#        q,r,e,qre=obj.open_file("/home/shariq/Desktop/Eclipse/Workspace/Phase-2/test.out")
#        self.querieslist=q
#        self.responseslist=r
#        self.errorslist=e
#        self.QueResErrList=qre
#        obj=lucgee.Lookupconverge_ext(None,"Lookup@KAD Converge Visualization",self.QueResErrList,(1440,900)).Show()
#        self.Close(True)
    def display_on_grid(self,t):
        pos = self.lc.InsertStringItem(self.counter1,str(self.counter1))
        self.lc.SetStringItem(pos, 1,str(t[0]))
        if(t[2]!="-"):
            self.lc.SetStringItem(pos, 2,"%d Peer(s) from Node" % t[1])
            self.lc.SetStringItem(pos, 3,str(t[2].addr))
        else:
            self.lc.SetStringItem(pos, 2,str(t[1]))
            self.lc.SetStringItem(pos, 3,str(t[2]))
        self.lc.SetStringItem(pos, 4,str(t[3]))
        if(self.lc.GetColumnWidth(4)<len(str(t[3]))*6.5):
            self.lc.SetColumnWidth(4, len(str(t[3]))*6.5)
        self.counter1=self.counter1+1
    def _on_peers_found(self, start_ts, peers,src_node):
        if peers:
            t=time.time() - start_ts, len(peers), src_node, peers
            wx.CallAfter(self.display_on_grid,t)
        else:
            t=time.time() - start_ts, "-","-","-"
            wx.CallAfter(self.display_on_grid,t)
            self.toolbar.EnableTool(1, True)
            self.packets=self.dht.stop_and_get_capture()
#    def LoadList(self,Packets):
#        obj=mainclass.MainClass()
#        q,r,e,qre=obj.open_file("/home/shariq/Desktop/Eclipse/Workspace/Phase-2/test.out")
#        self.querieslist=q
#        self.responseslist=r
#        self.errorslist=e
#        self.QueResErrList=qre
#        obj=lucgee.Lookupconverge_ext(None,"Lookup@KAD Converge Visualization",self.QueResErrList,(1440,900)).Show()
    def start_get_peers(self, dht, infohash, port):
        input = ['fast', infohash, port]
        dht.start_capture()
        dht.get_peers(time.time(), identifier.Id(input[1]),
                          self._on_peers_found, int(input[2]))
    def init_main_of_idht(self):
        parser = OptionParser()
        parser.add_option("-a", "--address", dest="ip",
                          metavar='IP', default='127.0.0.1',
                          help="IP address to be used")
        parser.add_option("-p", "--port", dest="port",
                          metavar='INT', default=7000,
                          help="port to be used")
        parser.add_option("-x", "--path", dest="path",
                          metavar='PATH', default='.',
                          help="state.dat and logs location")
        parser.add_option("-r", "--routing-plug-in", dest="routing_m_file",
                          metavar='FILE', default='plugins/routing_nice_rtt.py',
                          help="file containing the routing_manager code")
        parser.add_option("-l", "--lookup-plug-in", dest="lookup_m_file",
                          metavar='FILE', default='plugins/lookup_a4.py',
                          help="file containing the lookup_manager code")
        parser.add_option("-z", "--logs-level", dest="logs_level",
                          metavar='INT',
                          help="logging level")
        parser.add_option("-d", "--private-dht", dest="private_dht_name",
                          metavar='STRING', default=None,
                          help="private DHT name")
        parser.add_option("-e", "--experimental-plug-in",dest="experimental_m_file",
                          metavar='FILE',default='core/exp_plugin_template.py',
                          help="file containing ping-manager code")
        
        options, args= parser.parse_args()
        my_addr = (options.ip, int(options.port))
        logs_path = options.path
        print 'Using the following plug-ins:'
        print '*', options.routing_m_file
        print '*', options.lookup_m_file
        print '*', options.experimental_m_file
        print 'Private DHT name:', options.private_dht_name
        routing_m_name = '.'.join(os.path.split(options.routing_m_file))[:-3]
        routing_m_mod = __import__(routing_m_name, fromlist=[''])
        lookup_m_name = '.'.join(os.path.split(options.lookup_m_file))[:-3]
        lookup_m_mod = __import__(lookup_m_name, fromlist=[''])
        experimental_m_name = '.'.join(os.path.split(options.experimental_m_file))[:-3]
        experimental_m_mod = __import__(experimental_m_name, fromlist=[''])
        self.dht = pymdht.Pymdht(my_addr, logs_path,
                            routing_m_mod,
                            lookup_m_mod,
                            experimental_m_mod,
                            options.private_dht_name,
                            logs_level)
    def load_controls(self):


        sizer_v1 = wx.BoxSizer(wx.VERTICAL)

        sizer_v1_h1 = wx.BoxSizer(wx.HORIZONTAL)

        sizer_v1_h1.AddSpacer((10, 0))

        sizer_v1_h1_v1 = wx.BoxSizer(wx.VERTICAL)

        sizer_v1_h1_v1.AddSpacer((0, 10))

        sizer_v1_h1_v1_h1 = wx.BoxSizer(wx.HORIZONTAL)
        staticbox1 = wx.StaticText(self, label="Info Hash : ",size=wx.Size(100, -1))
        sizer_v1_h1_v1_h1.Add(staticbox1)
        self.textbox1 = wx.TextCtrl(self, size=wx.Size(400, -1))
        sizer_v1_h1_v1_h1.Add(self.textbox1, wx.EXPAND)        
        self.textbox1.SetValue("2aedb99b1e79e776433eecbec675c84704677124")
        sizer_v1_h1_v1.Add(sizer_v1_h1_v1_h1, 1, flag=wx.ALL | wx.EXPAND)

        sizer_v1_h1_v1_h2 = wx.BoxSizer(wx.HORIZONTAL)
        staticbox2 = wx.StaticText(self, label="Port : ",size=wx.Size(100, -1))
        sizer_v1_h1_v1_h2.Add(staticbox2)
        self.textbox2 = wx.TextCtrl(self, size=wx.Size(400, -1))
        sizer_v1_h1_v1_h2.Add(self.textbox2, wx.EXPAND)
        self.textbox2.SetValue("1234")
        sizer_v1_h1_v1.Add(sizer_v1_h1_v1_h2, 1, flag=wx.ALL | wx.EXPAND)

        sizer_v1_h1.Add(sizer_v1_h1_v1, 0, flag=wx.ALL | wx.EXPAND)

        sizer_v1_h1_v2 = wx.BoxSizer(wx.HORIZONTAL)
        self.toolbar = wx.ToolBar(self, style=wx.TB_HORIZONTAL | wx.TB_TEXT | wx.EXPAND)
        self.toolbar.AddLabelTool(1, "Run", wx.Bitmap('images/run.png'))
        self.Bind(wx.EVT_TOOL, self.run, id=1)
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(2, "Save", wx.Bitmap('images/exit.png'))
        self.Bind(wx.EVT_TOOL, self.save_infile, id=2)
        self.toolbar.AddLabelTool(3, "Graphical Display", wx.Bitmap('images/Graph.png'))
        self.toolbar.AddSeparator()
        self.Bind(wx.EVT_TOOL, self.on_graphical_display, id=3)
        self.toolbar.AddSeparator()
        self.toolbar.AddLabelTool(4, "Exit", wx.Bitmap('images/exit.png'))
        self.Bind(wx.EVT_TOOL, self.exit, id=4)
        self.toolbar.Realize()
        sizer_v1_h1_v2.Add(self.toolbar, wx.EXPAND)
        sizer_v1_h1.Add(sizer_v1_h1_v2, 0, flag=wx.ALL | wx.EXPAND)

        sizer_v1.Add(sizer_v1_h1, 0, flag=wx.ALL | wx.EXPAND)

        sizer_v1_h5 = wx.BoxSizer(wx.HORIZONTAL)
        self.checkbox1=wx.CheckBox (self, -1, 'Load Information from PirateBay' )
        self.checkbox1.Bind(wx.EVT_CHECKBOX, self.on_checkbox1)
        sizer_v1_h5.Add(self.checkbox1, 5, flag=wx.ALL, border=10)
        sizer_v1.Add(sizer_v1_h5, 0, flag=wx.ALL | wx.EXPAND)

        sizer_v1_h2 = wx.BoxSizer(wx.HORIZONTAL)
        self.lc = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_VRULES , size=(-1, 400))
        self.lc.InsertColumn(0, "No.")
        self.lc.SetColumnWidth(0, 40)
        self.lc.InsertColumn(1, "Query Time")
        self.lc.SetColumnWidth(1, 120)
        self.lc.InsertColumn(2, "X peers from Node")
        self.lc.SetColumnWidth(2, 180)
        self.lc.InsertColumn(3, "Queried Node")
        self.lc.SetColumnWidth(3, 173)
        self.lc.InsertColumn(4, "Peers")
        sizer_v1_h2.Add(self.lc, 5, flag=wx.ALL, border=10)
        sizer_v1.Add(sizer_v1_h2, 0, flag=wx.ALL | wx.EXPAND)
        
        sizer_v1_h4 = wx.BoxSizer(wx.HORIZONTAL)
        self.button1=wx.Button(self, 1, 'Load Information from PirateBay', (50, 130))
        self.Bind(wx.EVT_BUTTON, self.collect_values, id=1)
        sizer_v1_h4.Add(self.button1, 5, flag=wx.ALL, border=10)
        self.button2=wx.Button(self, 2, 'Stop!', (50, 130))
        self.Bind(wx.EVT_BUTTON, self.stop_collect_values, id=2)
        self.button2.Disable()
        sizer_v1_h4.Add(self.button2, 6, flag=wx.ALL, border=10)
        
        sizer_v1.Add(sizer_v1_h4, 0, flag=wx.ALL | wx.EXPAND)
        
        sizer_v1_h3 = wx.BoxSizer(wx.HORIZONTAL)
        self.lc2 = wx.ListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT | wx.SUNKEN_BORDER | wx.LC_VRULES , size=(-1, 250))
        self.lc2.InsertColumn(0, "No.")
        self.lc2.SetColumnWidth(0, 40)
        self.lc2.InsertColumn(1, "InfoHash")
        self.lc2.SetColumnWidth(1, 350)
        self.lc2.InsertColumn(2, "Description")
        self.lc2.SetColumnWidth(2, 700)
        sizer_v1_h3.Add(self.lc2, 5, flag=wx.ALL, border=10)
        sizer_v1.Add(sizer_v1_h3, 0, flag=wx.ALL | wx.EXPAND)

        self.SetSizer(sizer_v1)
        
    def run(self, event):
        self.counter1=0
        self.lc.DeleteAllItems()
        if self.checkbox1.IsChecked():
            ix_selected = self.lc2.GetNextItem(item=-1,
                                              geometry=wx.LIST_NEXT_ALL,
                                              state=wx.LIST_STATE_SELECTED)
            if(ix_selected!=-1):
                self.toolbar.EnableTool(1, False)
                self.textbox1.SetValue(self.lc2.GetItem(ix_selected, 1).GetText()) 
                self.start_get_peers(self.dht,str(self.textbox1.GetValue()), str(self.textbox2.GetValue()))
        else:
            self.toolbar.EnableTool(1, False)
            self.start_get_peers(self.dht,str(self.textbox1.GetValue()), str(self.textbox2.GetValue()))
    def save_infile(self,event):
        if not self.packets==[]:
            file_name=str(time.strftime("%Y%m%d%H%M%S"))
            file_path_name=os.path.join('data_files', file_name+'.out')
            f = open(file_path_name, "wb")
            cPickle.dump(self.packets, f)
            wx.MessageDialog(self, "The file "+file_name+" has been saved !!!", "File Saved!", wx.OK | wx.CENTRE | wx.ICON_EXCLAMATION).ShowModal()
         
    def exit(self,event):
        self.dht=None
        self.Destroy()
    def on_graphical_display(self,event):                  
#            obj=mainclass.MainClass()        
#            q,r,e,qre=obj.open_file(path)
#            self.querieslist=q
#            self.responseslist=r
#            self.errorslist=e
#            self.QueResErrList=qre
            obj=gdisplay.Graphical_display(None,"Graphical display of Interactive DHT",(1440,900)).Show()

    def display(self,information,lock):
        i=information[0]
        pos = self.lc2.InsertStringItem(self.counter2,str(self.counter2))
        self.lc2.SetStringItem(pos, 1,str(i[0]))
        self.lc2.SetStringItem(pos, 2,str(i[1]))
        self.counter2=self.counter2+1
        args=[information[1:len(information)],lock]
        wx.CallAfter(self.display_values,*args)
               
    def display_values(self,information,lock):
        if information==[]:
            return
        self.display(information,lock)        
    def collect_values(self,event):
        self.counter2=0
        self.lc2.DeleteAllItems()        
        self.button2.Enable()
        self.button1.Disable()
        self.idhtThread=idht_ext.idht_ext(self.display_values,[self.button1,self.button2])
        self.idhtThread.start()
        self.lc2.SetItemState(0, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED);
    def stop_collect_values(self,event):
        self.idhtThread.stop()
        self.button1.Enable()
        print "stopped"
    def on_checkbox1(self,event):
        if self.checkbox1.IsChecked():
            self.textbox1.Disable()
        else:
            self.textbox1.Enable()

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = Interactive_GUI(None, "Interactive DHT . . .", None,(1440,900))
    frame.Show(True)
    app.MainLoop()


