import gui.toplevel
import gui.startup
from gui.startup import in_gdb_thread, in_gtk_thread
import itertools
import igraph
import gdb
from gi.repository import Gtk, Gdk
import cairo
import threading

class Vec:
    def __init__(self, vec):
        self.vec = vec

    def __len__(self):
        t = gdb.lookup_type('vec_prefix').pointer()
        return int(self.vec.cast(t)['m_num'])

    def item(self, i):
        return self.vec['m_vecdata'][i]

    def __iter__(self):
        return itertools.imap(self.item, xrange (len (self)))

class VBreak(gdb.Breakpoint):
    def __init__(self, where, cb):
        gdb.Breakpoint.__init__(self, where, gdb.BP_BREAKPOINT,
                                internal = True)
        self.cb = cb

    def stop(self):
        self.cb()
        return False

class Visualizer(gui.toplevel.Toplevel):
    @in_gdb_thread
    def __init__(self):
        super(Visualizer, self).__init__()

        self.lock = threading.Lock()

        self.g = igraph.Graph(directed = True)
        self.entry_block = None
        self.exit_block = None
        self.blocks = {}
        self.bp1 = VBreak('execute_on_growing_pred', self.on_make_edge)
        self.bp2 = VBreak('execute_on_shrinking_pred', self.on_remove_edge)
        self.bp3 = VBreak('expunge_block', self.expunge)
        self.bp4 = VBreak('merge_blocks', self.merge_blocks)

        gui.startup.send_to_gtk(self.gtk_initialize)

    @in_gtk_thread
    def gtk_initialize(self):
        self.window = Gtk.Window()
        self.window.set_size_request(700, 800)

        self.surface = Gtk.DrawingArea()
        self.surface.connect("draw", self.draw_graph)

        self.window.add(self.surface)
        self.window.set_title('GCC CFG')
        self.window.show_all()

    @in_gtk_thread
    def draw_graph(self, widget, context):
        with self.lock:
            rect = widget.get_allocation()
 
            surface = cairo.ImageSurface (cairo.FORMAT_ARGB32,
                                          rect.width,
                                          rect.height)
 
            if self.g.vcount() > 0:
                layout = self.g.layout('sugiyama') #.mirror(1)
                plot = igraph.drawing.Plot(surface,
                                           (20, 20,
                                            rect.width - 20, rect.height - 20))
                plot.add(self.g, layout = layout)
                plot.redraw()

            context.set_source_surface (surface)
            context.paint()

    @in_gdb_thread
    def force_refresh(self):
        gdb.post_event(self.surface.queue_draw)

    @in_gdb_thread
    def ensure_vertex(self, block):
        if self.entry_block is None:
            cfg = gdb.lookup_symbol('cfun')[0].value()['cfg']
            self.entry_block = cfg['x_entry_block_ptr']
            self.exit_block = cfg['x_exit_block_ptr']

        if long(block) not in self.blocks:
            if block == self.entry_block:
                name = 'ENTRY'
            elif block == self.exit_block:
                name = 'EXIT'
            else:
                name = ('block #%d' % int(block['index']))
            n = self.g.vcount()
            self.log ('add vertex %d -> %s' % (n, name))
            self.g.add_vertices(1)
            self.blocks[long(block)] = name
            self.g.vs[n]['name'] = name
            self.g.vs[n]['label'] = name

        return self.blocks[long(block)]

    @in_gdb_thread
    def log(self, arg):
        # print arg
        pass

    @in_gdb_thread
    def on_make_edge(self):
        with self.lock:
            frame = gdb.newest_frame()
            edge = frame.read_var('e')
            srcv = self.ensure_vertex(edge['src'])
            destv = self.ensure_vertex(edge['dest'])
            self.log ('add (%s,%s)' % (str(srcv), str(destv)))
            self.g.add_edges([(srcv, destv)])
            self.force_refresh()

    @in_gdb_thread
    def on_remove_edge(self):
        with self.lock:
            frame = gdb.newest_frame()
            edge = frame.read_var('e')
            srcv = self.ensure_vertex(edge['src'])
            destv = self.ensure_vertex(edge['dest'])
            try:
                self.log ('remove (%s,%s)' % (str(srcv), str(destv)))
                self.g.delete_edges([(srcv, destv)])
                self.force_refresh()
            except ValueError:
                pass

    @in_gdb_thread
    def merge_blocks(self):
        with self.lock:
            frame = gdb.newest_frame()
            keep = frame.read_var('a')
            zap = frame.read_var('b')

            keepv = self.ensure_vertex(keep)

            # We only have to copy over successor edges; other breakpoints
            # will take care of the rest.
            for succ in Vec(zap['succs']):
                newv = self.ensure_vertex(succ['dest'])
                self.log ('add (%s,%s)' % (str(keepv), str(newv)))
                self.g.add_edges([(keepv, newv)])
            self.force_refresh()

    @in_gdb_thread
    def expunge(self):
        with self.lock:
            frame = gdb.newest_frame()
            vert = long(frame.read_var('b'))
            if vert in self.blocks:
                v = self.blocks[vert]
                del self.blocks[vert]
                try:
                    self.log ('expunge node %s' % str(v))
                    self.g.delete_vertices([v])
                    self.force_refresh()
                except:
                    pass

    def doplot(self):
        layout = self.g.layout('kk').mirror(1)
        igraph.plot(self.g, layout = layout)
