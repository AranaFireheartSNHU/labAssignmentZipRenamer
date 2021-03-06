#!/usr/bin/env python
import os
from sys import argv, exit
import platform
from os import path
from logging import basicConfig, getLogger, DEBUG, INFO, CRITICAL
from pickle import dump, load
from zipfile import ZipFile
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, QSettings, Qt, QDir, QCoreApplication
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QMessageBox, QFileSystemModel, QHeaderView
# Change the current dir to the temporary one created by PyInstaller for MSWindowOS
try:
    from sys import _MEIPASS
    os.chdir(_MEIPASS)
    print(f"On MSWindows OS {_MEIPASS}")
except ImportError:
    pass    # Must be macOS, just forget it and move on...

import zipRenamerResources_rc

homeDir = path.expanduser('~')

namingPatternDefault = 'full'   # options: name, name-email or full
removeZipFilesDefault = False
logFilenameDefault = 'zipRenamer.log'
rootFolderNameDefault = './'
createLogFileDefault = True
pickleFilenameDefault = ".zipRenamerSavedObjects.pl"
showHelpOnStartupDefault = True

baseDir = os.path.dirname(__file__)


class ZipRenamer(QMainWindow):
    """A zip file extraction & renaming utility for zyBooks project lab file downloads"""

    def __init__(self, parent=None):
        """ Build a GUI  main window for zipRenamer."""

        super().__init__(parent)
        self.logger = getLogger("Fireheart.zipRenamer")
        self.appSettings = QSettings()
        self.quitCounter = 0       # used in a workaround for a QT5 bug.

        self.pickleFilename = pickleFilenameDefault
        self.restoreSettings()

        try:
            self.zipFileFound, self.statusMessage, self.textOutput = self.restoreApp()
        except FileNotFoundError:
            self.restartApp()

        uic.loadUi("zipRenamerMainWindow.ui", self)

        self.textOutputUI.appendPlainText("Hello")
        self.textOutputUI.repaint()
        self.zipFileFound = False
        self.statusMessage = ""
        if self.logger.getEffectiveLevel() == 10:   # Logger is set to debug level.
            self.textOutput = f"createLogFile: {self.createLogFile}\nrootFolderName: {self.rootFolderName}\nlogFilename: {self.logFilename}\nnamingPattern: {self.namingPattern}\npickleFilename: {self.pickleFilename}\nshowHelpOnStartup: {self.showHelpOnStartup}"
        else:
            self.textOutput = ""

        self.preferencesSelectButton.clicked.connect(self.preferencesSelectButtonClickedHandler)
        self.helpSelectUI.clicked.connect(self.helpSelectButtonClickedHandler)
        self.rootFolderSelectButton.clicked.connect(self.rootFolderSelectButtonClickedHandler)
        self.currentRootFilePathLabel.clicked.connect(self.rootFolderSelectButtonClickedHandler)
        self.convertButton.clicked.connect(self.convertButtonClickedHandler)
        self.setWindowIcon(QIcon('images/zipRenamer.png'))
        self.logger.info("Application startup completed.")

        self.updateUI()
        # Startup with the help dialog opened.
        if self.showHelpOnStartup:
            self.helpSelectButtonClickedHandler()

    def __str__(self):
        """String representation for zipRenamer.
        """
        return "A zip file extraction & renaming utility for zyBooks project lab file downloads"

    def updateUI(self):
        self.textOutputUI.setPlainText(self.textOutput)
        self.textOutputUI.repaint()
        self.currentRootFilePathLabel.setText(self.rootFolderName)
        if len(self.statusMessage) > 0:
            self.zipStatusBarUI.showMessage(self.statusMessage, 5000)
            self.statusMessage = ""

    def setRootFolderName(self, newFolderName):
        self.rootFolderName = newFolderName
        self.appSettings.setValue('rootFolderName', self.rootFolderName)

    def getRootFolderName(self):
        return self.rootFolderName

    def restartApp(self):
        if self.createLogFile:
            self.logger.debug("Restarting program")

    def saveApp(self):
        if self.createLogFile:
            self.logger.debug("Saving program state")
        saveItems = (self.zipFileFound, self.statusMessage, self.textOutput)
        if self.appSettings.contains('pickleFilename'):
            with open(path.join(path.dirname(path.realpath(__file__)),  self.appSettings.value('pickleFilename', type=str)), 'wb') as pickleFile:
                dump(saveItems, pickleFile)
        elif self.createLogFile:
            self.logger.critical("No pickle Filename")

    def restoreApp(self):
        if self.appSettings.contains('pickleFilename'):
            self.appSettings.value('pickleFilename', type=str)
            with open(path.join(path.dirname(path.realpath(__file__)),  self.appSettings.value('pickleFilename', type=str)), 'rb') as pickleFile:
                return load(pickleFile)
        else:
            self.logger.critical("No pickle Filename")

    def restoreSettings(self):
        # Restore settings values, write defaults to any that don't already exist.
        if appSettings.contains('createLogFile'):
            self.createLogFile = appSettings.value('createLogFile')
        else:
            self.createLogFile = createLogFileDefault
            appSettings.setValue('createLogFile', self.createLogFile)

        if self.createLogFile:
            self.logger.debug("Starting restoreSettings")

        if self.appSettings.contains('rootFolderName'):
            self.rootFolderName = self.appSettings.value('rootFolderName', type=str)
        else:
            self.rootFolderName = rootFolderNameDefault
            self.appSettings.setValue('rootFolderName', self.rootFolderName)

        if self.appSettings.contains('logFilename'):
            self.logFilename = self.appSettings.value('logFilename', type=str)
        else:
            self.logFilename = logFilenameDefault
            self.appSettings.setValue('logFilename', self.logFilename)

        if self.appSettings.contains('namingPattern'):
            self.namingPattern = self.appSettings.value('namingPattern', type=str)
        else:
            self.namingPattern = namingPatternDefault
            self.appSettings.setValue('namingPattern', self.namingPattern)

        if self.appSettings.contains('removeZipFiles'):
            self.removeZipFiles = self.appSettings.value('removeZipFiles', type=bool)
        else:
            self.removeZipFiles = removeZipFilesDefault
            self.appSettings.setValue('removeZipFiles', self.removeZipFiles)

        if self.appSettings.contains('pickleFilename'):
            self.pickleFilename = self.appSettings.value('pickleFilename', type=str)
        else:
            self.pickleFilename = pickleFilenameDefault
            self.appSettings.setValue('pickleFilename', self.pickleFilename)

        if self.appSettings.contains('showHelpOnStartup'):
            self.showHelpOnStartup = self.appSettings.value('showHelpOnStartup', type=bool)
        else:
            self.showHelpOnStartup = showHelpOnStartupDefault
            self.appSettings.setValue('showHelpOnStartup', self.showHelpOnStartup)

    def convertButtonClickedHandler(self):
        if not path.exists(self.getRootFolderName()):
            self.statusMessage = f"Folder {self.getRootFolderName()} doesn't exist. Click the Folder Icon to select a different one."
        self.textOutput = f"Unzipped and renamed the following Files in folder\n  {self.getRootFolderName()}:\n"
        for root, dirs, files in os.walk(self.getRootFolderName()):
            if len(files) > 0:
                self.textOutput += f"\nSubfolder: {path.basename(root)}:\n"
                for file in files:
                    if len(file) > 0:
                        if type(file) is tuple:
                            self.logger.critical(f"File type mismatch!\n Root: {root}\nDirs: {dirs}\nFiles: {files}")
                        fullFilename = path.join(root, file)
                        if fullFilename.endswith('.zip'):
                            # opening the zip file in READ mode
                            self.zipFileFound = True
                            with ZipFile(fullFilename, 'r') as zipArchive:
                                for zippedFile in zipArchive.namelist():
                                    if zippedFile.endswith(".py"):
                                        try:
                                            zipArchive.extract(zipArchive.getinfo(zippedFile), root)
                                            if self.namingPattern == "full":
                                                newFilename = path.join(root, f"{file[:-4]}.py")
                                            elif self.namingPattern.startswith("name"):
                                                if file.count('_') == 4:
                                                    lastname, firstName, emailAddress, year, datePlus = file.split('_')
                                                elif file.count('_') == 5:
                                                    lastname, middleName, firstName, emailAddress, year, datePlus = file.split('_')
                                                else:
                                                    raise ValueError
                                                if self.namingPattern == "name":
                                                    newFilename = path.join(root, f"{firstName.capitalize()}{lastname.capitalize()}.py")
                                                elif self.namingPattern == "name-email":
                                                    newFilename = path.join(root, f"{firstName.capitalize()}{lastname.capitalize()}_{emailAddress}.py")
                                            else:
                                                self.logger.critical(f"Unknown file naming pattern {self.namingPattern}")
                                            os.rename(path.join(root, zippedFile), newFilename)
                                            self.textOutput += f"        {path.basename(newFilename)}\n"
                                            self.logger.info(f"UnZipped: {path.basename(zippedFile)} as {path.basename(newFilename)} from Folder {path.basename(root)}")
                                            if self.removeZipFiles:
                                                os.remove(fullFilename)
                                                self.logger.info(f"Removed: {fullFilename}")
                                        except (FileNotFoundError, FileExistsError) as errorObj:
                                            print(errorObj)
                                        except ValueError:
                                            print(f"ValueError on file {file}")
                    self.updateUI()
        if not self.zipFileFound:
            self.textOutput = f"No ZIP files were found in the current folder."
        self.updateUI()

    @pyqtSlot()  # User is requesting a top level folder select.
    def rootFolderSelectButtonClickedHandler(self):
        folderDialog = FolderSelectDialog(self.getRootFolderName())
        folderDialog.show()
        folderDialog.exec_()
        self.updateUI()

    @pyqtSlot()  # User is requesting preferences editing dialog box.
    def preferencesSelectButtonClickedHandler(self):
        if self.createLogFile:
            self.logger.info("Setting preferences")
        preferencesDialog = PreferencesDialog()
        preferencesDialog.show()
        preferencesDialog.exec_()
        self.restoreSettings()              # 'Restore' settings that were changed in the dialog window.
        self.updateUI()

    @pyqtSlot()  # User is requesting preferences editing dialog box.
    def helpSelectButtonClickedHandler(self):
        if self.createLogFile:
            self.logger.info("Help dialog opened.")
        helpDialog = HelpDialog()
        helpDialog.show()
        helpDialog.exec_()
        self.restoreSettings()              # 'Restore' settings that were changed in the dialog window.
        self.updateUI()

    @pyqtSlot()				# Player asked to quit the game.
    def closeEvent(self, event):
        if self.createLogFile:
            self.logger.debug("Closing app event")
        if self.quitCounter == 0:
            self.quitCounter += 1
            quitMessage = "Are you sure you want to quit?"
            reply = QMessageBox.question(self, 'Message', quitMessage, QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.saveApp()
                event.accept()
            else:
                self.quitCounter = 0
                event.ignore()


class FolderSelectDialog(QDialog):
    def __init__(self, startingFolderName, parent=ZipRenamer):
        super(FolderSelectDialog, self).__init__()
        uic.loadUi('rootSelectDialog.ui', self)
        if platform.system() == "Darwin+":
            pass
        else:
            fileModel = QFileSystemModel()
            # fileModel.setFilter(QDir.AllDirs | QDir.Hidden | QDir.AllEntries | QDir.NoDotAndDotDot)
            fileModel.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
            # fileModel.setRootPath('/Volumes')
            fileModel.setRootPath(startingFolderName)
            self.selectedPath = '/Volumes/Macintosh HD'
            self.selectedPath = startingFolderName
            self.fileSelectTreeView.setModel(fileModel)
            self.fileSelectTreeView.setCurrentIndex(fileModel.index(startingFolderName))
            self.fileSelectTreeView.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        if platform.system() == "Darwin+":
            iconFilename = 'images/zipRenamer.icns'
        else:
            iconFilename = 'images/zipRenamer.ico'
        self.setWindowIcon(QIcon(os.path.join(baseDir, iconFilename)))

        self.fileSelectTreeView.doubleClicked.connect(self.fileDoubleClickedHandler)
        self.buttonBox.rejected.connect(self.cancelClickedHandler)
        self.buttonBox.accepted.connect(self.okayClickedHandler)
        self.fileSelectTreeView.clicked.connect(self.selectionChangedHandler)
        self.fileSelectTreeView.expanded.connect(self.itemExpandedHandler)

    # @pyqtSlot()
    def fileDoubleClickedHandler(self, signal):
        # print(signal)
        filePath = self.fileSelectTreeView.model().filePath(signal)
        if path.isdir(filePath):
            # print(filePath)
            ZipRenamerApp.setRootFolderName(filePath)
            self.close()
        else:
            print("File selected, not directory")

    # @pyqtSlot()
    def okayClickedHandler(self):
        # print(self.selectedPath)
        if path.isdir(self.selectedPath):
            ZipRenamerApp.setRootFolderName(self.selectedPath)
            self.close()
        else:
            print("File Selected on Okay")

    # @pyqtSlot(QItemSelection)
    def selectionChangedHandler(self, selected):
        self.fileSelectTreeView.resizeColumnToContents(0)
        # print(selected)
        if path.isdir(self.fileSelectTreeView.model().filePath(selected)):
            self.selectedPath = self.fileSelectTreeView.model().filePath(selected)
            # print(self.selectedPath)
        else:
            print("File Selected")

    # @pyqtSlot()
    def itemExpandedHandler(self, selected):
        self.fileSelectTreeView.resizeColumnToContents(0)

    # @pyqtSlot()
    def cancelClickedHandler(self):
        self.close()


class PreferencesDialog(QDialog):
    def __init__(self, parent=ZipRenamer):
        super(PreferencesDialog, self).__init__()

        uic.loadUi('preferencesDialog.ui', self)
        self.logger = getLogger("Fireheart.zipRenamer")

        self.logger.debug("Starting Preferences Dialog launch.")
        self.appSettings = QSettings()
        if self.appSettings.contains('logFilename'):
            self.logFilename = self.appSettings.value('logFilename', type=str)
        else:
            self.logFilename = logFilenameDefault
            self.appSettings.setValue('logFilename', self.logFilename)

        if self.appSettings.contains('namingPattern'):
            self.namingPattern = self.appSettings.value('namingPattern', type=str)
        else:
            self.namingPattern = namingPatternDefault
            self.appSettings.setValue('namingPattern', self.namingPattern)

        if self.appSettings.contains('removeZipFiles'):
            self.removeZipFiles = self.appSettings.value('removeZipFiles', type=bool)
        else:
            self.removeZipFiles = removeZipFilesDefault
            self.appSettings.setValue('removeZipFiles', self.removeZipFiles)

        if self.appSettings.contains('createLogFile'):
            self.createLogFile = self.appSettings.value('createLogFile')
        else:
            self.createLogFile = logFilenameDefault
            self.appSettings.setValue('createLogFile', self.createLogFile)
        self.logger.debug("Preferences settings restored.")

        if platform.system() == "Darwin+":
            iconFilename = 'images/zipRenamer.icns'
        else:
            iconFilename = 'images/zipRenamer.ico'
        self.setWindowIcon(QIcon(os.path.join(baseDir, iconFilename)))

        self.buttonBox.rejected.connect(self.cancelClickedHandler)
        self.buttonBox.accepted.connect(self.okayClickedHandler)
        self.logFilenameUI.editingFinished.connect(self.logFilenameChanged)
        self.namingPatternNameUI.toggled.connect(self.nameOnlySelected)
        self.namingPatternNameEmailUI.toggled.connect(self.nameEmailSelected)
        self.namingPatternFullUI.toggled.connect(self.nameFullSelected)
        self.removeZipFilesUI.stateChanged.connect(self.removeZipFilesChanged)
        self.createLogFileUI.stateChanged.connect(self.createLogFileChanged)
        self.logger.debug("Preferences dialog object built.")

        self.updateUI()

    # @pyqtSlot()
    def logFilenameChanged(self):
        self.logFilename = self.logFilenameUI.text()

    # @pyqtSlot()
    def nameOnlySelected(self, selected):
        if selected:
            self.namingPattern = "name"

    # @pyqtSlot()
    def nameEmailSelected(self, selected):
        if selected:
            self.namingPattern = "name-email"

    # @pyqtSlot()
    def nameFullSelected(self, selected):
        if selected:
            self.namingPattern = "full"

    # @pyqtSlot()
    def removeZipFilesChanged(self):
        self.removeZipFiles = self.removeZipFilesUI.isChecked()

    # @pyqtSlot()
    def createLogFileChanged(self):
        self.createLogFile = self.createLogFileCUI.isChecked()

    def updateUI(self):
        self.logger.debug("Updating Preferences UI.")
        self.logFilenameUI.setText(str(self.logFilename))
        self.namingPatternNameUI.setChecked(False)
        self.namingPatternNameEmailUI.setChecked(False)
        self.namingPatternFullUI.setChecked(False)
        if self.namingPattern == "name":
            self.namingPatternNameUI.setChecked(True)
        elif self.namingPattern == "name-email":
            self.namingPatternNameEmailUI.setChecked(True)
        if self.namingPattern == "full":
            self.namingPatternFullUI.setChecked(True)

        if self.removeZipFiles:
            self.removeZipFilesUI.setCheckState(Qt.Checked)
        else:
            self.removeZipFilesUI.setCheckState(Qt.Unchecked)

        if self.createLogFile:
            self.createLogFileUI.setCheckState(Qt.Checked)
        else:
            self.createLogFileUI.setCheckState(Qt.Unchecked)
        self.logger.debug("Preferences UI Updated.")

    # @pyqtSlot()
    def okayClickedHandler(self):
        # write out all settings
        preferencesGroup = (('logFilename', self.logFilename),
                            ('namingPattern', self.namingPattern),
                            ('removeZipFiles', self.removeZipFiles),
                            ('createLogFile', self.createLogFile),
                            )
        # Write settings values.
        for setting, variableName in preferencesGroup:
            self.appSettings.setValue(setting, variableName)
        self.close()

    # @pyqtSlot()
    def cancelClickedHandler(self):
        self.close()


class HelpDialog(QDialog):
    def __init__(self, parent=ZipRenamer):
        super(HelpDialog, self).__init__()

        uic.loadUi('helpDialog.ui', self)
        self.logger = getLogger("Fireheart.zipRenamer")

        self.appSettings = QSettings()
        if self.appSettings.contains('showHelpOnStartup'):
            self.showHelpOnStartup = self.appSettings.value('showHelpOnStartup', type=bool)
        else:
            self.self.showHelpOnStartup = showHelpOnStartupDefault
            self.appSettings.setValue('showHelpOnStartup', self.showHelpOnStartup)

        if platform.system() == "Darwin+":
            iconFilename = 'images/zipRenamer.icns'
        else:
            iconFilename = 'images/zipRenamer.ico'
        self.setWindowIcon(QIcon(os.path.join(baseDir, iconFilename)))

        self.buttonBox.accepted.connect(self.okayClickedHandler)
        self.helpOnStartupUI.stateChanged.connect(self.helpOnStartupChanged)

        try:
            self.helpText = ""
            with open("helpDialog.html", 'r') as helpTextFile:
                for line in helpTextFile.readlines():
                    self.helpText += line.strip()
        except FileNotFoundError:
            self.helpText = "Help Text file is missing!"

        self.updateUI()

    # @pyqtSlot()
    def updateUI(self):
        self.helpTextUI.setText(self.helpText)

        if not self.showHelpOnStartup:
            self.helpOnStartupUI.setCheckState(Qt.Checked)
        else:
            self.helpOnStartupUI.setCheckState(Qt.Unchecked)

    # @pyqtSlot()
    def helpOnStartupChanged(self):
        self.showHelpOnStartup = not self.helpOnStartupUI.isChecked()

    # @pyqtSlot()
    def okayClickedHandler(self):
        # write out all settings
        helpGroup = (('showHelpOnStartup', self.showHelpOnStartup),
                     )
        # Write settings values.
        for setting, variableName in helpGroup:
            self.appSettings.setValue(setting, variableName)
        self.close()

    # @pyqtSlot()
    def cancelClickedHandler(self):
        self.close()


if __name__ == "__main__":
    QCoreApplication.setOrganizationName("Fireheart Software")
    QCoreApplication.setOrganizationDomain("fireheartsoftware.com")
    QCoreApplication.setApplicationName("zipRenamer")
    appSettings = QSettings()
    if appSettings.contains('createLogFile'):
        createLogFile = appSettings.value('createLogFile')
    else:
        createLogFile = createLogFileDefault
        appSettings.setValue('createLogFile', createLogFile)

    if createLogFile:
        startingFolderName = path.dirname(path.realpath(__file__))
        if appSettings.contains('logFilename'):
            logFilename = appSettings.value('logFilename', type=str)
        else:
            logFilename = logFilenameDefault
            appSettings.setValue('logFilename', logFilename)
        basicConfig(filename=path.join(startingFolderName, logFilename), level=INFO,
                    format='%(asctime)s %(name)-8s %(levelname)-8s %(message)s')
    app = QApplication(argv)
    if platform.system() == "Darwin+":
        iconFilename = 'images/zipRenamer.icns'
    else:
        iconFilename = 'images/zipRenamer.ico'

    app.setWindowIcon(QIcon(os.path.join(baseDir, iconFilename)))
    ZipRenamerApp = ZipRenamer()
    ZipRenamerApp.updateUI()
    ZipRenamerApp.show()
    exit(app.exec_())
