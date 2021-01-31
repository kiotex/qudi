# -*- coding: utf-8 -*-

"""
ToDo: Document

Qudi is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Qudi is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Qudi. If not, see <http://www.gnu.org/licenses/>.

Copyright (c) the Qudi Developers. See the COPYRIGHT.txt file at the
top-level directory of this distribution and at <https://github.com/Ulm-IQO/qudi/>
"""

import os
import weakref
from PySide2 import QtCore, QtWidgets, QtGui
from qudi.core.datafitting import FitContainer, FitConfigurationsModel, FitConfiguration
from qudi.core.util.paths import get_artwork_dir
from qudi.core import qudi_slot


class FitWidget(QtWidgets.QWidget):
    """
    """

    sigDoFit = QtCore.Signal(str)

    def __init__(self, *args, fit_container=None, **kwargs):
        super().__init__(*args, **kwargs)
        main_layout = QtWidgets.QGridLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.selection_combobox = QtWidgets.QComboBox()
        self.selection_combobox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.fit_pushbutton = QtWidgets.QPushButton('Fit')
        self.fit_pushbutton.setMinimumWidth(3 * self.fit_pushbutton.sizeHint().width())
        self.result_label = QtWidgets.QLabel()
        self.result_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        main_layout.addWidget(self.fit_pushbutton, 0, 0)
        main_layout.addWidget(self.selection_combobox, 0, 1)
        main_layout.addWidget(self.result_label, 1, 0, 1, 2)
        main_layout.setColumnStretch(1, 1)

        self.fit_pushbutton.clicked.connect(self._fit_clicked)

        self.__fit_container_ref = lambda: None
        if fit_container is not None:
            self.link_fit_container(fit_container)

    def link_fit_container(self, fit_container):
        assert (fit_container is None) or isinstance(fit_container, FitContainer), \
            'Can only link qudi FitContainer instances.'
        old_container = self.__fit_container_ref()
        # disconnect old fit container if present
        if old_container is not None:
            old_container.sigFitConfigurationsChanged.disconnect(self.update_fit_configurations)
            old_container.sigLastFitResultChanged.disconnect(self.update_fit_result)
        # link new fit container
        self.result_label.clear()
        self.selection_combobox.clear()
        if fit_container is None:
            self.__fit_container_ref = lambda: None
        else:
            self.__fit_container_ref = weakref.ref(fit_container)
            self.selection_combobox.addItems(fit_container.fit_configuration_names)
            fit_container.sigFitConfigurationsChanged.connect(
                self.update_fit_configurations, QtCore.Qt.QueuedConnection
            )
            fit_container.sigLastFitResultChanged.connect(
                self.update_fit_result, QtCore.Qt.QueuedConnection
            )

    @qudi_slot(tuple)
    def update_fit_configurations(self, config_names):
        old_text = self.selection_combobox.currentText()
        self.selection_combobox.clear()
        self.selection_combobox.addItems(config_names)
        if old_text in config_names:
            self.selection_combobox.setCurrentText(old_text)

    @qudi_slot(str, object)
    def update_fit_result(self, fit_config, fit_result):
        if fit_config is not None:
            container = self.__fit_container_ref()
            if container is not None:
                if self.selection_combobox.currentText() != fit_config:
                    self.selection_combobox.setCurrentText(fit_config)
                self.result_label.setText(container.formatted_result(fit_result))

    @qudi_slot()
    def _fit_clicked(self):
        config = self.selection_combobox.currentText()
        self.sigDoFit.emit(config)


