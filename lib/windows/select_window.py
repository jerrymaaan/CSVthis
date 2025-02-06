from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QKeySequence, QBrush, QColor
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QShortcut,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton
)


class SelectWindow(QWidget):
    def __init__(self, vb_list, axis_list, plot_widget, curve_list, graph_label_list, config):
        super().__init__()
        # initialises instance variables
        self.vb_list = vb_list
        self.axis_list = axis_list
        self.plot_widget = plot_widget
        self.curve_list = curve_list
        self.graph_label_list = graph_label_list
        self.CONFIG = config

        # select window settings
        self.setWindowTitle("Selektieren")
        self.setMinimumSize(QSize(400, 800))

        # set styles
        self.load_stylesheet("lib/assets/style.qss")

        # window box and layout
        self.win_layout = QVBoxLayout()
        self.setLayout(self.win_layout)

        # Shortcut für ESC
        self.shortcut_exit = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_exit.activated.connect(self.close)  # type: ignore

        # adds QTreeWidget
        self.tree = QTreeWidget(self)
        self.tree.setHeaderLabel("Auswahl der Datenreihen")
        self.win_layout.addWidget(self.tree)

        # adds tree parent for main_y_axis
        self.tree_parent_list = {}
        main_y_axis = self.plot_widget.getAxis('left')
        main_y_axis_name = main_y_axis.label.toPlainText()
        self.tree_parent_list[main_y_axis_name] = QTreeWidgetItem(self.tree, [main_y_axis_name])

        # button to un-/check all
        self.un_check_all_btn = QPushButton("Alles selektieren")
        self.un_check_all_btn_state = "uncheck"  # saves state (uncheck or check)
        self.un_check_all_btn.clicked.connect(self.un_select_all)  # type: ignore
        self.win_layout.addWidget(self.un_check_all_btn)

        # adds tree parents for secondary_y_axes
        for axis_name in self.axis_list:
            axis_label = axis_list[axis_name].label.toPlainText()
            self.tree_parent_list[axis_name] = QTreeWidgetItem(self.tree, [axis_label])
            # gets color from CONFIG from corresponding sec_axis
            for sec_axis in self.CONFIG["secondary_y_axes"]:
                if sec_axis["label"] in axis_label:
                    color = sec_axis["color"]
                    brush_fore = QBrush(QColor(color))
                    self.tree_parent_list[axis_name].setForeground(0, brush_fore)
            # gets color from CONFIG from corresponding calc_axis
            for calc_axis in self.CONFIG["calc_y_axes"]:
                if calc_axis["label"] in axis_label:
                    color = calc_axis["color"]
                    brush_fore = QBrush(QColor(color))
                    self.tree_parent_list[axis_name].setForeground(0, brush_fore)

        # adds tree items to its parent
        self.item_list = {}
        for curve in curve_list:
            if curve in self.CONFIG["main_y_axis"]["columns"]:
                # adds curves from main_y_axis to main_y_axis parent tree widget
                self.item_list[curve] = QTreeWidgetItem(self.tree_parent_list[main_y_axis_name], [curve])
                self.set_check_state(self.item_list[curve])  # sets CheckState Unchecked if curve isn't visible
                continue

            # adds curves form secondary_y_axes to their parents
            for sec_axis in self.CONFIG["secondary_y_axes"]:
                if curve in sec_axis["columns"]:
                    axis_name = sec_axis["name"]
                    self.item_list[curve] = QTreeWidgetItem(self.tree_parent_list[axis_name], [curve])
                    self.set_check_state(self.item_list[curve])  # sets CheckState Unchecked if curve isn't visible

            # adds curves form calc_y_axes to their parents
            for calc_axis in self.CONFIG["calc_y_axes"]:
                if curve == calc_axis["name"]:
                    name = calc_axis["name"]
                    self.item_list[curve] = QTreeWidgetItem(self.tree_parent_list[name], [curve])
                    self.set_check_state(self.item_list[curve])  # sets CheckState Unchecked if curve isn't visible

        # adds function to tree items
        self.tree.itemChanged.connect(self.select_plot)  # type: ignore

        # expands all parents and items
        self.tree.expandAll()

    def load_stylesheet(self, filename):
        with open(filename, "r") as qss_file:
            stylesheet = qss_file.read()
            self.setStyleSheet(stylesheet)

    def select_plot(self, item):
        data_set = item.text(0)  # which is in a column (which was used to create a curve)

        # gets corresponding curve
        curve = self.curve_list[data_set]

        # shows curve
        if item.checkState(0) == Qt.Checked:
            curve.setVisible(True)
            # shows corresponding label if exists
            if data_set in self.graph_label_list:
                self.graph_label_list[data_set].show()

        # hides curve
        elif item.checkState(0) == Qt.Unchecked:
            curve.setVisible(False)
            # hides corresponding label if exists
            if data_set in self.graph_label_list:
                self.graph_label_list[data_set].hide()

    def set_check_state(self, item):
        data_set = item.text(0)
        curve = self.curve_list[data_set]

        if curve.isVisible():
            item.setCheckState(0, Qt.Checked)
        else:
            item.setCheckState(0, Qt.Unchecked)

    def un_select_all(self):
        if self.un_check_all_btn_state == "uncheck":
            for i_parents in range(self.tree.topLevelItemCount()):
                parent = self.tree.topLevelItem(i_parents)
                for i_item in range(parent.childCount()):
                    item = parent.child(i_item)
                    item.setCheckState(0, Qt.Unchecked)
            self.un_check_all_btn_state = "check"

        elif self.un_check_all_btn_state == "check":
            for i_parents in range(self.tree.topLevelItemCount()):
                parent = self.tree.topLevelItem(i_parents)
                for i_item in range(parent.childCount()):
                    item = parent.child(i_item)
                    item.setCheckState(0, Qt.Checked)
            self.un_check_all_btn_state = "uncheck"
