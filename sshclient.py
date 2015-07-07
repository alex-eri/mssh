import paramiko

class Script():
    client = None
    def __init__(self,host,port,username,password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
        self.client = paramiko.client.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host,self.port,self.username,self.password,allow_agent=False,look_for_keys=False)

    def write(self,script):

        #transport = paramiko.Transport((host, port))
        #transport.connect(username = username, password = password)

        #transport = self.client.get_transport()
        #sftp = paramiko.SFTPClient.from_transport(transport)
        sftp = self.client.open_sftp()
        f = sftp.file("msshscript.rsc","w")
        f.write(script)
        f.close()
        sftp.close()

    def execute(self):
        transport = self.client.get_transport()
        self.chan = transport.open_session()
        self.chan.get_pty()
        self.chan.set_combine_stderr(True)
        self.chan.settimeout(0.5)
        #out = chan.makefile('w',80)
        self.chan.exec_command('/import msshscript.rsc')
        return self.chan

        #stdin, stdout, stderr = self.client.exec_command('/import msshscript.rsc')
        #return stdout


    def close(self):
        self.client.close()

