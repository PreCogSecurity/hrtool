import os
import logging
from PySide import QtCore, QtGui
# from PyQt4 import QtCore, QtGui
from ui.mainwindow import Ui_MainWindow
import subprocess
from debian import deb822
import gzip

logger = logging.getLogger(__name__)
CWD = os.path.abspath(os.path.dirname(__file__))


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.debs = {}
        self.parse_packages()
        self.list_components()
        self.list_installed_components()
        self.update_table()

    def list_components(self):
        components = subprocess.check_output(
            ['hr', 'cmd', 'list_components', 'install'])
        components = components.splitlines()
        for component in ['head', 'head-deps', 'opencog', 'opencog-deps']:
            if component in components:
                components.remove(component)
        self.components = components

    def list_installed_components(self):
        try:
            installed_components = subprocess.check_output(
                ['hr', 'cmd', 'list_installed'])
        except subprocess.CalledProcessError as e:
            logger.error('hr cmd list_installed failed: %s', e)
            self.installed_components = []
            return
        self.installed_components = installed_components.splitlines()

    def parse_packages(self):
        self.debs = {}
        package_file = os.path.join(CWD, 'Packages.gz')
        with gzip.open(package_file, 'rb') as f:
            content = f.read()
            packages = content.strip().split('\n\n')
            for package in packages:
                deb = deb822.Deb822(package)
                name = deb['Package']
                self.debs[name] = deb

    def get_installed_versions(self, components):
        cmd = ['dpkg-query', '-W', '-f',
               '${Package} ${Status} ${Version}\n'] + components
        try:
            versions = subprocess.check_output(cmd).splitlines()
        except subprocess.CalledProcessError as e:
            logger.error('dpkg-query failed: %s', e)
            return {}
        installed_versions = {}
        for v in versions:
            if 'installed' in v:
                toks = v.split()
                if len(toks) > 4:
                    installed_versions[toks[0]] = toks[-1]
        return installed_versions

    def update_table(self):
        cw = self.ui.componentTableWidget
        ic = self.installed_components
        installed_versions = self.get_installed_versions(ic)

        cw.setColumnCount(5)
        cw.setRowCount(len(self.components))
        cw.setColumnWidth(0, 30)
        cw.setColumnWidth(1, 300)
        cw.setColumnWidth(2, 120)
        cw.setColumnWidth(3, 120)
        labels = ['S', 'Package', 'Installed Version',
                  'Latest Version', 'Description']
        cw.setHorizontalHeaderLabels(labels)

        for row, key in enumerate(self.components):
            status = QtGui.QTableWidgetItem()
            if key in ic:
                status.setCheckState(QtCore.Qt.Checked)
            else:
                status.setCheckState(QtCore.Qt.Unchecked)
            cw.setItem(row, 0, status)
            item = QtGui.QTableWidgetItem(key)
            cw.setItem(row, 1, item)
            if key in self.debs:
                if key in installed_versions:
                    iversion = installed_versions[key]
                    installed_version = QtGui.QTableWidgetItem(iversion)
                    cw.setItem(row, 2, installed_version)
                version = QtGui.QTableWidgetItem(self.debs[key]['Version'])
                cw.setItem(row, 3, version)
                desc = QtGui.QTableWidgetItem(self.debs[key]['Description'])
                cw.setItem(row, 4, desc)


if __name__ == "__main__":
    import sys
    fh = logging.FileHandler('manager.log', mode='w')
    fh.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    sh.setLevel(logging.WARN)
    formatter = logging.Formatter(
        '[%(name)s][%(levelname)s] %(asctime)s: %(message)s')
    fh.setFormatter(formatter)
    sh.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(fh)
    root_logger.addHandler(sh)

    logger.info("Start")
    app = QtGui.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())
