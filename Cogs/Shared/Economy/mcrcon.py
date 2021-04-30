import socket
from struct import pack,unpack
from select import select

class mcrcon:
    def connect(self):
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.connect((self.config["ip"],self.config["port"]))
        self._send(3,self.config["password"])

    def __init__(self,config):
        self.config = config

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self,type,value,tb):
        self.disconnect()

    def disconnect(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def _read(self,length):
        data = b""
        while len(data) < length:
            data += self.socket.recv(length - len(data))
        return data

    def _send(self,out_type,out_data):
        out_payload = (pack("<ii",0,out_type)+out_data.encode("utf8")+b"\x00\x00")
        out_length = pack("<i",len(out_payload))
        self.socket.send(out_length+out_payload)
        in_data = ""
        while True:
            (in_length,) = unpack("<i",self._read(4))
            in_payload = self._read(in_length)
            in_id,in_type = unpack("<ii",in_payload[:8])
            in_data += in_payload[8:-2].decode("utf8")
            if len(select([self.socket],[],[],0)[0]) == 0:
                return in_data

    def run(self,command):
        return self._send(2,command)

def mcrsend(commands,cog,group,server):
    with mcrcon(cog.bot.main.config["enabled_addons"]["mmhm"]) as mcr:
        for command in commands:
            resp = mcr.run(command)
            if resp != "":
                cog.bot.main.log(cog,f"Command '{command}' for {group} unsuccessful:\n{resp}",server)
                return False
    cog.bot.main.log(cog,"Successfully ran commands for "+group,server)
    return True
