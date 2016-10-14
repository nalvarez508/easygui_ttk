
try:
    import tkinter as tk  # python 3
    import tkinter.font as tk_Font
except (SystemError, ValueError, ImportError):
    import Tkinter as tk  # python 2
    import tkFont as tk_Font

try:
    from . import global_state
    from . import utils as ut
    from .text_box import textbox
except (SystemError, ValueError, ImportError):
    import global_state
    import utils as ut


import re


class GUItk(object):
    """ This is the object that contains the tk root object"""

    def __init__(self, msg, title, choices, images, default_choice, cancel_choice):
        """ Create ui object

        Parameters
        ----------
        msg : string
            text displayed in the message area (instructions...)
        title : str
            the window title
        choices : iterable of strings
            build a button for each string in choices
        images : iterable of filenames, or an iterable of iterables of filenames
            displays each image
        default_choice : string
            one of the strings in choices to be the default selection
        cancel_choice : string
            if X or <esc> is pressed, it appears as if this button was pressed.
        update: function
            if set, this function will be called when any button is pressed.


        Returns
        -------
        object
            The ui object
        """
        self._title = title
        self._msg = msg
        self._choices = choices
        self._default_choice = default_choice
        self._cancel_choice = cancel_choice
        self.callback_on_update = None
        self._choice_text = None
        self._choice_row_column = None
        self._images = list()

        self.boxRoot = tk.Tk()
        # self.boxFont = tk_Font.Font(
        #     family=global_state.PROPORTIONAL_FONT_FAMILY,
        #     size=global_state.PROPORTIONAL_FONT_SIZE)

        self.boxFont = tk_Font.nametofont("TkFixedFont")
        self.width_in_chars = global_state.fixw_font_line_length

        # default_font.configure(size=global_state.PROPORTIONAL_FONT_SIZE)

        self.configure_root(title)

        self.create_msg_widget(msg)

        self.create_images_frame()

        self.create_images(images)

        self.create_buttons_frame()

        self.create_buttons(choices, default_choice)


    # Run and stop methods ---------------------------------------

    def run(self):
        self.boxRoot.mainloop()
        self.boxRoot.destroy()

    def stop(self):
        # Get the current position before quitting
        #self.get_pos()
        self.boxRoot.quit()

    # Methods to change content ---------------------------------------
    def set_msg(self, msg):
        self.messageArea.config(state=tk.NORMAL)
        self.messageArea.delete(1.0, tk.END)
        self.messageArea.insert(tk.END, msg, 'justify')
        self.messageArea.config(state=tk.DISABLED)
        # Adjust msg height
        self.messageArea.update()
        numlines = self.get_num_lines(self.messageArea)
        self.set_msg_height(numlines)
        self.messageArea.update()

    def set_msg_height(self, numlines):
        self.messageArea.configure(height=numlines)

    def get_num_lines(self, widget):
        end_position = widget.index(tk.END)  # '4.0'
        end_line = end_position.split('.')[0]  # 4
        return int(end_line) + 1  # 5

    def set_pos(self, pos):
        self.boxRoot.geometry(pos)

    def get_pos(self):
        # The geometry() method sets a size for the window and positions it on
        # the screen. The first two parameters are width and height of
        # the window. The last two parameters are x and y screen coordinates.
        # geometry("250x150+300+300")
        geom = self.boxRoot.geometry()  # "628x672+300+200"
        global_state.window_position = '+' + geom.split('+', 1)[1]

    def remember_window_position(self):
        # Determine window location and save to global
        # TODO: Not sure where this goes, but move it out of here!
        m = re.match("(\d+)x(\d+)([-+]\d+)([-+]\d+)", self.boxRoot.geometry())
        if not m:
            raise ValueError(
                "failed to parse geometry string: {}".format(self.boxRoot.geometry()))
        width, height, xoffset, yoffset = [int(s) for s in m.groups()]
        global_state.window_position = '{0:+g}{1:+g}'.format(xoffset, yoffset)

    # Methods executing when a key is pressed -------------------------------
    def x_pressed(self):
        self._choice_text = self._cancel_choice
        self.box_updated(evnt_name='x')

    def escape_pressed(self, event):
        self._choice_text = self._cancel_choice
        self.box_updated(evnt_name='escape')

    def button_pressed(self, button_text, button_row, button_column):
        self._choice_text = button_text
        self._choice_row_column = (button_row, button_column)
        self.box_updated(evnt_name='update')

    def box_updated(self, evnt_name):
        event_to_controller = EventToController(evnt_name, self._choice_text, self._choice_row_column)
        response = self.callback_on_update(event_to_controller)
        if response.stop:
            self.stop()
        if response.msg:
            self.set_msg(response.msg)

    def hotkey_pressed(self, event=None):
        """
        Handle an event that is generated by a person interacting with a button.  It may be a button press
        or a key press.

        TODO: Enhancement: Allow hotkey to be specified in filename of image as a shortcut too!!!
        """
        self.remember_window_position()

        # Hotkeys
        if self._buttons:
            for button_name, button in self._buttons.items():
                hotkey_pressed = event.keysym
                if event.keysym != event.char:  # A special character
                    hotkey_pressed = '<{}>'.format(event.keysym)
                if button['hotkey'] == hotkey_pressed:
                    self._choice_text = button_name
                    self.box_updated(evnt_name='update')
                    return
        print("Event not understood")

    # Auxiliary methods -----------------------------------------------
    def calc_character_width(self):
        char_width = self.boxFont.measure('W')
        return char_width

    # Initial configuration methods ---------------------------------------
    # These ones are just called once, at setting.

    def configure_root(self, title):
        self.boxRoot.title(title)

        self.set_pos(global_state.window_position)

        # Resize setup
        self.boxRoot.columnconfigure(0, weight=10)
        self.boxRoot.minsize(100, 200)
        # Quit when x button pressed
        self.boxRoot.protocol('WM_DELETE_WINDOW', self.x_pressed)
        self.boxRoot.bind("<Escape>", self.escape_pressed)
        self.boxRoot.iconname('Dialog')

    def create_msg_widget(self, msg):

        if msg is None:
            msg = ""

        self.messageArea = tk.Text(
            self.boxRoot,
            width=self.width_in_chars,
            state=tk.DISABLED,
            padx=(global_state.default_hpad_in_chars) *
            self.calc_character_width(),
            relief="flat",
            background=self.boxRoot.config()["background"][-1],
            pady=global_state.default_hpad_in_chars *
            self.calc_character_width(),
            wrap=tk.WORD,
        )
        self.messageArea.tag_config('justify', justify=tk.CENTER)
        self.set_msg(msg)
        self.messageArea.grid(row=0)
        self.boxRoot.rowconfigure(0, weight=10, minsize='10m')


    def create_images_frame(self):
        self.imagesFrame = tk.Frame(self.boxRoot)
        row = 1
        self.imagesFrame.grid(row=row)
        self.boxRoot.rowconfigure(row, weight=10, minsize='10m')

    def create_images(self, img_filenames):
        """
        Create one or more images in the dialog.
        :param img_filenames:
         a list of list of filenames
        :return:
        """

        if img_filenames is None:
            return


        images = list()
        for _r, images_row in enumerate(img_filenames):
            row_number = len(img_filenames) - _r
            for column_number, filename in enumerate(images_row):
                this_image = dict()
                try:
                    this_image['tk_image'] = ut.load_tk_image(filename)
                except Exception as e:
                    print(e)
                    this_image['tk_image'] = None
                this_image['widget'] = tk.Button(
                    self.imagesFrame,
                    takefocus=1,
                    compound=tk.TOP)
                if this_image['widget'] is not None:
                    this_image['widget'].configure(image=this_image['tk_image'])
                fn = lambda text=filename, row=_r, column=column_number: self.button_pressed(text, (row, column))
                this_image['widget'].configure(command=fn)
                sticky_dir = tk.N+tk.S+tk.E+tk.W
                this_image['widget'].grid(row=row_number, column=column_number, sticky=sticky_dir, padx='1m', pady='1m', ipadx='2m', ipady='1m')
                self.imagesFrame.rowconfigure(row_number, weight=10, minsize='10m')
                self.imagesFrame.columnconfigure(column_number, weight=10)
                images.append(this_image)
        self._images = images  # Image objects must live, so place them in self.  Otherwise, they will be deleted.

    def create_buttons_frame(self):
        self.buttonsFrame = tk.Frame(self.boxRoot)
        self.buttonsFrame.grid(row=2, column=0)

    def create_buttons(self, choices, default_choice):

        unique_choices = ut.uniquify_list_of_strings(choices)

        def create_command(button_text, button_row, button_column):
            def command():
                return self.button_pressed(button_text, button_row, button_column)
            return command

        def command_when_hotkey_pressed(event):
            return self.hotkey_pressed(event)

        # Create buttons dictionary and Tkinter widgets
        buttons = dict()
        i_hack = 0


        for row, (button_text, unique_button_text) in enumerate(zip(choices, unique_choices)):
            this_button = dict()
            this_button['original_text'] = button_text
            this_button['clean_text'], this_button['hotkey'], hotkey_position = ut.parse_hotkey(button_text)
            this_button['widget'] = tk.Button(
                    self.buttonsFrame,
                    takefocus=1,
                    text=this_button['clean_text'],
                    underline=hotkey_position)

            command_when_pressed = create_command(button_text, row, 0)

            this_button['widget'].configure(command=command_when_pressed)

            this_button['widget'].grid(row=0, column=i_hack, padx='1m', pady='1m', ipadx='2m', ipady='1m')
            self.buttonsFrame.columnconfigure(i_hack, weight=10)
            i_hack += 1
            buttons[unique_button_text] = this_button
        self._buttons = buttons
        if default_choice in buttons:
            buttons[default_choice]['widget'].focus_force()
        # Bind hotkeys
        for hk in [button['hotkey'] for button in buttons.values() if button['hotkey']]:
            self.boxRoot.bind_all(hk, command_when_hotkey_pressed, add=True)


class EventToController(object):
    """ Object passed from view to controller, after each upadte"""
    def __init__(self, name, selected_choice_as_text, selected_choice_row_column):
        self.name = name
        self.selected_choice_as_text = selected_choice_as_text
        self.selected_choice_row_column = selected_choice_row_column
