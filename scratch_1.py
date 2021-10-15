import tkinter as tk
from tkinter.filedialog import askopenfilenames, asksaveasfilename
from PIL import Image, ImageTk
import glob
import cv2

class MousePositionTracker(tk.Frame):
    """ Tkinter Canvas mouse position widget. """

    def __init__(self, canvas):
        self.canvas = canvas
        self.canv_width = self.canvas.cget('width')
        self.canv_height = self.canvas.cget('height')
        self.reset()

        # Create canvas cross-hair lines.
        xhair_opts = dict(dash=(3, 2), width=2, fill='green')
        self.lines = (self.canvas.create_line(0, 0, 0, self.canv_height, **xhair_opts),
                      self.canvas.create_line(0, 0, self.canv_width, 0, **xhair_opts))

    def cur_selection(self):
        return (self.start, self.end)

    def begin(self, event):
        self.start = (event.x, event.y)  # Remember position (no drawing).
        self.canvas.coords(self.lines[0], event.x, 0, event.x, self.canv_height)
        self.canvas.coords(self.lines[1], 0, event.y, self.canv_width, event.y)

    def update(self, event):
        self.end = (event.x, event.y)
        self.canvas.coords(self.lines[0], event.x, 0, event.x, self.canv_height)
        self.canvas.coords(self.lines[1], 0, event.y, self.canv_width, event.y)
        self._command(self.start, (event.x, event.y))  # User callback.

    def reset(self):
        self.start = self.end = None

    def autodraw(self, command=lambda *args: None):
        """Setup automatic drawing; supports command option"""
        self.reset()
        self._command = command
        self.canvas.bind("<Motion>", self.begin)
        self.canvas.bind("<B1-Motion>", self.update)
        self.canvas.bind("<ButtonRelease-1>", self.quit)

    def quit(self, event):
        self.reset()


class SelectionObject(tk.Frame):
    """ Widget to display a rectangular area on given canvas defined by two points
        representing its diagonal.
    """

    def __init__(self, canvas, select_opts):
        # Create attributes needed to display selection.
        self.canvas = canvas
        self.select_opts1 = select_opts
        self.width = self.canvas.cget('width')
        self.height = self.canvas.cget('height')

        # Options for areas outside rectangular selection.
        select_opts1 = self.select_opts1.copy()  # Avoid modifying passed argument.
        select_opts1.update(state=tk.NORMAL)  # Hide initially.
        # Separate options for area inside rectangular selection.
        select_opts2 = dict(dash=(2, 2), fill='', width=2, outline='green', state=tk.NORMAL)

        # Initial extrema of inner and outer rectangles.
        imin_x, imin_y, imax_x, imax_y = 0, 0, 1, 1
        omin_x, omin_y, omax_x, omax_y = 0, 0, self.width, self.height

        self.rects = (
            # Area *outside* selection (inner) rectangle.
            self.canvas.create_rectangle(omin_x, omin_y, omax_x, imin_y, **select_opts1),
            self.canvas.create_rectangle(omin_x, imin_y, imin_x, imax_y, **select_opts1),
            self.canvas.create_rectangle(imax_x, imin_y, omax_x, imax_y, **select_opts1),
            self.canvas.create_rectangle(omin_x, imax_y, omax_x, omax_y, **select_opts1),
            # Inner rectangle.
            self.canvas.create_rectangle(imin_x, imin_y, imax_x, imax_y, **select_opts2)
        )

    def update(self, start, end):
        # Current extrema of inner and outer rectangles.
        imin_x, imin_y, imax_x, imax_y = self._get_coords(start, end)
        omin_x, omin_y, omax_x, omax_y = 0, 0, self.width, self.height

        # Update coords of all rectangles based on these extrema.
        self.canvas.coords(self.rects[0], omin_x, omin_y, omax_x, imin_y),
        self.canvas.coords(self.rects[1], omin_x, imin_y, imin_x, imax_y),
        self.canvas.coords(self.rects[2], imax_x, imin_y, omax_x, imax_y),
        self.canvas.coords(self.rects[3], omin_x, imax_y, omax_x, omax_y),
        self.canvas.coords(self.rects[4], imin_x, imin_y, imax_x, imax_y),

        for rect in self.rects:  # Make sure all are now visible.
            self.canvas.itemconfigure(rect, state=tk.NORMAL)

    def _get_coords(self, start, end):
        """ Determine coords of a polygon defined by the start and
            end points one of the diagonals of a rectangular area.
        """
        return (min((start[0], end[0])), min((start[1], end[1])),
                max((start[0], end[0])), max((start[1], end[1])))


