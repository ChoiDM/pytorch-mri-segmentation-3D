import torch.nn as nn
import math
import torch.utils.model_zoo as model_zoo
import torch
import numpy as np
import sys
import torch.nn.init as init
affine_par = True

class HighResNetBlock(nn.Module):

    def __init__(self, inplanes, outplanes, padding_=1, stride=1, dilation_ = 1):
        super(HighResNetBlock, self).__init__()

        self.conv1 = nn.Conv3d(inplanes, outplanes, kernel_size=3, stride=1, 
                                padding=padding_, bias=False, dilation = dilation_)
        self.conv2 = nn.Conv3d(outplanes, outplanes, kernel_size=3, stride=1, 
                                padding=padding_, bias=False, dilation = dilation_)
        #2 convolutions of same dilation. residual block
        self.bn1 = nn.BatchNorm3d(outplanes, affine = affine_par)
        for i in self.bn1.parameters():
            i.requires_grad = False

        self.bn2 = nn.BatchNorm3d(outplanes, affine = affine_par)
        for i in self.bn2.parameters():
            i.requires_grad = False

        self.relu = nn.PReLU()
        self.diff_dims = (inplanes != outplanes)

        self.downsample = nn.Sequential(
            nn.Conv3d(inplanes, outplanes, kernel_size=1, stride=stride, bias=False),
            nn.BatchNorm3d(outplanes, affine = affine_par)
        )
        for i in self.downsample._modules['1'].parameters():
                i.requires_grad = False

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        
        if self.diff_dims:
            residual = self.downsample(residual)

        out += residual
        out = self.relu(out)

        return out

class SmallHighResNet(nn.Module):
    def __init__(self,NoLabels):
        super(SmallHighResNet,self).__init__()
        self.conv1 = nn.Conv3d(1, 8, kernel_size=3, stride=8, padding=1, bias=False)
        self.bn1 = nn.BatchNorm3d(8, affine = affine_par)
        for i in self.bn1.parameters():
            i.requires_grad = False
        self.relu = nn.PReLU()

        self.block1_1 = HighResNetBlock(inplanes=8, outplanes=8, padding_=1, dilation_=1)

        self.block2_1 = HighResNetBlock(inplanes=8, outplanes=16,padding_=2, dilation_=2)
        self.block2_2 = HighResNetBlock(inplanes=16, outplanes=16, padding_=2, dilation_=2)

        self.block3_1 = HighResNetBlock(inplanes=16, outplanes=16, padding_=4, dilation_=4)
        self.block3_2 = HighResNetBlock(inplanes=16, outplanes=16, padding_=4, dilation_=4)

        self.conv2 = nn.Conv3d(16, NoLabels, kernel_size=1, stride=1, padding=0, bias=False)

    def forward(self,x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        #print('A', out.size())
        #res blocks (dilation = 1)
        out = self.block1_1(out)
        #print('B', out.size())
        out = self.block1_1(out)
        #print('C', out.size())
        out = self.block1_1(out)
        #print('D', out.size())

        #res blocks (dilation = 2)
        out = self.block2_1(out)
        #print('E', out.size())
        out = self.block2_2(out)
        #print('F', out.size())
        out = self.block2_2(out)
        #print('G', out.size())

        #res blocks (dilation = 4)
        out = self.block3_1(out)
        #print('H', out.size())
        out = self.block3_2(out)
        #print('I', out.size())
        out = self.block3_2(out)
        #print('J', out.size())
        out = self.conv2(out)
        s0 = x.size()[2]
        s1 = x.size()[3]
        s2 = x.size()[4]
        self.interp = nn.Upsample(size = (s0, s1, s2), mode='trilinear')
        out = self.interp(out)
        #print('K', out.size())
        return out

def getSmallHRNet(NoLabels=3):
    model = SmallHighResNet(NoLabels)
    for m in model.modules():
        if isinstance(m,nn.Conv3d):
            init.kaiming_uniform(m.weight)
        elif isinstance(m, nn.Sequential):
            for m_1 in m.modules():
                if isinstance(m_1, nn.Conv3d):
                    init.kaiming_uniform(m_1.weight)
    return model

#or m in net.modules():
#m.weight.data.fill_(1)
#m.bias.data.fill_(0)