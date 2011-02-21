# Copyright (C) 2011 Raul Jimenez
# Released under GNU LGPL 2.1
# See LICENSE.txt for more information

import os.path

def openf(filename, mode='w'):
    return open(os.path.join('parser_results', filename), mode)