class FitConfigPanel(QtWidgets.QWidget):
    """
    """
    def __init__(self, *args, fit_config=None, **kwargs):
        # assert (fit_config is None) or isinstance(fit_config, FitConfiguration)
        super().__init__(*args, **kwargs)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)

        # add estimator combobox
        self.estimator_selection_combobox = QtWidgets.QComboBox()
        self.estimator_selection_combobox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        label = QtWidgets.QLabel('Estimator:')
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        hlayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(hlayout)
        hlayout.addWidget(label)
        hlayout.addWidget(self.estimator_selection_combobox)
        hlayout.addStretch(1)

        # add horizontal line
        hline = QtWidgets.QFrame()
        hline.setFrameShape(QtWidgets.QFrame.HLine)
        main_layout.addWidget(hline)

        # add parameters
        self.parameters_widgets = dict()
        self.parameters_layout = QtWidgets.QGridLayout()
        main_layout.addLayout(self.parameters_layout)

        if fit_config is not None:
            self.update_fit_config(fit_config)

    @property
    def estimator(self):
        return self.estimator_selection_combobox.currentText()

    def update_fit_config(self, config):
        self.estimator_selection_combobox.clear()
        self.estimator_selection_combobox.addItems(tuple(config.available_estimators))


class FitConfigurationItemDelegate(QtWidgets.QStyledItemDelegate):
    """
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def createEditor(self, parent, option, index):
        editor = FitConfigPanel(parent=parent)
        return editor

    def setEditorData(self, editor, index):
        if index.isValid():
            editor.update_fit_config(index.data(QtCore.Qt.DisplayRole))

    def setModelData(self, editor, model, index):
        print('setModelData:', index.row(), editor.estimator)

    def updateEditorGeometry(self, editor, option, index):
        return editor.sizeHint()

    def sizeHint(self, option, index):
        return FitConfigPanel(fit_config=index.data(QtCore.Qt.DisplayRole)).sizeHint()

    def paint(self, painter, option, index):
        painter.save()
        r = option.rect
        painter.translate(r.topLeft())
        widget = FitConfigPanel(fit_config=index.data(QtCore.Qt.DisplayRole))
        widget.render(painter, QtCore.QPoint(0, 0), painter.viewport())
        painter.restore()


class FitConfigurationWidget(QtWidgets.QWidget):
    """
    """
    _sigAddNewConfig = QtCore.Signal(str, str)  # name, model

    def __init__(self, *args, fit_config_model, **kwargs):
        assert isinstance(fit_config_model, FitConfigurationsModel)
        super().__init__(*args, **kwargs)
        main_layout = QtWidgets.QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)

        icon_dir = os.path.join(get_artwork_dir(), 'icons', 'oxygen', '64x64')

        # Create new fit config editor elements
        self.model_combobox = QtWidgets.QComboBox()
        self.model_combobox.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.model_combobox.addItems(fit_config_model.model_names)
        self.name_lineedit = QtWidgets.QLineEdit()
        self.add_config_toolbutton = QtWidgets.QToolButton()
        self.add_config_toolbutton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.add_config_toolbutton.setIcon(QtGui.QIcon(os.path.join(icon_dir, 'add-icon.png')))
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.model_combobox)
        hlayout.addWidget(self.name_lineedit)
        hlayout.addWidget(self.add_config_toolbutton)
        hlayout.setContentsMargins(0, 0, 0, 0)
        # hlayout.setStretch(0, 1)
        hlayout.setStretch(1, 1)
        main_layout.addLayout(hlayout)

        # Create fit config editor list view
        self.config_listview = QtWidgets.QListView()
        config_item_delegate = FitConfigurationItemDelegate()
        self.config_listview.setItemDelegate(config_item_delegate)
        self.config_listview.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.config_listview.setModel(fit_config_model)
        main_layout.addWidget(self.config_listview)
        main_layout.setStretch(1, 1)

        self.add_config_toolbutton.clicked.connect(self._add_config_clicked)
        self._sigAddNewConfig.connect(
            fit_config_model.add_configuration, QtCore.Qt.QueuedConnection
        )

    @qudi_slot()
    def _add_config_clicked(self):
        model = self.model_combobox.currentText()
        name = self.name_lineedit.text()
        if name and model:
            self.name_lineedit.clear()
            self._sigAddNewConfig.emit(name, model)