class Widgets(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.frame = tk.Frame(height=1000, width=400)

        btn_open = tk.Button(master=self.frame, text="Open", width=6, height=2, command=self.open_file)
        btn_save = tk.Button(master=self.frame, text="Save As...", width=6, height=2, command=self.save_file)
        btn_next = tk.Button(master=self.frame, text="Next", width=6, height=2, command=self.next_img)
        btn_prev = tk.Button(master=self.frame, text="Previous", width=6, height=2, command=self.prev_img)

        btn_open.pack()
        btn_save.pack()
        btn_next.pack()
        btn_prev.pack()

        self.frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

    def open_file(self):
        filepath = askopenfilenames(
            filetypes=[("image", "*.jpg")]
        )
        if not filepath:
            return
        self.images = [cv2.imread(file) for file in glob.glob('filepath/*.jpg')]
        self.index = 0
        Application.canvas.create_image(0, 0, image=self.images[self.index], anchor=tk.NW)

    def save_file(self):
        filepath = asksaveasfilename(
            defaultextension="txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        with open(filepath, "w") as output_file:
            text = SelectionObject._get_coords()
            output_file.write(text)

    def next_img(self):
        Application.canvas.delete("all")
        self.index += 1
        Application.canvas.create_image(0, 0, image=self.images[self.index], anchor=tk.NW)

    def prev_img(self):
        Application.canvas.delete("all")
        self.index -= 1
        Application.canvas.create_image(0, 0, image=self.images[self.index], anchor=tk.NW)

class Application(tk.Frame):
    # Default selection object options.
    SELECT_OPTS = dict(dash=(2, 2), stipple='gray25', fill='',
                       outline='')

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # MAKE BUTTON TO SELECT PATH
        #path = r"C:\Users\Bach Nguyen\PycharmProjects\CarDetectionModelTesting\yolov4-custom-functions\detections\crop\dog\truck_1.png"
        #img = ImageTk.PhotoImage(Image.open(path))
        self.canvas = tk.Canvas(root, height=1000, width=1600, bg='grey')
        self.canvas.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        #images = Widgets.open_file(self)
        #self.canvas.create_image(0, 0, image=images, anchor=tk.NW)
        #self.canvas.img = img  # Keep reference.

        # Create selection object to show current selection boundaries.
        self.selection_obj = SelectionObject(self.canvas, self.SELECT_OPTS)

        # Callback function to update it given two points of its diagonal.
        def on_drag(start, end, **kwarg):  # Must accept these arguments.
            self.selection_obj.update(start, end)

        # Create mouse position tracker that uses the function.
        self.posn_tracker = MousePositionTracker(self.canvas)
        self.posn_tracker.autodraw(command=on_drag)  # Enable callbacks.


if __name__ == '__main__':
    WIDTH, HEIGHT = 2000, 1000
    BACKGROUND = 'grey'
    TITLE = 'Object classifier'

    root = tk.Tk()
    root.title(TITLE)
    root.geometry('%sx%s' % (WIDTH, HEIGHT))
    root.configure(background=BACKGROUND)

    root.bind()

    widg = Widgets(root)
    widg.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    app = Application(root)
    app.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

    root.mainloop()
