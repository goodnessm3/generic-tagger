from tkinter import *
from PIL import Image, ImageTk, UnidentifiedImageError
from io import BytesIO


class MainWindow(Frame):

    """Top level window"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.supplier_window = CodeWindow()
        self.pw = PicWindow()
        self.bw = BindingsWindow()
        self.function_window = CodeWindow()

        self.supplier_window.pack(side=LEFT)
        self.pw.pack(side=LEFT)
        self.bw.pack(side=LEFT)
        self.function_window.pack(side=LEFT)


class PicWindow(Frame):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.lab = Label(self)
        self.caption = Label(self)

        self.lab.pack(side=TOP)
        self.caption.pack(side=TOP)

    def update_image(self, imgbytes, capt):

        """Expects a tuple of (PIL image, caption)"""

        im = ImageTk.PhotoImage(imgbytes)
        self.lab.configure(image=im)
        self.caption.configure(text=capt)


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
                self._root().fxn_list.append(x)
                print(f"Added {x} to the function list.")









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
        self.keylabel = Button(self)
        self.functionlabel = OptionMenu(self, self.v, self._root().fxn_list)  #
        self.argslist = Entry(self)  # list of args with which to call the function (string only)

        self.keylabel.pack(side=LEFT)
        self.functionlabel.pack(side=LEFT)
        self.argslist.pack(side=LEFT)


class MyRoot(Tk):

    """To contain data that needs to be accessible by everyone"""

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fxn_list = []  # list of all the functions made in the interactive text entry
        self.ignore = set()

        # first we note everything that is callable in the global namespace. Then later, when user-defined functions
        # are introduced, we will get globals(), and compare against this list. Anything not in this list is a
        # newly-appeared callable in the global namespace and is a user-defined function so we will use it
        # to populate the drop-down menu of function choice

        for x in globals():
            if callable(globals().get(x)):
                self.ignore.add(x)



root = MyRoot()
myapp = MainWindow(root)
myapp.pack()
root.mainloop()