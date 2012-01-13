'''
Created on 6 Apr 2011

@author: shariq
'''
import math

class Node:
    IPadress=""
    Port=""
    d=""
    dn=""
    x=""
    y=""
    size=0
    color1=""
    color2=""
    def __init__(self,pIP,pPt,pd,pdn,px,py,psize,pcolor1,pcolor2):
        self.IPadress=pIP
        self.Port=pPt
        self.d=pd
        self.dn=pdn
        self.x=px
        self.y=py
        self.size=psize
        self.color1=pcolor1
        self.color2=pcolor2

class ListofNodes:
    MainNode=""
    NodeList=[]
    def __init__(self):
        self.MainNode=""
        self.NodeList=[]
        self.PeerList=[]
        pass
    def SetMainNode(self,pIP,pPt,pd,pdn,px,py,psize,pcolor1,pcolor2):
        self.MainNode=Node(pIP,pPt,pd,pdn,px,py,psize,pcolor1,pcolor2)
    def AddNode(self,pIP,pPt,pd,pdn,px,py,psize,pcolor1,pcolor2):
        tempa=Node(pIP,pPt,pd,pdn,px,py,psize,pcolor1,pcolor2)        
        self.NodeList.append(tempa)
    def SetPeerList(self,pPeerList):
        self.PeerList=pPeerList
#    def DeletePeerNode(self,px,py):
#        for i in self.NodeList:
#            if(i.x==px and i.y==py):
#                self.NodeList.remove(i)
    def Find_Vertical_Number_of_Node(self,pd,ToStoreRecursiveValue):             
        if self.MainNode.d==pd:
            if(ToStoreRecursiveValue<int(self.MainNode.dn)):
                ToStoreRecursiveValue=int(self.MainNode.dn)
        for i in self.NodeList:
            if i.__class__.__name__!='ListofNodes':
                if(i.d==pd):
                    if(ToStoreRecursiveValue<int(i.dn)):
                        ToStoreRecursiveValue=int(i.dn)
            else:
                ToStoreRecursiveValueTemp=i.Find_Vertical_Number_of_Node(pd,ToStoreRecursiveValue)
                if(ToStoreRecursiveValueTemp>ToStoreRecursiveValue):
                    ToStoreRecursiveValue=ToStoreRecursiveValueTemp 
        return ToStoreRecursiveValue
    def Return_Node_of_IPandPort(self,pip,pp,tNode):
        if self.MainNode.IPadress==pip and self.MainNode.Port==pp:
            tNode=self.MainNode
        for i in self.NodeList:
            if i.__class__.__name__!='ListofNodes':
                if i.IPadress==pip and i.Port==pp:
                    tNode=i
            else:
                tNode=i.Return_Node_of_IPandPort(pip,pp,tNode)           
        return tNode
    def Return_Node_At_Position(self,px,py,node):
        if math.sqrt((self.MainNode.x - px) ** 2 + (self.MainNode.y - py) ** 2)<self.MainNode.size:
            if not node == None:
                if not self==node[0]:
                    return self,0
            else:
                if not self==node:
                    return self,0
        for i in self.NodeList:
            if i.__class__.__name__!='ListofNodes':
                if math.sqrt((i.x - px) ** 2 + (i.y - py) ** 2)<self.MainNode.size:
                    if not node == None:
                        if not i==node[0]:
                            return i,1
                    else:
                        if not i==node:
                            return i,1
            else:
                Temp = i.Return_Node_At_Position(px,py,node)
                if Temp!=False:
                    if Temp!=node:
                        return Temp
        return False  
    def Add_Special_Node(self,pNode1,pNode2):
        for i in self.NodeList:
            if i.__class__.__name__!='ListofNodes':
                if i.d==pNode2.d and i.IPadress==pNode2.IPadress and i.Port==pNode2.Port:
                    self.NodeList.remove(i)
                    self.NodeList.append(pNode1)
#                    return True
            else:
                if i.MainNode.d==pNode2.d and i.MainNode.IPadress==pNode2.IPadress and i.MainNode.Port==pNode2.Port:
                    self.NodeList.remove(i)
                    self.NodeList.append(pNode1)
#                    return True
                i.Add_Special_Node(pNode1,pNode2)                                   
        return False
    def Delete_Special_Nodes(self,pNode,pcolor1,pcolor2):
        for i in self.NodeList:
            if i.__class__.__name__!='ListofNodes':
                if i.d==pNode.d and i.IPadress==pNode.IPadress and i.Port==pNode.Port:
                    self.NodeList.remove(i)
                    pNode.color1=pcolor1
                    pNode.color2=pcolor2
                    pNode.NodeList=[]
                    self.NodeList.append(pNode)
#                    return True
            else:
                if i.MainNode.d==pNode.d and i.MainNode.IPadress==pNode.IPadress and i.MainNode.Port==pNode.Port:
                    self.NodeList.remove(i)
                    pNode.color1=pcolor1
                    pNode.color2=pcolor2
                    pNode.NodeList=[]
                    self.NodeList.append(pNode)
#                    return True
                i.Delete_Special_Nodes(pNode,pcolor1,pcolor2)
    def ClearNodes(self,pNode,pcolor1,pcolor2):
        if self.MainNode==pNode:
            self.NodeList=[]
            self.MainNode.color1=pcolor1
            self.MainNode.color2=pcolor2
        for i in self.NodeList:
            if i.__class__.__name__!='ListofNodes':
                pass
            else:
                if i==pNode:
                    i.NodeList=[]
                i.ClearNodes(pNode,pcolor1,pcolor2)
    def FindMaxY(self,pMY):
        if self.MainNode.y>pMY:
            pMY=self.MainNode.y
        for i in self.NodeList:
            if i.__class__.__name__!='ListofNodes':
                if i.y>pMY:
                    pMY=i.y
            else:
                TemppMY=i.FindMaxY(pMY)
                if TemppMY>pMY:
                    pMY=TemppMY
        return pMY
    def FindMaxX(self,pMX):
        if self.MainNode.x>pMX:
            pMX=self.MainNode.x
        for i in self.NodeList:
            if i.__class__.__name__!='ListofNodes':
                if i.x>pMX:
                    pMX=i.x
            else:
                TemppMY=i.FindMaxY(pMX)
                if TemppMY>pMX:
                    pMX=TemppMY
        return pMX
                
            