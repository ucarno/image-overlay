import json
import sys

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QSlider, QLabel, QFrame
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QPainter


DEFAULT_OPACITY = 0.8
_config = None


class Config:
    config = None

    @classmethod
    def load(cls):
        if cls.config:
            return

        try:
            cls.config = json.loads(open('config.json', 'r', encoding='utf-8').read())
        except FileNotFoundError:
            cls.config = {'opacity': DEFAULT_OPACITY}

    @classmethod
    def save(cls):
        cls.load()
        with open('config.json', 'w+', encoding='utf-8') as f:
            f.write(json.dumps(cls.config))
            f.close()

    @classmethod
    def get_opacity(cls):
        return cls.config['opacity']

    @classmethod
    def set_opacity(cls, value):
        cls.config['opacity'] = value


class ExitOnClose:
    def closeEvent(self, event):
        Config.save()
        exit()


class QHLine(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Raised)


class MainWindow(QWidget, ExitOnClose):
    def __init__(self):
        super().__init__()
        self.setFixedSize(300, 100)
        self.setWindowTitle('ImageOverlay')

        self.is_sticked = False

        self.stick_button = QPushButton()
        self.stick_button.setText('Click to stick')
        self.stick_button.clicked.connect(self.on_stick_button_click)

        self.slider_label = QLabel('Opacity')
        self.opacity_slider = QSlider(orientation=Qt.Orientation.Horizontal)
        self.opacity_slider.setSingleStep(1)
        self.opacity_slider.setMaximum(95)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setSliderPosition(int(Config.get_opacity() * 100))
        self.opacity_slider.sliderMoved.connect(self.on_opacity_slider_move)

        self.image_window = ImageWindow()
        self.image_window.setWindowOpacity(Config.get_opacity())

        self.image_window.show()

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.stick_button)
        self.main_layout.addWidget(QHLine())
        self.main_layout.addWidget(self.slider_label)
        self.main_layout.addWidget(self.opacity_slider)

        self.setLayout(self.main_layout)

    def on_stick_button_click(self):
        if self.is_sticked:
            self.is_sticked = False
            self.image_window.unstick()
            self.stick_button.setText('Click to stick')
        else:
            if self.image_window.pixmap:
                self.is_sticked = True
                self.image_window.stick()
                self.stick_button.setText('Click to unstick')
            else:
                self.stick_button.setText('There is nothing to stick!')
                return

    def on_opacity_slider_move(self, value):
        opacity = value / 100
        self.image_window.setWindowOpacity(opacity)
        Config.set_opacity(opacity)


class ImageWindow(QWidget, ExitOnClose):
    pixmap = None
    _sizeHint = QSize()

    def __init__(self):
        super().__init__()
        self.resize(400, 400)
        self.setAcceptDrops(True)
        self.setWindowTitle('Image Window')

        self.scaled = None

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)

    def stick(self):
        self.hide()
        self.move(
            self.pos().x() + round((self.width() - self.scaled.width()) / 2) + 1,
            self.pos().y() + round((self.height() - self.scaled.height()) / 2) + 31
        )

        self.resize(self.scaled.width(), self.scaled.height())

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=True)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowTransparentForInput
        )
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, on=True)
        self.show()

    def unstick(self):
        self.hide()
        pos = self.pos()
        self.move(pos.x()-1, pos.y()-31)

        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, on=False)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, on=False)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.FramelessWindowHint
            & ~Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowTransparentForInput
        )
        self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasImage:
            event.setDropAction(Qt.DropAction.CopyAction)
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.setPixmap(QPixmap(file_path))
            event.accept()
        else:
            event.ignore()

    def setPixmap(self, pixmap):
        if self.pixmap != pixmap:
            self.pixmap = pixmap
            if isinstance(pixmap, QPixmap):
                self._sizeHint = pixmap.size()
            else:
                self._sizeHint = QSize()
            self.updateGeometry()
            self.updateScaled()

    def updateScaled(self):
        if self.pixmap:
            self.scaled = self.pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        self.update()

    def sizeHint(self):
        return self._sizeHint

    def resizeEvent(self, event):
        self.updateScaled()

    def paintEvent(self, event):
        if not self.pixmap:
            return
        qp = QPainter(self)
        r = self.scaled.rect()
        r.moveCenter(self.rect().center())
        qp.drawPixmap(r, self.scaled)


if __name__ == '__main__':
    Config.load()

    app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.show()

    sys.exit(app.exec())
