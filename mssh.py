#coding:utf-8

import csv
import threading
import time
import paramiko
import platform
import string

from gi.repository import GLib, Gtk, Gdk, GtkSource, GObject

try:
    from gi.repository import  Vte
    termtype="vte"
    #raise Exception('hy')
except:
    termtype="io"
    import io,re

    recolor = re.compile(b'\x1b.*?m|\x1b.*?B')
    #recolor = re.compile(b'\x1b.*?m')

    class TerminalBuffer(GtkSource.Buffer):
        def __init__(self,*a,**kw):
                self.bb = io.BytesIO()
                self.text = Gtk.TextBuffer()

                return super(TerminalBuffer, self).__init__(*a,**kw)

        def feed(self,data):
                st = self.bb.tell()
                self.bb.seek(0,2)
                self.bb.write(data)
                self.bb.seek(st)

                while True:
                    st = self.bb.tell()
                    line = self.bb.readline()
                    if line and line[-1]==10:
                        text = recolor.sub(b'',line)
                        self.feedline(text.decode('utf-8'))
                    else:
                        self.bb.seek(st)
                        break

        def feedline(self,text):
            #text = ''.join(filter(lambda x: x in string.printable, text))
            #text = ''.join([c for c in text if ord(c) > 31 or ord(c) == 9 or ord(c) == 10 or ord(c) < 0x84 ])
            print(text)
            self.insert(self.get_end_iter(),text)



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




def editor_cb(num):
    def edited(widget, path, text):
        store[path][num] = text
    return edited

def tiktreecolumns(tree):
    check = Gtk.CellRendererToggle()
    check.connect("toggled", Handler.tik_toggled)

    column1 = Gtk.TreeViewColumn("Вкл", check, active=0)

    name = Gtk.CellRendererText()
    name.set_property("editable", True)
    name.connect("edited", editor_cb(1))
    column4 = Gtk.TreeViewColumn("Микротик",name,text=1)

    column = Gtk.TreeViewColumn("Хост")

    ip = Gtk.CellRendererText()
    port = Gtk.CellRendererText()

    ip.set_property("editable", True)
    port.set_property("editable", True)

    ip.connect("edited", editor_cb(2))
    port.connect("edited", editor_cb(3))

    column.pack_start(ip, True)
    column.pack_start(port, True)

    column.add_attribute(ip, "text", 2)
    column.add_attribute(port, "text", 3)

    progress = Gtk.CellRendererProgress()
    column2 = Gtk.TreeViewColumn("Процесс",progress,value=6)
    column3 = Gtk.TreeViewColumn("Учётная запись")
    login = Gtk.CellRendererText()
    password = Gtk.CellRendererText()

    login.set_property("editable", True)
    password.set_property("editable", True)

    login.connect("edited", editor_cb(4))
    password.connect("edited", editor_cb(5))

    column3.pack_start(login, True)
    column3.pack_start(password, True)

    column3.add_attribute(login, "text", 4)
    column3.add_attribute(password, "text", 5)

    tree.append_column(column1)
    tree.append_column(column4)
    tree.append_column(column2)
    tree.append_column(column)
    tree.append_column(column3)

def loadtiks(model):
    #apply,name,ip,port,login,password
    try:
        csvfile = open('tiks.csv', newline='')
    except FileNotFoundError:
        return
    tabledata = csv.reader(csvfile, delimiter=';')
    for row in tabledata:
        check,name,ip,port,login,password = row
        check = bool(check)
        port = int(port)
        model.append([check,name,ip,port,login,password,0])

