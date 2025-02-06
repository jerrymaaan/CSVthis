import math
import pandas
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QAbstractTableModel, QSize
from PyQt5.QtGui import QKeySequence, QColor
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QShortcut,
    QLabel,
    QTableView,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox
)


class AnalyseWindow(QWidget):
    def __init__(self, vb_list, axis_list, plot_widget, curve_list, df, config):
        super().__init__()
        # initialises instance variables
        self.vb_list = vb_list
        self.axis_list = axis_list
        self.plot_widget = plot_widget
        self.curve_list = curve_list
        self.df = df
        self.CONFIG = config

        # select window settings
        self.setWindowTitle("Analysieren")
        self.setMinimumSize(QSize(800, 800))

        # set styles
        self.load_stylesheet("lib/assets/style.qss")

        # window box and layout
        self.win_layout = QVBoxLayout()
        self.setLayout(self.win_layout)

        # Shortcut für ESC
        self.shortcut_exit = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_exit.activated.connect(self.close)  # type: ignore

        # headline
        self.show_df = QLabel("Datenwerte")
        self.win_layout.addWidget(self.show_df)

        # data table
        self.data_table = QTableView()
        self.model = PandasModel(self.df)  # creates data model from pandas data for table widget
        self.data_table.setModel(self.model)
        self.data_table.verticalHeader().setVisible(False)
        self.win_layout.addWidget(self.data_table)

        # enable selection of whole rows
        self.data_table.setSelectionBehavior(QTableView.SelectRows)

        # enables context menu on right click
        self.data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.data_table.customContextMenuRequested.connect(self.show_context_menu)  # type: ignore

        # headline 2
        self.show_df = QLabel("Auswertung")
        self.win_layout.addWidget(self.show_df)

        # calc table
        # [mean, standard deviation, max deviation, integral]
        calc_table_row_list = ["x\u0304", "\u03C3", "\u0394max", "\u222B"]

        self.calc_table = QTableWidget()
        self.calc_table.setColumnCount(len(self.df.columns.tolist()))
        self.calc_table.setHorizontalHeaderLabels(self.df.columns.tolist())
        self.calc_table.setRowCount(len(calc_table_row_list))
        self.calc_table.setVerticalHeaderLabels(calc_table_row_list)
        self.win_layout.addWidget(self.calc_table)

        # saves started and end value for calc for calculation()
        self.start_x_val = None
        self.end_x_val = None

    def load_stylesheet(self, filename):
        with open(filename, "r") as qss_file:
            stylesheet = qss_file.read()
            self.setStyleSheet(stylesheet)

    def show_context_menu(self, position):
        # gets row
        index = self.data_table.indexAt(position)  # index on which rows the user clicked
        if not index.isValid():
            return  # no valid index (e.g. click outside table)
        row = index.row()  # get index of row

        # gets data from pandas dataframe via row
        df_row = self.df.iloc[row]
        x_axis_column = self.CONFIG["x_axis"]["column"]
        x_data = df_row[x_axis_column]

        # creates actions
        menu = QMenu()
        set_start = menu.addAction("Start")
        set_end = menu.addAction("Ende")
        unselect = menu.addAction("Alles Entfernen")
        action = menu.exec_(self.data_table.viewport().mapToGlobal(position))

        if action == set_start:
            self.remove_dashed_line('start')
            self.draw_dashed_line(x_data, 'start')
            self.model.highlight_row(row, QColor("green"))
            self.start_x_val = x_data
            self.calculation()
        elif action == set_end:
            self.remove_dashed_line('end')
            self.draw_dashed_line(x_data, 'end')
            self.model.highlight_row(row, QColor("red"))
            self.end_x_val = x_data
            self.calculation()
        elif action == unselect:
            self.remove_dashed_line('start')
            self.remove_dashed_line('end')
            self.model.unhighlight_rows()
            self.start_x_val = None
            self.end_x_val = None
            self.calc_table.clearContents()

    def draw_dashed_line(self, x_data, location):
        x = [float(x_data), float(x_data)]
        y = [-10, 10]  # doesn't really matter

        if location == 'start':
            color = 'darkgreen'
            vb = self.vb_list["dashed_start"]
        else:
            color = 'red'
            vb = self.vb_list["dashed_end"]

        pen = pg.mkPen(color=color, width=2, style=pg.QtCore.Qt.DashLine)

        # creates new curve (dashed line) and adds curve to ViewBox
        curve = pg.PlotCurveItem(x, y, pen=pen)
        vb.addItem(curve)

        # syncs vb with plot widget
        vb.setGeometry(self.plot_widget.plotItem.vb.sceneBoundingRect())
        vb.linkedViewChanged(self.plot_widget.plotItem.vb, vb.XAxis)

    def remove_dashed_line(self, location):
        if location == 'start':
            vb = self.vb_list["dashed_start"]
        else:
            vb = self.vb_list["dashed_end"]

        # removes old line
        vb.clear()

    def calculation(self):
        # if every val is set correctly
        if self.start_x_val and self.end_x_val and self.start_x_val < self.end_x_val:
            calc_df = self.df.loc[self.df[self.CONFIG["x_axis"]["column"]].between(self.start_x_val, self.end_x_val)]

            # starts calculation for every column in df
            for i, column in enumerate(calc_df.columns.tolist()):
                n_data_points = len(calc_df)

                # sum
                data_sum = 0
                for data in calc_df[column]:
                    data_sum += data

                # mean
                mean = data_sum / n_data_points
                self.calc_table.setItem(0, i, QTableWidgetItem(str(round(mean, 5))))  # row=0 => mean

                # standard deviation
                sum_deviation_to_mean_quad = 0
                for data in calc_df[column]:
                    sum_deviation_to_mean_quad += (data - mean) ** 2
                standard_deviation = math.sqrt(sum_deviation_to_mean_quad / n_data_points)
                self.calc_table.setItem(1, i, QTableWidgetItem(
                    str(round(standard_deviation, 5))))  # row=1 => standard deviation

                # max deviation
                delta_max = 0
                for data in calc_df[column]:
                    delta = abs(data - mean)
                    if delta > delta_max:
                        delta_max = delta
                self.calc_table.setItem(2, i, QTableWidgetItem(
                    str(round(delta_max, 5))))  # row=2 => max deviation

                # integral (uses trapezoidal integration)
                integral = 0
                for i_data, data in enumerate(calc_df[column]):
                    if i_data == 0:
                        continue
                    else:
                        y_1 = calc_df[column].iloc[i_data - 1]
                        y_2 = data
                        x_1 = calc_df[self.CONFIG["x_axis"]["column"]].iloc[i_data - 1]
                        x_2 = calc_df[self.CONFIG["x_axis"]["column"]].iloc[i_data]
                        integral += ((y_2 + y_1) / 2) * (x_2 - x_1)  # trapezoidal integration
                        self.calc_table.setItem(3, i, QTableWidgetItem(str(round(integral, 5))))  # row=3 => integral

        elif self.start_x_val and self.end_x_val and self.start_x_val > self.end_x_val:
            self.calc_table.clearContents()  # clears calc_table

            # creates alarm window
            msg = QMessageBox()
            msg.setWindowTitle("Fehler!")
            msg.setText(f"Der Startwert \n"
                        f"x = {self.start_x_val}\n"
                        f"muss kleiner sein als der Endwert\n"
                        f"x = {self.end_x_val}.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()


# custom model for pandas data frame (by ChatGPT)
class PandasModel(QAbstractTableModel):
    def __init__(self, dataframe: pandas.DataFrame):
        super().__init__()
        self._data = dataframe
        self.row_colors = {}  # saves color for marked row

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        elif role == Qt.BackgroundRole and index.row() in self.row_colors:
            return self.row_colors[index.row()]
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._data.columns[section]
            if orientation == Qt.Vertical:
                return None  # doesn't show row number
        return None

    def highlight_row(self, row, color):
        # removes previous marked row, if color is already used
        for r, c in self.row_colors.items():
            if c == color:
                del self.row_colors[r]
                self.dataChanged.emit(self.index(r, 0), self.index(r, self.columnCount() - 1), [Qt.BackgroundRole])
                break

        # sets new color
        self.row_colors[row] = color
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1), [Qt.BackgroundRole])

    def unhighlight_rows(self):
        if self.row_colors:  # checks if colors inside
            self.row_colors.clear()  # removes all colors

            self.dataChanged.emit(self.index(0, 0),
                                  self.index(self.rowCount() - 1,
                                             self.columnCount() - 1),
                                  [Qt.BackgroundRole])
