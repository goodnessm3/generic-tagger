from tkinter import *
from PIL import Image, ImageTk, UnidentifiedImageError
from io import BytesIO
import random


class IterWrapper:

    """Wraps an iterator to give it a memory, so we can step backwards using the previous() method."""

    def __init__(self, iterator, maxlen=25):

        self.it = iter(iterator)
        self.maxlen = maxlen
        self.history = []
        self.pos = -1  # the end of the history list

    def __iter__(self):

        return self

    def __next__(self):

        if self.pos < -1:
            self.pos += 1
            ne = self.history[self.pos]
        else:
            ne = next(self.it)
            self.history.append(ne)
            if len(self.history) > self.maxlen:
                self.history.pop(0)
        return ne

    def previous(self):

        if self.pos > -1 * self.maxlen:
            self.pos -= 1
        # maximum history of maxlen items, just return the last item again if trying to go back further
        if abs(self.pos) > len(self.history):
            self.pos = -1 * len(self.history)
        return self.history[self.pos]


class MainWindow(Frame):

    """Top level window"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._root().mw = self

        self.pw = PicWindow(self, width=400, height=420, relief=RIDGE)
        self.bw = BindingsWindow(self, borderwidth=5, relief=RIDGE)

        self.left_frame = Frame(self)
        self.button_frame = Frame(self.left_frame)
        self.code_window = CodeWindow(self.left_frame, bg="red")

        self.gen = None  # the iterator that will provide images and captions to the PicWindow

        self.control = Button(self.button_frame, text="Make function", command=self.code_window.prepare)
        self.run = Button(self.button_frame, text="Run iterator", command=self.start_iteration)
        self.stop = Button(self.button_frame, text="Stop iterator", command=self.stop_iteration)
        self.apply = Button(self.button_frame, text="Apply functions", command=self.apply)

        self.control.pack(side=LEFT)
        self.run.pack(side=LEFT)
        self.stop.pack(side=LEFT)
        self.apply.pack(side=LEFT)

        self.button_frame.pack(side=TOP)
        self.code_window.pack(side=TOP, fill=BOTH, expand=YES)
        self.left_frame.pack(side=LEFT)
        self.pw.pack(side=LEFT, fill=BOTH, expand=YES)
        self.pw.pack_propagate(0)  # need this otherwise size overshoots drastically, not sure why??
        self.bw.pack(side=LEFT, fill=BOTH, expand=YES)

    def start_iteration(self):

        """Start sending images and captions to the image window. """

        g = globals()["gen"]()
        self.gen = IterWrapper(g)  # wrap user-made generator to give it a memory/cache
        # the CodeWindow must define a generator called gen that yields tuples of (image, caption)
        self.advance_iterator(None)

    def stop_iteration(self):

        self.gen = None

    def advance_iterator(self, e):

        self.pw.update_image(*next(self.gen))

    def previous(self):

        self.pw.update_image(*self.gen.previous())

    def apply(self):

        self._root().apply()


class PicWindow(Frame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.lab = Label(self)
        self.caption = Label(self)
        self.current_caption = None  # need to store it here, easier than getting it from the widget
        self.history = []

        self.lab.pack(side=TOP)
        self.caption.pack(side=TOP)

    def update_image(self, imgbytes, capt):

        """Expects a tuple of (PIL image, caption)"""

        q = Image.open(imgbytes).resize((300, 300))
        im = ImageTk.PhotoImage(q)
        self.history.append(im)  # need to hold a reference to the images or they'll be garbage collected
        self.lab.configure(image=im)
        self.caption.configure(text=capt)
        self.current_caption = capt

        if len(self.history) > 25:
            self.history.pop(0)  # don't store images forever


class CodeWindow(Frame):

    """Contains the text box with the code for the image/caption supplier"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.tbox = Text(self)
        self.tbox.pack(side=TOP)

    def prepare(self):

        """evaluates the code in the entry box.
        this will be an iterator or a function to run on the result of the iterator.
        It is added to the global root function dictionary."""

        content = self.tbox.get(0.0, END)  # index needs to be a float!?
        print(content)
        try:
            exec(content, globals())
        except SyntaxError as e:
            print(e)
            return

        for x in globals():
            if callable(globals().get(x)) and not x in self._root().ignore:
                self._root().fxn_set.add(x)  # we are adding the name of the function, not the function itself
                print(f"Added {x} to the function list.")

        self._root().update_menus()


