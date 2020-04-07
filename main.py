from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import *
from PyQt5 import QtWidgets, uic
from functools import partial
from dxf2svg.pycore import save_svg_from_dxf, extract_all
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from shutil import copyfile
from PIL import Image
import sys, os, json, cv2, time, threading

Data_JSON = "data.json"
Data_JSON_Contents = []

file_names = []
image_locations = []

class mainwindowUI(QMainWindow):
    def __init__(self, parent = None):
        super(mainwindowUI, self).__init__(parent)
        uic.loadUi('MainWindow.ui', self)
        self.setStyleSheet(open("style.qss", "r").read())

        self.progressbar = self.findChild(QProgressBar,'progressBar')
        self.progressbar.setHidden(True)
        self.lblState = self.findChild(QLabel,'lblState')
        
        self.gridLayoutItems = self.findChild(QGridLayout, 'gridLayoutItems')
        
        self.btnAdd = self.findChild(QPushButton, 'btnAdd')
        self.btnAdd.clicked.connect(self.add)
        self.clearLayout(self.gridLayoutItems)
        self.hideProgress(True)
        self.reloadListUI()
        self.show()
    def hideProgress(self, b):
        self.lblState.setHidden(b)
        # self.progressbar.setHidden(b)
    def add(self):
        # open file directory
        files, _ = QFileDialog.getOpenFileNames(self,"Add Files", "","DXF Files (*.dxf)")
        if files:
            self.addFiles(files)
            # threading.Thread(target=self.addFiles,args=(files,)).start()
    def addFiles(self,files):
        # self.progressBar.setMaxinum(i+1)
        for i, j in enumerate(files):
            # self.progressbar.setMaximum(len(files)+1)
            self.hideProgress(False)
            # Generate file name
            temp_fileName = j.split("/")
            temp_fileName = temp_fileName[-1]
            temp_fileName = temp_fileName.split(".")
            temp_fileName = temp_fileName[0]
            
            # Generate final file location for the image
            imgLoc = j.split("/")
            imgLoc.pop(-1)
            imgLoc = '/'.join(imgLoc)
            imgLoc = imgLoc + '/Images/' + temp_fileName + '.png'
            
            # Check if file already exists
            for o, k in enumerate(image_locations):
                if k == imgLoc:
                    buttonReply = QMessageBox.critical(self, 'File already exists', f"{temp_fileName}.DXF already exists!\n\nWould you like to overwrite {temp_fileName}?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
                    if buttonReply == QMessageBox.No: return
                    elif buttonReply == QMessageBox.Cancel: return
                    elif buttonReply == QMessageBox.Yes:
                        if os.path.exists(k): os.remove(k)
                        Data_JSON_Contents.pop(o)

            dxffilepath = j
            
            self.lblState.setText("Getting dimensions.")
            os.popen(f'dia \"{j}\" -e properties.png')
            time.sleep(2)
            while os.path.exists("properties.png"):
                # time.sleep(1)
                # Get data from DXF FILE
                im = cv2.imread('properties.png')
                h, w, c = im.shape
                print('width:  ', w)
                print('height: ', h)
                w = w + 100
                h = h + 100
                if w > h: s = w
                else: s = h
                
                # convert DXF file to PNG
                self.lblState.setText("Extracting DXF..")
                copyfile(dxffilepath, "clone.DXF")
                extract_all('clone.DXF', size=s/20)
                drawing = svg2rlg('clone.DXF')
                self.lblState.setText("Converting DXF...")
                renderPM.drawToFile(drawing, f"Images/{temp_fileName}.png", fmt="PNG")
                
                self.lblState.setText("Finalizing image....")
                # Make image black and white
                originalImage = cv2.imread(imgLoc)
                originalImage = cv2.resize(originalImage, (int(w/2), int(h/2)))
                # originalImage = cv2.GaussianBlur(originalImage,(3,1),0)
                
                
                (thresh, blackAndWhiteImage) = cv2.threshold(originalImage, 250, 255, cv2.THRESH_BINARY)
                cv2.imwrite(f"{imgLoc}", blackAndWhiteImage)
                
                top, bottom, left, right = 50, 50, 50 ,50
                color = (255, 255, 255)
                # add margin
                im = Image.open(imgLoc)
                width, height = im.size
                new_width = width + right + left
                new_height = height + top + bottom
                result = Image.new(im.mode, (new_width, new_height), color)
                result.paste(im, (left, top))
                result.save(imgLoc, quality=95)
                
                top, bottom, left, right = int(50/5),  int(50/5), int(50/5), int(50/5)
                color = (0, 0, 0)
                im = Image.open(imgLoc)
                width, height = im.size
                new_width = width + right + left
                new_height = height + top + bottom
                result = Image.new(im.mode, (new_width, new_height), color)
                result.paste(im, (left, top))
                result.save(imgLoc, quality=95)
                
                self.lblState.setText("Saving.....")
                Data_JSON_Contents.append({
                'fileName': [temp_fileName],
                'imgLoc': [imgLoc]
                })
                # save data to JSON file
                sortedList = sorted(Data_JSON_Contents, key = lambda i: i['fileName'])
                with open(Data_JSON, mode='w+', encoding='utf-8') as file: json.dump(sortedList, file, ensure_ascii=True, indent=4, sort_keys=True)
                os.remove('properties.png')
                os.remove('clone.DXF')
                # self.progressBar.setValue(i+1)
            
            # Reload GUI
            print('finished.')
            self.lblState.setText("Finished!")
            self.clearLayout(self.gridLayoutItems)
            self.reloadListUI()
            time.sleep(1)
            self.hideProgress(True)
            
    def openImage(self, path):
        self.vi = view_image(path)
        self.vi.show()
        
    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: widget.deleteLater()
                else: self.clearLayout(item.layout())

    def reloadListUI(self):
        load_data_file(file_names, image_locations)
        label = QLabel("Name:")
        self.gridLayoutItems.addWidget(label, 0, 0)
        label = QLabel("Quantity:")
        self.gridLayoutItems.addWidget(label, 0, 1)
        label = QLabel("Thumbnail:")
        self.gridLayoutItems.addWidget(label, 0, 2)
        for i, j in enumerate(file_names):
            
            label = QLabel(j)
            # label.setFixedSize(128,20)
            self.gridLayoutItems.addWidget(label, i+1, 0)
            
            textBoxInput = QLineEdit("1")
            # textBoxInput.setFixedSize(64,20)
            self.gridLayoutItems.addWidget(textBoxInput, i+1, 1)
            
            btnImage = QPushButton()
            btnImage.clicked.connect(partial(self.openImage, image_locations[i]))
            btnImage.setIcon(QIcon(image_locations[i]))
            btnImage.setIconSize(QSize(64,64))
            # btnImage.setFixedSize(64,64)
            btnImage.setFlat(True)
            self.gridLayoutItems.addWidget(btnImage, i+1, 2)
        # self.gridLayoutItems.setColumnStretch(3,0)

class view_image(QtWidgets.QWidget):
    def __init__(self, directory_to_open):
        super(view_image, self).__init__()
        self.image_to_open = directory_to_open
        directory_to_open = directory_to_open.replace('\\','/')
        self.setWindowTitle(directory_to_open)
        self.viewer = PhotoViewer(self)
        # self.resize(width, height)
        screen = app.primaryScreen()
        rect = screen.availableGeometry()
        self.setGeometry(0, 0, rect.width(), rect.height())
        self.viewer.photoClicked.connect(self.photoClicked)
        # Arrange layout
        VBlayout = QVBoxLayout(self)
        VBlayout.addWidget(self.viewer)
        HBlayout = QHBoxLayout()
        HBlayout.setAlignment(Qt.AlignLeft)
        VBlayout.addLayout(HBlayout)
        self.loadImage()
    def loadImage(self):
        self.viewer.setPhoto(QPixmap(self.image_to_open))
        self.showMaximized()
    def pixInfo(self):
        self.viewer.toggleDragMode()
    def photoClicked(self, pos):
        if self.viewer.dragMode()  == QGraphicsView.NoDrag:
            self.editPixInfo.setText('%d, %d' % (pos.x(), pos.y()))
class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = pyqtSignal(QPoint)
    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self._zoom = 100
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)
    def hasPhoto(self):
        return not self._empty
    def fitInView(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0
    def setPhoto(self, pixmap=None):
        self._zoom = 100
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())
        self.fitInView()
    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0
    def toggleDragMode(self):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setDragMode(QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.ScrollHandDrag)
    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        super(PhotoViewer, self).mousePressEvent(event)
def load_data_file(*args):
    global Data_JSON_Contents
    for i, j in enumerate(args):
        j.clear()
    with open(Data_JSON) as file:
        Data_JSON_Contents = json.load(file)
        # for name in Data_JSON_Contents[0]['fileName']: args[0].append(name)
        # for imgLoc in Data_JSON_Contents[0]['imgLoc']: args[1].append(imgLoc)
        for info in Data_JSON_Contents:
            for name in info['fileName']: file_names.append(name)
            for path in info['imgLoc']: image_locations.append(path)
                
if __name__ == '__main__':
    if not os.path.exists('Images'): os.makedirs('Images')
    file_exists = os.path.isfile(Data_JSON)
    if file_exists:
        load_data_file(file_names, image_locations)
    else:
        f = open(Data_JSON, "w+")
        f.write("[]")
    app = QApplication(sys.argv)
    window = mainwindowUI()
    app.exec_()
