#coding:utf-8
from gi.repository import Gtk, GtkSource, GObject

try:
    from gi.repository import  Vte
    termtype="vte"

except:
    termtype="io"
    import io,re
    recolor = re.compile(b'\x1b.*?m|\x1b.*?B')

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
            self.insert(self.get_end_iter(),text)

GObject.type_register(GtkSource.View)
