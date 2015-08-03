#coding:utf-8

import csv
import threading
import time

from gi.repository import GLib, Gtk, Gdk, GtkSource, GObject

from terminalwidget import *
from sshclient import Script



#decorators

def applyscript(text):

    def inner(row):
        riter = row.iter
        check,name,ip,port,login,password,progress = row
        GLib.idle_add(row.__setitem__,6,0)
        resp = "\r\n\n"
        resp += "#"*(len(name)+8)
        resp += "\r\n### " + name + " ###\r\n"
        resp += "#"*(len(name)+8)
        resp += "\r\n\n"

        runner = None
        if check:
            GLib.idle_add(row.__setitem__,6,1)
            runner = Script(ip,port,login,password)

            GLib.idle_add(row.__setitem__,6,2)
            try:
                runner.connect()
            except Exception as e:
                return  resp + e.message(), chan

            GLib.idle_add(row.__setitem__,6,5)
            try:
                runner.write(text)
            except Exception as e:
                return resp + e.message(), chan

            GLib.idle_add(row.__setitem__,6,10)
            try:
                chan = runner.execute()
            except Exception as e:
                return  resp + e.message(), chan
            return  resp, runner
    return inner

#end_decorators

# thread

def pulse(row):
    if row[6] > 90:
        row[6] = 15
    else:
        row[6] = row[6]+1

def proccess_exec(app):
    terminal = app.terminal
    source = app.builder.get_object("source")
    text = source.get_text(source.get_start_iter(), source.get_end_iter(), False)
    text = text + "\nquit"
    fu = applyscript(text)
    for row in app.store:
        if app.running:
            r = fu(row)
            resp,runner = r
            chan = runner.chan
            GLib.idle_add(terminal.feed, resp.encode('utf-8'))
            GLib.idle_add(row.__setitem__,6,11)

            while not chan.exit_status_ready():
                try:
                    GLib.idle_add(terminal.feed, chan.recv(120))
                    GLib.idle_add(pulse, row)
                except:
                    time.sleep(0.02)

            chan.close()
            GLib.idle_add(row.__setitem__,6,99)
            runner.close()
            GLib.idle_add(row.__setitem__,6,100)

    GLib.idle_add(app.ended_cb)

# end thread

# app
class App():
    running = False
    def __init__(self,*a,**kw):
        self.builder = builder = Gtk.Builder()
        builder.add_from_file("mssh.glade")
        builder.connect_signals(self)

        self.store = builder.get_object("tikstore")
        self.loadtiks()

        scrolledterminal = builder.get_object("scrolledterminal")
        if termtype == "vte":
            self.terminal = Vte.Terminal()
            scrolledterminal.add(self.terminal)
        else:
            self.terminal = TerminalBuffer()
            terminalsource = GtkSource.View.new_with_buffer(self.terminal)
            scrolledterminal.add(terminalsource)

        self.start_btn = builder.get_object("exec")
        self.stop_btn = builder.get_object("stop")
        try:
            builder.get_object("sourceview").set_monospace(True)
        except AttributeError:
            pass

        self.window = builder.get_object("mainwindow")
        self.window.set_name("mssh")

    def loadtiks(self):
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
            self.store.append([check,name,ip,port,login,password,0])

    def store_changed(self,model,*args):
        csvfile = open('tiks.csv','w', newline='')
        tabledata = csv.writer(csvfile, delimiter=';')
        for row in model:
            check,name,ip,port,login,password,progress = row
            tabledata.writerow([check,name,ip,port,login,password])
        csvfile.close()

    def exit_cb(self, *args):
        self.running = False
        Gtk.main_quit(*args)

    def file_set(self, widget):
        fn = widget.get_filename()
        source = self.builder.get_object("source")
        source.set_text(open(fn).read())
        self.builder.get_object("savescript").set_sensitive(True)

    def savescript_clicked_cb(self, widget):
        fn = widget.get_filename()
        source = self.builder.get_object("source")
        open(fn,'w').write(source.get_text(source.get_start_iter(), source.get_end_iter(), False))

    def clear_clicked_cb(self,*args):
        fo = self.builder.get_object("openscript")
        fo.set_filename("")
        self.builder.get_object("source").source.set_text("")
        self.builder.get_object("savescript").set_sensitive(True)

    def deltik_clicked(self,selection,*args):
        model,rows = selection.get_selected_rows()
        fordelete = []
        for row in rows:
            #selection.unselect_path(row)
            fordelete.append(Gtk.TreeRowReference.new(model,row))
        for row in fordelete:
            path = row.get_path()
            del model[path]

    def addtik_clicked(self,model):
        row = model.append([False,"Новый Mikrotik","192.168.88.1",22,"admin","",0])
        selection = self.builder.get_object("tikselection")
        m,rows = selection.get_selected_rows()
        for orow in rows:
            selection.unselect_path(orow)
        selection.select_iter(row)

    def check_clicked_cb(self,selection):
        model,rows = selection.get_selected_rows()
        for r in rows:
            model[r][0] = True

    def uncheck_clicked_cb(self,selection):
        model,rows = selection.get_selected_rows()
        for r in rows:
            model[r][0] = False

    def exec_clicked_cb(self,*args):
        if termtype == "io":
            self.terminal.bb = io.BytesIO()
        self.running = True
        self.start_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        threading.Thread(target=proccess_exec,args=(self,)).start()

    def ended_cb(self):
        self.stop_btn.set_sensitive(False)
        self.start_btn.set_sensitive(True)

    def stop_clicked_cb(self,*args):
        self.running = False

    def editor_cb(self,num):
        def edited(widget, path, text):
            self.store[path][num] = text
        return edited

    def onoff_toggled_cb(self, widget, path, *args):
        self.store[path][0] = not self.store[path][0]

    def name_edited_cb(self, widget, path, text):
        self.editor_cb(1)(widget, path, text)

    def ip_edited_cb(self, widget, path, text):
        self.editor_cb(2)(widget, path, text)

    def port_edited_cb(self, widget, path, text):
        try:
            port = int(text)
        except ValueError:
            return
        self.editor_cb(3)(widget, path, port)

    def login_edited_cb(self, widget, path, text):
        self.editor_cb(4)(widget, path, text)

    def password_edited_cb(self, widget, path, text):
        self.editor_cb(5)(widget, path, text)

if __name__ == "__main__":
    app = App()
    app.window.show_all()
    GObject.threads_init()
    Gtk.main()
        
