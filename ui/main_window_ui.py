# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QGridLayout, QHeaderView, QMainWindow,
    QMenu, QMenuBar, QPushButton, QSizePolicy,
    QStatusBar, QTableView, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(726, 593)
        self.action_surface_energy = QAction(MainWindow)
        self.action_surface_energy.setObjectName(u"action_surface_energy")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tableView = QTableView(self.centralwidget)
        self.tableView.setObjectName(u"tableView")

        self.verticalLayout.addWidget(self.tableView)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.btn_ch2i2 = QPushButton(self.centralwidget)
        self.btn_ch2i2.setObjectName(u"btn_ch2i2")

        self.gridLayout_2.addWidget(self.btn_ch2i2, 0, 1, 1, 1)

        self.btn_export_xlsx = QPushButton(self.centralwidget)
        self.btn_export_xlsx.setObjectName(u"btn_export_xlsx")

        self.gridLayout_2.addWidget(self.btn_export_xlsx, 2, 1, 1, 1)

        self.btn_open_file = QPushButton(self.centralwidget)
        self.btn_open_file.setObjectName(u"btn_open_file")

        self.gridLayout_2.addWidget(self.btn_open_file, 2, 0, 1, 1)

        self.btn_h2o = QPushButton(self.centralwidget)
        self.btn_h2o.setObjectName(u"btn_h2o")

        self.gridLayout_2.addWidget(self.btn_h2o, 0, 0, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 726, 33))
        self.menu = QMenu(self.menubar)
        self.menu.setObjectName(u"menu")
        self.menu_2 = QMenu(self.menu)
        self.menu_2.setObjectName(u"menu_2")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menu.menuAction())
        self.menu.addAction(self.menu_2.menuAction())
        self.menu_2.addAction(self.action_surface_energy)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.action_surface_energy.setText(QCoreApplication.translate("MainWindow", u"\u8868\u9762\u80fd\u8ba1\u7b97", None))
        self.btn_ch2i2.setText(QCoreApplication.translate("MainWindow", u"\u5bfc\u5165\u4e8c\u7898\u7532\u70f7\u89d2\u5ea6", None))
        self.btn_export_xlsx.setText(QCoreApplication.translate("MainWindow", u"\u5bfc\u51fa.xlsx\u6587\u4ef6", None))
        self.btn_open_file.setText(QCoreApplication.translate("MainWindow", u"\u8ba1\u7b97\u8868\u9762\u80fd", None))
        self.btn_h2o.setText(QCoreApplication.translate("MainWindow", u"\u5bfc\u5165\u6c34\u6ef4\u89d2", None))
        self.menu.setTitle(QCoreApplication.translate("MainWindow", u"\u83dc\u5355", None))
        self.menu_2.setTitle(QCoreApplication.translate("MainWindow", u"\u6570\u636e\u5904\u7406", None))
    # retranslateUi

