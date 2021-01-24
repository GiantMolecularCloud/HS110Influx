####################################################################################################
# log FritzBox to InfluxDB
####################################################################################################

"""
FritzBox to InfluxDB

author: Nico Krieger (GiantMolecularCloud)

This script uses environment variables for authentification and settings:
HS110_IP        IP address of the HS110
HS110_PORT      port to use for the connection, default: 9999
INFLUX_IP       IP address of the machine InfluxDB is running on, default: 127.0.0.1
INFLUX_PORT     port to connect to InfluxDB, default: 8086
INFLUX_USER     user to access the InfluxDB database, default: root
INFLUX_PASSWD   password to access the InfluxDB database, default: root
INFLUX_DB       Database to write the measurements to, default: HS110
SAMPLE_TIME     time to wait before getting the next sample, default: 60
"""


####################################################################################################
# imports
####################################################################################################

import os
import time
from influxdb import InfluxDBClient
import influxdb.exceptions as inexc


####################################################################################################
# settings
####################################################################################################

# read in environment variables, set some defaults if env vars are not defined

HS110_IP      = os.getenv('HS110_IP')
HS110_PORT    = int(os.getenv('HS110_PORT') or 9999)
INFLUX_IP     = os.getenv('INFLUX_IP') or '127.0.0.1'
INFLUX_PORT   = int(os.getenv('INFLUX_PORT') or 8086)
INFLUX_USER   = os.getenv('INFLUX_USER') or 'root'
INFLUX_PASSWD = os.getenv('INFLUX_PASSWD') or 'root'
INFLUX_DB     = os.getenv('INFLUX_DB') or 'HS110'
SAMPLE_TIME   = int(os.getenv('SAMPLE_TIME') or 60)


####################################################################################################
# helper functions
####################################################################################################

class HS110:

    def __init__(self, ip, port):
        self.ip   = ip
        self.port = port


    def encrypt(self,string):
        """
        Encrypt the TP-Link Smart Home Protocoll: XOR Autokey Cipher with starting key = 171
        This follows: https://github.com/softScheck/tplink-smartplug
        """
        from struct import pack
        key = 171
        result = pack('>I', len(string))
        for i in string:
            a = key ^ ord(i)
            key = a
            result += bytes([a])
        return result

    def decrypt(self):
        """
        Decrypt the TP-Link Smart Home Protocoll: XOR Autokey Cipher with starting key = 171
        This follows: https://github.com/softScheck/tplink-smartplug
        """
        key = 171
        self.decrypted = ""
        for i in self.encrypted[4:]:
            a = key ^ i
            key = i
            self.decrypted += chr(a)

    def get_raw(self):
        """
        connect to HS110, send payload and receive power data
        """
        import socket
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(int(10))
            sock_tcp.connect((self.ip, self.port))
            sock_tcp.settimeout(None)
            sock_tcp.send(self.encrypt('{"emeter":{"get_realtime":{}}}'))
            self.encrypted = sock_tcp.recv(2048)
            sock_tcp.close()
        except:
            raise ConnectionError("Could not connect to HS110 at IP "+str(self.ip)+" on port "+str(self.port))

    def decrypt_power(self):
        """
        decrypt power data and convert to Volts, Ampere, Watt, kWh
        """
        import json
        try:
            self.decrypt()
            decrypt_dict = json.loads(self.decrypted)
            self.data = {'voltage':      decrypt_dict['emeter']['get_realtime']['voltage_mv']/1000,    # V
                         'current':      decrypt_dict['emeter']['get_realtime']['current_ma']/1000,    # A
                         'power':        decrypt_dict['emeter']['get_realtime']['power_mw']/1000,      # W
                         'energy_total': decrypt_dict['emeter']['get_realtime']['total_wh']/1000,      # kWh
                         'error_code':   decrypt_dict['emeter']['get_realtime']['err_code']
                        }
        except:
            raise TypeError("Could not decrypt returned data.")


    def error_data(self):
        """
        In case of an error set all data to None and return error code 9999
        This error code is presumably not used by TP-Link, so I highjack this metric to let '9999' denote errors within HS110Influx.
        """
        self.data = {'voltage':      None,
                     'current':      None,
                     'power':        None,
                     'energy_total': None,
                     'error_code':   9999
                    }

    def poll(self):
        """
        Poll the HS110 and format the data to be sent to InfluxDB.
        """
        from datetime import datetime

        self.polltime = datetime.utcnow().isoformat()
        try:
            self.get_raw()
            self.decrypt_power()
        except ConnectionError:
            print(polltime, "  Error contacting HS110.")
            self.error_data
        except TypeError:
            print(polltime, "  Error decrypting data")
            self.error_data
        except Exception:
            print(polltime, "  Unknown error.")
            self.error_data

        return [{'measurement': 'power',
                 'tags': {'sensor': 'HS110'},
                 'time': self.polltime,
                 'fields': self.data
                }]


####################################################################################################
# Initialize
####################################################################################################

# Set up HS110
HS = HS110(HS110_IP, HS110_PORT)

# connect to InfluxDB
client = InfluxDBClient(host     = INFLUX_IP,
                        port     = INFLUX_PORT,
                        username = INFLUX_USER,
                        password = INFLUX_PASSWD
                       )

# create new database if necessary
if not INFLUX_DB in [db['name'] for db in client.get_list_database()]:
    client.create_database(INFLUX_DB)

# select current database
client.switch_database(INFLUX_DB)


####################################################################################################
# Send data to influxdb
####################################################################################################

def write_database(client, data):
    """
    Writes a given data record to the database and prints unexpected results.
    Copy/paste from my homeclimate code.
    """
    from datetime import datetime

    try:
        iresponse  = client.write_points(data)
        if not iresponse:
            print("Sending data to database failed. Response: ", iresponse)
    except inexc.InfluxDBServerError as e:
        print(datetime.utcnow().isoformat(), "  Sending data to database failed due to timeout.\n", e)
        pass
    except Exception as e:
        print(datetime.utcnow().isoformat(), "  Encountered unknown error.\n", e)
        pass


####################################################################################################
# Continuously take data
####################################################################################################

try:
    while True:

        try:
            write_database(client = client,
                           data   = HS.poll()
                          )
        except Exception as e:
            print(e)
        finally:
            time.sleep(SAMPLE_TIME)

except KeyboardInterrupt:
    print (datetime.now(), "  Program stopped by keyboard interrupt [CTRL_C] by user. ")


####################################################################################################
