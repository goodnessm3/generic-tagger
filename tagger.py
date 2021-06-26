from tkinter import *
from PIL import Image, ImageTk, UnidentifiedImageError
from io import BytesIO


class MainWindow(Frame):

    """Top level window"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._root().mw = self

        self.code_window = CodeWindow()
        self.pw = PicWindow()
        self.bw = BindingsWindow()

        self.gen = None  # the iterator that will provide images and captions to the PicWindow



        self.run = Button(text="Run iterator", command=self.start_iteration)
        self.stop = Button(text="Stop iterator", command=self.stop_iteration)
        self.apply = Button(text="Apply functions", command=self.apply)

        self.run.pack(side=TOP)
        self.stop.pack(side=TOP)
        self.apply.pack(side=TOP)

        self.code_window.pack(side=LEFT)
        self.pw.pack(side=LEFT)
        self.bw.pack(side=LEFT)

    def start_iteration(self):

        """Start sending images and captions to the image window. """

        self.gen = globals()["gen"]()
        # the CodeWindow must define a generator called gen that yields tuples of (image, caption)
        self.advance_iterator(None)

    def stop_iteration(self):

        self.gen = None

    def advance_iterator(self, e):

        self.pw.update_image(*next(self.gen))

    def apply(self):

        self._root().apply()


class PicWindow(Frame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.lab = Label(self)
        self.caption = Label(self)

        self.history = []  # all the pictures that have been shown so we can step backwards if needed

        self.lab.pack(side=TOP)
        self.caption.pack(side=TOP)

    def update_image(self, imgbytes, capt):

        """Expects a tuple of (PIL image, caption)"""

        q = Image.open(imgbytes).resize((300,300))
        im = ImageTk.PhotoImage(q)
        self.history.append(im)
        self.lab.configure(image=im, bg="green")
        self.caption.configure(text=capt)
        self.current_caption = capt


class CodeWindow(Frame):

    """Contains the text box with the code for the image/caption supplier"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.tbox = Text(self)
        self.control = Button(text="Make function", command=self.prepare)


        self.control.pack(side=TOP)
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
        self.button = Button(text="+", command=self.add_button)
        self.button.pack(side=TOP)

    def add_button(self):

        new = BindingRow()
        new.pack(side=TOP)


class BindingRow(Frame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.v = StringVar(self)  # stores the name of the function to be called
        self.keylabel = Button(self, command=self.run_command)
        self.functionlabel = OptionMenu(self, self.v, ())
        self.argslist = Entry(self)  # list of args with which to call the function (string only)

        self.keylabel.pack(side=LEFT)
        self.functionlabel.pack(side=LEFT)
        self.argslist.pack(side=LEFT)

        self._root().fxn_menus.append(self)  # register self with root to recieve menu updates
        self._root().update_menus()

    def run_command(self):

        args = [q.strip(" ") for q in self.argslist.get().split(",")]
        if args == [""]:
            args = []  # actually no args
        fx = globals()[self.v.get()]
        self._root().append_action(fx, args)
        self._root().event_generate("<<advance>>")


class MyRoot(Tk):

    """To contain data that needs to be accessible by everyone"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fxn_set = set()  # set of the names of all the functions made in the interactive text entry
        self.ignore = set()
        self.fxn_menus = []  # a list of BindingRows to force them to update their lists when new functions are made
        self.mw = None  # a reference to the main window for propagating events
        self.mapping = []  # the functions and args to be run once the tagging is complete

        # first we note everything that is callable in the global namespace. Then later, when user-defined functions
        # are introduced, we will get globals(), and compare against this list. Anything not in this list is a
        # newly-appeared callable in the global namespace and is a user-defined function so we will use it
        # to populate the drop-down menu of function choice

        for x in globals():
            if callable(globals().get(x)):
                self.ignore.add(x)

    def setup_bindings(self):

        self.bind("<<advance>>", self.mw.advance_iterator)

    def update_menus(self):

        """Force an update of the dropdowns with all available functions"""

        for x in self.fxn_menus:
            x.functionlabel["menu"].delete(0, END)
            for fx in self.fxn_set:
                x.functionlabel["menu"].add_command(label=fx, command=lambda value=fx: x.v.set(value))

    def append_action(self, fx, args):

        """Record a function and args to be applied to a picture caption"""

        cap = self.mw.pw.current_caption
        action = (fx, cap, *args)
        self.mapping.append(action)

    def apply(self):

        """The function that goes through self.mapping and actually carries out all the functions"""

        print("Applying functions...")
        for x in self.mapping:
            try:
                x[0](*x[1:])
            except Exception as e:
                print(e)
        print("done")



root = MyRoot()
myapp = MainWindow(root)
root.setup_bindings()  # make bindings now that the root object knows about all its children
myapp.pack()
root.mainloop()