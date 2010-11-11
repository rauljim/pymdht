import GeoIP
import math
import os, sys

# IP address and coordinates of my laptop at Forum
my_ip = '192.16.125.198'
my_country = "Sweden"
my_lat = 59.4500007629
my_lon = 17.9167003632

# longitude/latitude constants
nauticalMilePerLat = 60.00721
nauticalMilePerLongitude = 60.10793
rad = math.pi / 180.0
milesPerNauticalMile = 1.15078
kmPerNauticalMile = 1.852

geo_city_file = "/usr/share/GeoIP/GeoIPCity.dat"
#can the DB be distributed to other peers?

class Geo:

    def __init__(self):
        self.gi = GeoIP.open(geo_city_file, GeoIP.GEOIP_STANDARD)

    def get_city(self, ip):
        try:
            gir = self.gi.record_by_addr(ip)
        except AttributeError:
            return None

        if gir:
            return gir['city']
        else:
            return None

    def get_country(self, ip):
        try:
            gir = self.gi.record_by_addr(ip)
        except AttributError:
            return None

        if gir:
            return gir['country_name']
        else:
            return None

    def get_coordinates(self, ip):
        try:
            gir = self.gi.record_by_addr(ip)
        except AttributError:
            return None, None

        if gir:
            return gir['latitude'], gir['longitude']
        else:
            return None, None

    def is_in_same_country(self, ip):
        return (self.get_country(ip) == my_country)

        
    def calc_distance(self, lat1, lon1, lat2=my_lat, lon2=my_lon):
        yDistance = (lat2 - lat1) * nauticalMilePerLat
        xDistance = (math.cos(lat1 * rad) + math.cos(lat2 * rad)) * \
                    (lon2 - lon1) * (nauticalMilePerLongitude / 2)
        
        distance = math.sqrt(yDistance ** 2 + xDistance ** 2)
        return int(round(distance * kmPerNauticalMile))

    def score_peer(self, ip):
        peer_addr = ip
        peer_lat, peer_lon = self.get_coordinates(peer_addr)
        peer_distance = self.calc_distance(peer_lat, peer_lon)
        if (self.is_in_same_country(peer_addr)):
            extra_km = 1
        else:
            extra_km = 500
            
        total_score = peer_distance + extra_km
        return total_score

def main():
    
    #  Testing peer (in Amsterdam)
    peer_addr = '213.197.62.197'
    lat1 = 52.3499984741
    lon1 = 4.91669988632

    peer_score = Geo().score_peer(peer_addr)
    print "Peer Score:", peer_score
    
       
if __name__ == '__main__':
    main()
