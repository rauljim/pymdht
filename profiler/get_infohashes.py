#! /usr/bin/env python

from httplib import HTTPConnection

import os, sys, time

pages = [
    'all',
    # audio
    '100', '199',
    '101', '102', '103', '104',
    # video
    '200', '299',
    '201', '202', '203', '204', '205', '206', '207', '208',
    # apps
    '300', '399',
    '301', '302', '303', '304',
    # games
    '400', '499',
    '401', '402', '403', '404', '405', '406',
    # pr0n
    #'501', '502', '503', '504', '505', '506',
    # other
    '600', '699',
    '601', '602', '603', '604',
    ]

header = 'magnet:?xt=urn:btih:'
header_len = len(header)
infohashes = set()

def get_html(page):
    html_filename = os.path.join('torrent_pages', page+'.html')
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

def parse(html_file):
    for line in html_file:
        i = line.find(header)
        if i >= 0:
            begin = header_len + i
            end = begin + 40
            infohash = line[begin:end]
            infohashes.add(infohash)


if __name__ == '__main__':
    try:
        os.mkdir('torrent_pages')
    except (OSError):
        pass # directory already exists
    for page in pages:
        html_filename = get_html(page)
        parse(open(html_filename))

    infohashes_file = open('infohashes.dat', 'w')
    for infohash in infohashes:
        infohashes_file.write('%s\n' % infohash)
    print 'Infohashes saved in infohashes.dat'