def applyscript(text):
    #print(text)
    def inner(row):
        riter = row.iter
        check,name,ip,port,login,password,progress = row
        print(name)
        #row[6] = 0
        GLib.idle_add(row.__setitem__,6,0)
        resp = "\r\n\n"
        resp += "#"*(len(name)+8)
        resp += "\r\n### " + name + " ###\r\n"
        resp += "#"*(len(name)+8)
        resp += "\r\n\n"


        runner = None
        if check:
            #row[6] = 1
            GLib.idle_add(row.__setitem__,6,1)
            runner = Script(ip,port,login,password)
            #row[6] = 2
            GLib.idle_add(row.__setitem__,6,2)
            try:
                runner.connect()
            except Ecxeption as e:
                return  e.message(), chan
            #row[6] = 5
            GLib.idle_add(row.__setitem__,6,5)
            try:
                runner.write(text)
            except Ecxeption as e:
                return e.message(), chan
            #row[6] = 10
            GLib.idle_add(row.__setitem__,6,10)
            try:
                chan = runner.execute()
            except Ecxeption as e:
                return  e.message(), chan
            return  resp, runner
    return inner


def proccess_exec():

    source = builder.get_object("source")
    text = source.get_text(source.get_start_iter(), source.get_end_iter(), False)
    text = text + "\nquit"
    fu = applyscript(text)
    for row in store:
        #print(type(row))
        #riter = row.iter
        r = fu(row)
        resp,runner = r
        chan = runner.chan
        GLib.idle_add(terminal.feed, resp.encode('utf-8'))
        GLib.idle_add(row.__setitem__,6,11)

        while not chan.exit_status_ready():
            try:
                GLib.idle_add(terminal.feed, chan.recv(120))

#                if row[6] > 90:
#                    row[6] = 15
#                else:
#                    row[6] = row[6]+1
            except:
                time.sleep(0.02)
            #"] > "

        chan.close()
        #row[6] = 99
        GLib.idle_add(row.__setitem__,6,99)
        runner.close()
        #row[6] = 100
        GLib.idle_add(row.__setitem__,6,100)


class Handler:
    def exec_clicked(self,*args):
        terminal.bb = io.BytesIO()
        threading.Thread(target=proccess_exec).start()


    def exit_clicked_cb(self, *args):
        Gtk.main_quit(*args)

    def file_set(self, widget):
        fn = widget.get_filename()
        source = builder.get_object("source")
        source.set_text(open(fn).read())

    def select_page(self,*args):
        pass

    def tik_toggled(self,path):
        store[path][0] = not store[path][0]

    def deltik_clicked(self,selection,*args):
        model,rows = selection.get_selected_rows()
        fordelete = []
        for row in rows:
            #selection.unselect_path(row)
            fordelete.append(Gtk.TreeRowReference(model,row))
        for row in fordelete:
            path = row.get_path()
            del model[path]

    def addtik_clicked(self,model):
        row = model.append([False,"Новый Mikrotik","192.168.88.1",22,"admin","",0])
        selection=builder.get_object("tikselection")
        m,rows = selection.get_selected_rows()
        for orow in rows:
            selection.unselect_path(orow)
        selection.select_iter(row)

    def store_changed(self,model,*args):
        csvfile = open('tiks.csv','w', newline='')
        tabledata = csv.writer(csvfile, delimiter=';')
        for row in model:
            check,name,ip,port,login,password,progress = row
            tabledata.writerow([check,name,ip,port,login,password])
        csvfile.close()

    def cursor(self,tree,*args):
        path,col = tree.get_cursor()
        print(path)



GObject.type_register(GtkSource.View)
builder = Gtk.Builder()
builder.add_from_file("mssh.glade")
builder.connect_signals(Handler())

store = builder.get_object("tikstore")
loadtiks(store)

tree = builder.get_object("tikview")
tiktreecolumns(tree)

scrolledterminal = builder.get_object("scrolledterminal")
if termtype == "vte":
    terminal = Vte.Terminal()
    scrolledterminal.add(terminal)
else:
    terminal = TerminalBuffer()
    terminalsource = GtkSource.View.new_with_buffer(terminal)
    scrolledterminal.add(terminalsource)


window = builder.get_object("mainwindow")
window.set_name("mssh")

window.show_all()
GObject.threads_init()
Gtk.main()