class BindingsWindow(Frame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.labels = iter(range(1, 100))
        self.button = Button(self, text="Add binding", command=self.add_button)
        self.button.pack(side=TOP)
        self.back_frame = Frame(self)
        self.back_button = Button(self.back_frame, text="<", command=self.back)

        self.back_button.pack(side=LEFT)
        self.back_frame.pack(side=TOP)

    def add_button(self):

        new = BindingRow(self, title=str(next(self.labels)))
        new.pack(side=TOP, fill="x")

    def back(self):

        self._root().event_generate("<<back>>")


class BindingRow(Frame):

    def __init__(self, *args, **kwargs):

        title = kwargs.pop("title")
        super().__init__(*args, **kwargs)
        self.v = StringVar(self)  # stores the name of the function to be called
        self.keylabel = Button(self, text=title, command=self.run_command, width=5)
        self.functionlabel = OptionMenu(self, self.v, *self._root().fxn_set)
        self.argslist = Entry(self)  # list of args with which to call the function (string only)

        self.keylabel.pack(side=LEFT)
        self.functionlabel.pack(side=LEFT)
        self.argslist.pack(side=LEFT, fill="x", expand=YES)

        self._root().fxn_menus.append(self)  # register self with root to recieve menu updates
        #self._root().update_menus()

    def run_command(self):

        args = [q.strip(" ") for q in self.argslist.get().split(",")]
        if args == [""]:
            args = []  # actually no args
        fx = self.v.get()
        self._root().append_action(fx, args)
        self._root().event_generate("<<advance>>")


class MyRoot(Tk):

    """To contain data that needs to be accessible by everyone"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fxn_set = {" "}  # set of the names of all the functions made in the interactive text entry
        self.ignore = set()
        self.fxn_menus = []  # a list of BindingRows to force them to update their lists when new functions are made
        self.mw = None  # a reference to the main window for propagating events
        self.mapping = []  # the functions and args to be run once the tagging is complete
        self.mapfile = open("session.txt", "w")  # write out history to a file in case something goes wrong

        # first we note everything that is callable in the global namespace. Then later, when user-defined functions
        # are introduced, we will get globals(), and compare against this list. Anything not in this list is a
        # newly-appeared callable in the global namespace and is a user-defined function so we will use it
        # to populate the drop-down menu of function choice

        for x in globals():
            if callable(globals().get(x)):
                self.ignore.add(x)

    def setup_bindings(self):

        self.bind("<<advance>>", self.mw.advance_iterator)
        self.bind("<<back>>", self.back)

    def update_menus(self):

        """Force an update of the dropdowns with all available functions. We have to destroy and re-make the menus
        because the commented-out code below behaves a weird way where only the last menu in the sequence will
        be updated regardless of which menu we are selecting the option from. Can't work out why."""
        '''
        for x in self.fxn_menus:
            x.functionlabel["menu"].delete(0, END)
            for fx in self.fxn_set:
                print(id(x))
                print(id(x.v))
                x.functionlabel["menu"].add_command(label=fx, command=lambda fx=fx: x.v.set(fx))
                #x.functionlabel["menu"].add_command(label=fx, command= lambda:print(fx))
                x.v.set(str(random.randint(0,1000)))
        '''

        num = len(self.fxn_menus)
        for x in self.fxn_menus:
            x.destroy()
        self.fxn_menus = []
        for x in range(num):
            self.mw.bw.add_button()

    def append_action(self, fx, args):

        """Record a function and args to be applied to a picture caption"""

        cap = self.mw.pw.current_caption
        action = (fx, cap, *args)
        self.mapping.append(action)
        self.mapfile.write(f"{fx}|||{cap}|||{args}\n")

    def back(self, e):

        self.mapfile.write("<<UNDO>>\n")  # easier than trying to step back through the file
        self.mw.previous()

    def apply(self):

        """The function that goes through self.mapping and actually carries out all the functions"""

        for x in self.mw.gen.history:
            x[0].close()  # close all open file handles so the files can be moved

        print("Applying functions...")
        for x in self.mapping:
            try:
                func = globals()[x[0]]
                func(*x[1:])
            except Exception as e:
                print(e)
        print("done")
        self.mapping = []  # clear list if the user wants to carry on



root = MyRoot()
myapp = MainWindow(root)
root.setup_bindings()  # make bindings now that the root object knows about all its children
myapp.pack()
root.mainloop()