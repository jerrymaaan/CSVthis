import json
import os
import importlib.util
import pandas
import re
import pyqtgraph as pg
from lib.windows.select_window import SelectWindow
from lib.windows.analyse_window import AnalyseWindow
from lib.windows.loading_window import LoadingWindow
from PyQt5.QtCore import QSize, Qt, QCoreApplication
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QComboBox,
    QPushButton,
    QShortcut
)


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # directory and list of CSV files
        if os.path.exists("data"):  # checks if folder /data exists
            self.csv_path = "data"
            self.csv_files = os.listdir("data")
        else:
            # exits programm if folder is missing
            print("Folder /data is missing!")
            exit(1)

        # reads config.json
        with open('lib/config.json', 'r') as f:
            self.CONFIG = json.load(f)

        # main window settings
        self.setWindowTitle(f'{self.CONFIG["settings"]["use_case"]} | Version {self.CONFIG["settings"]["version"]}')
        self.setMinimumSize(QSize(800, 600))
        self.showMaximized()

        # set styles
        self.load_stylesheet("lib/assets/style.qss")

        # main window box and layout
        self.main_box = QWidget()
        self.main_layout = QVBoxLayout()
        self.main_box.setLayout(self.main_layout)
        self.setCentralWidget(self.main_box)

        # initialise secondary windows
        self.select_window = None
        self.analyse_window = None
        self.loading_window = LoadingWindow()

        # Shortcut für ESC
        self.shortcut_exit = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_exit.activated.connect(self.close)  # type: ignore

        # dropdown_box
        self.dropdown_box = QWidget()
        self.dropdown_layout = QHBoxLayout()
        self.dropdown_box.setLayout(self.dropdown_layout)
        self.main_layout.addWidget(self.dropdown_box)
        self.dropdown_layout.setAlignment(Qt.AlignLeft)

        # dropdown label
        self.dropdown_label = QLabel("Datei:")
        self.dropdown_layout.addWidget(self.dropdown_label)

        # dropdown
        self.dropdown = QComboBox()
        dropdown_list = self.csv_files
        dropdown_list.insert(0, "Datei auswählen")
        self.dropdown.addItems(dropdown_list)
        self.dropdown.currentTextChanged.connect(self.choose_file)  # type: ignore
        self.dropdown_layout.addWidget(self.dropdown)

        # deactivates the first item in the dropdown list
        self.model = self.dropdown.model()
        self.item = self.model.item(0)
        self.item.setFlags(self.item.flags() & ~Qt.ItemIsEnabled)

        # headline2
        self.headline2 = QLabel("Keine Datei ausgewählt")
        self.dropdown_layout.addWidget(self.headline2)

        # button to select plots
        self.select_plotted_data_btn = QPushButton("Selektieren")
        self.select_plotted_data_btn.clicked.connect(self.select_plotted_data)  # type: ignore
        self.select_plotted_data_btn.setVisible(False)
        self.dropdown_layout.addWidget(self.select_plotted_data_btn)

        # button to analyse
        self.analyse_data_btn = QPushButton("Analysieren")
        self.analyse_data_btn.clicked.connect(self.analyse_data)  # type: ignore
        self.analyse_data_btn.setVisible(False)
        self.dropdown_layout.addWidget(self.analyse_data_btn)

        # pyqtgraph
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', self.CONFIG["main_y_axis"]["label"])  # setting y-axis
        self.plot_widget.setLabel('bottom', self.CONFIG["x_axis"]["label"])  # setting x-axis
        self.plot_widget.setBackground("lightgray")
        self.plot_widget.setMouseEnabled(x=True, y=False)  # disables rescaling y-axis
        self.main_layout.addWidget(self.plot_widget)

        # styles axes
        self.plot_widget.getAxis('bottom').setTextPen('black')
        self.plot_widget.getAxis('left').setTextPen('black')

        # initializes lists to save objects and access them later in select window
        self.curve_list = {}  # adds objects in plot_data()
        self.vb_list = {}  # adds objects in adds_axes()
        self.axis_list = {}  # adds objects in adds_axes()
        self.graph_label_list = {}

        # adds axes for plot widget
        self.adds_axes()

        # initializes dataframe to save df and access it in different functions
        self.df = None

        # adds extra vb for analyse_window to draw dashed lines
        self.add_vb_dashed_line()

    def load_stylesheet(self, filename):
        with open(filename, "r") as qss_file:
            stylesheet = qss_file.read()
            self.setStyleSheet(stylesheet)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.plot_widget.plotItem.getViewBox().setMouseMode(pg.ViewBox.RectMode)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.plot_widget.plotItem.getViewBox().setMouseMode(pg.ViewBox.PanMode)

    def adds_axes(self):
        # adds axis for every secondary_y_axes item
        axes_to_add = self.CONFIG["secondary_y_axes"] + self.CONFIG["calc_y_axes"]
        for axis in axes_to_add:
            index = axes_to_add.index(axis)
            axis_label = axis['label']
            axis_name = axis['name']
            color = axis['color']

            # creates new axis
            axis = pg.AxisItem("right")
            axis.setLabel(axis_label)
            axis.setTextPen(pg.mkPen(color))
            axis.setPen(pg.mkPen(color))

            #  saves axis objects
            self.axis_list[axis_name] = axis

            # adds axis to plotItem
            self.plot_widget.plotItem.layout.addItem(axis, 2, 3 + index * 60)

            # creates new ViewBox and adds to plot widget
            vb = pg.ViewBox()
            self.plot_widget.scene().addItem(vb)
            axis.linkToView(vb)

            # synchronises x-axis
            vb.setXLink(self.plot_widget.plotItem.vb)

            # saves vb objects
            self.vb_list[axis_name] = vb

    def choose_file(self, s):
        # ends function to prevent running the following code when "Datei auswählen" is set
        if s == "Datei auswählen":
            return

        # starts loading window
        self.loading_window.show()
        app = QCoreApplication.instance()
        app.processEvents()  # manually starts event loop to show loading_window correctly;
        # app is the Core application

        # set headline 2
        try:
            year, month, day, hr, minutes = str(2000 + int(s[:2])), s[2:4], s[4:6], s[7:9], s[9:11]
            hint = s[12:]
            self.headline2.setText("Jahr: " + year
                                   + ", Monat: " + month
                                   + ", Tag: " + day
                                   + ", Start der Messung: " + hr + ":" + minutes
                                   + ", Bemerkung: " + hint)
        except ValueError:
            self.headline2.setText(s)

        # clears data from old plot
        self.plot_widget.clear()
        self.curve_list = {}
        for vb_name in self.vb_list:
            vb = self.vb_list[vb_name]
            vb.clear()

        # extracts data
        file = os.path.join(self.csv_path, s)
        self.df = pandas.read_csv(file, encoding='latin-1', sep=self.CONFIG["settings"]["seperator"])

        # converts every column to float if possible
        for col in self.df.columns:
            try:
                self.df[col] = self.df[col].astype(str).str.replace(',', '.').astype(float)
            except ValueError:
                print("Couldn't convert column '" + col + "' to float.")
            except AttributeError:
                self.df[col] = self.df[col].str.replace(',', '.').astype(float)

        # changes hh:mm:ss to minutes
        if self.CONFIG["settings"]["column_in_hh_mm_ss"]:
            time_col = self.CONFIG["settings"]["column_in_hh_mm_ss"]
            for i in range(len(self.df)):
                h, m, s = self.df.iloc[i][time_col].split(':')
                self.df.at[i, time_col] = int(h) * 3600 + int(m) * 60 + int(s)

        # calculate new data
        self.calc_data()

        # plots data
        self.plot_data()

        # sets buttons visible
        self.select_plotted_data_btn.setVisible(True)
        self.analyse_data_btn.setVisible(True)

        # closes loading window
        self.loading_window.close()

    def calc_data(self):
        # calcs axes
        for calc_axis in self.CONFIG["calc_y_axes"]:

            if "formula" in calc_axis:   # calculates new data with eval
                # formula from config.json
                formula = calc_axis["formula"]
                name = calc_axis["name"]

                # extracts column names from formular
                matched_var = re.findall(r'\[(.*?)]', formula)

                # checks if every column name from formula exists in dataframe df
                if all(col in self.df.columns for col in matched_var):

                    # changes column names in formula with dataframe access
                    formular_calc = formula
                    for column in matched_var:
                        formular_calc = formular_calc.replace(f"[{column}]", f"self.df['{column}']")

                    try:
                        self.df[name] = round(eval(formular_calc), 5)  # calculates formular_calc with eval
                    except Exception as e:
                        print("Error while trying to calculate formula:", e)

                else:
                    print("One ore more columns from formular doesn't exist in CSV-file.")

            elif "script" in calc_axis:   # calculates new data with script
                # gets script name and columns from config.json
                script_name = calc_axis["script"]
                name = calc_axis["name"]

                # path to all personal scripts
                file_path = os.path.join("lib/personal_scripts", f"{script_name}.py")

                # loading module dynamically
                spec = importlib.util.spec_from_file_location(script_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # tries to call function with same name as script
                function = getattr(module, script_name, None)

                if callable(function):
                    try:
                        result = function(self.df.copy())  # calls function
                        self.df[name] = round(result, 5)
                    except Exception as e:
                        print(f"Error trying to run script '{script_name}':", e)
                else:
                    print(f"The function '{script_name}' doesn't exist in the script file.")

    def plot_data(self):
        # -------------- x axis --------------
        # column from config file
        x_column = self.CONFIG["x_axis"]["column"]

        # column from CSV file
        try:
            x_data = self.df[x_column].tolist()
        except KeyError:
            print("Column name '" + x_column + "' for x-axis from config.json doesn't exist in CSV-file.")
            return

        # -------------- y axis --------------
        # columns from CSV file
        column_list = self.df.columns.tolist()

        for column_from_df in column_list:
            # skips x_column
            if column_from_df == x_column:
                continue

            y_data = self.df[column_from_df].tolist()

            # checks if column is in column from main_y_axis from config.json
            for main_column in self.CONFIG["main_y_axis"]["columns"]:
                if column_from_df in main_column:
                    # plots on main y-axis
                    curve = self.plot_widget.plot(x_data, y_data, pen=pg.mkPen(color='black'))
                    self.curve_list[column_from_df] = curve

                    # activates clickable curve
                    curve.setCurveClickable(True)
                    curve.sigClicked.connect(
                        lambda _, ev, col=column_from_df: self.show_plot_label(ev, "black", col)
                    )

            # checks if column is in any column from secondary_y_axes from config.json
            axis_to_add = self.CONFIG["secondary_y_axes"]
            for new_axis in axis_to_add:
                columns_to_add = new_axis["columns"]
                if column_from_df in columns_to_add:
                    category = new_axis["name"]

                    # gets ViewBox, axis
                    vb = self.vb_list[category]
                    axis = self.axis_list[category]
                    axis_color = axis.pen().color().name()

                    # creates new curve and adds curve to ViewBox; plots data on one of secondary y-axes
                    curve = pg.PlotCurveItem(x_data, y_data, pen=axis_color)
                    vb.addItem(curve)

                    # syncs every vb with plot widget; needs extra function so lambda gets new vb for each iteration
                    self.sync_vb_and_plotwidget(vb)

                    # saves curve object
                    self.curve_list[column_from_df] = curve

                    # activates clickable curve
                    curve.setClickable(True)
                    curve.sigClicked.connect(
                        lambda _, ev, color=axis_color, col=column_from_df: self.show_plot_label(ev, color, col)
                    )

            # checks if column is in any calc_y_axes from config.json
            calc_axes = self.CONFIG["calc_y_axes"]
            for calc_axis in calc_axes:
                if column_from_df == calc_axis["name"]:
                    category = calc_axis["name"]

                    # gets ViewBox, axis
                    vb = self.vb_list[category]
                    axis = self.axis_list[category]
                    axis_color = axis.pen().color().name()

                    # creates new curve and adds curve to ViewBox; plots data on one of secondary y-axes
                    curve = pg.PlotCurveItem(x_data, y_data, pen=axis_color)
                    vb.addItem(curve)

                    # syncs every vb with plot widget; needs extra function so lambda gets new vb for each iteration
                    self.sync_vb_and_plotwidget(vb)

                    # saves curve object
                    self.curve_list[column_from_df] = curve

                    # activates clickable curve
                    curve.setClickable(True)
                    curve.sigClicked.connect(
                        lambda _, ev, color=axis_color, col=column_from_df: self.show_plot_label(ev, color, col)
                    )

    def sync_vb_and_plotwidget(self, vb):
        # Synchronize the geometry of the ViewBox with the main plot
        self.plot_widget.plotItem.vb.sigResized.connect(
            lambda: (
                vb.setGeometry(self.plot_widget.plotItem.vb.sceneBoundingRect()),
                vb.linkedViewChanged(self.plot_widget.plotItem.vb, vb.XAxis)
            )
        )

    def show_plot_label(self, event, color, label):
        # mouse position in scene koordinates
        scene_pos = event.scenePos()

        # gets plot koordinates from scene koordinates
        plot_pos = self.plot_widget.plotItem.vb.mapSceneToView(scene_pos)

        if label in self.graph_label_list:

            # checks coordinates
            if self.graph_label_list[label].pos() == plot_pos:
                # removes label if it already exists and click is on the same position
                self.plot_widget.removeItem(self.graph_label_list[label])  # removes from plot
                self.graph_label_list.pop(label)  # removes reference from dictionary graph_label_list
                del label  # removes reference "once and for all"

            else:
                # sets new position if label already exists and click is on another point of the graph
                self.graph_label_list[label].setPos(plot_pos.x(), plot_pos.y())

        else:
            # creates new label and sets position; saves in list to access label from other windows
            self.graph_label_list[label] = pg.TextItem(label, color=color, anchor=(0.5, 0.5), fill=(211, 211, 211, 240))
            self.graph_label_list[label].setVisible(True)
            self.plot_widget.addItem(self.graph_label_list[label])
            self.graph_label_list[label].setPos(plot_pos.x(), plot_pos.y())

    def select_plotted_data(self):
        if self.select_window is None:
            self.select_window = SelectWindow(
                self.vb_list, self.axis_list, self.plot_widget,
                self.curve_list, self.graph_label_list, self.CONFIG
            )
            self.select_window.setAttribute(Qt.WA_DeleteOnClose)  # deletes windows on close
            self.select_window.destroyed.connect(self.reset_select_window)
        self.select_window.show()

    def reset_select_window(self):
        self.select_window = None

    def analyse_data(self):
        if self.analyse_window is None:
            self.analyse_window = AnalyseWindow(self.vb_list, self.axis_list,
                                                self.plot_widget, self.curve_list, self.df, self.CONFIG)
            self.analyse_window.setAttribute(Qt.WA_DeleteOnClose)  # deletes windows on close
            self.analyse_window.destroyed.connect(self.reset_analyse_window)
        self.analyse_window.show()

    def reset_analyse_window(self):
        self.analyse_window = None
        self.vb_list["dashed_start"].clear()
        self.vb_list["dashed_end"].clear()

    def add_vb_dashed_line(self):
        # creates new ViewBox and adds to plot widget for dashed line
        vb_start = pg.ViewBox()
        vb_end = pg.ViewBox()
        self.plot_widget.scene().addItem(vb_start)
        self.plot_widget.scene().addItem(vb_end)

        # synchronises x-axis
        vb_start.setXLink(self.plot_widget.plotItem.vb)
        vb_end.setXLink(self.plot_widget.plotItem.vb)

        # saves vb
        self.vb_list["dashed_start"] = vb_start
        self.vb_list["dashed_end"] = vb_end
