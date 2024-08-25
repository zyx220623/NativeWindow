import win32api
import win32con
import win32gui
from ctypes import (Structure, POINTER, c_int, cast, windll)
from ctypes.wintypes import (POINT, HWND, UINT, RECT, MSG)
from PySide6.QtCore import (Qt, QSize, QTimer, QPoint)
from PySide6.QtGui import (QCursor, QCloseEvent, QIcon, QGuiApplication, QAction)
from PySide6.QtWidgets import (QApplication, QPushButton, QLabel, QMainWindow, QMenu)
from sys import exit as sys_exit
from sys import argv
class MINMAXINFO(Structure):
    _fields_ = [
        ("ptReserved", POINT),
        ("ptMaxSize", POINT),
        ("ptMaxPosition", POINT),
        ("ptMinTrackSize", POINT),
        ("ptMaxTrackSize", POINT),
    ]
class PWINDOWPOS(Structure):
    _fields_ = [
        ('hWnd',            HWND),
        ('hwndInsertAfter', HWND),
        ('x',               c_int),
        ('y',               c_int),
        ('cx',              c_int),
        ('cy',              c_int),
        ('flags', UINT)
    ]
class NCCALCSIZE_PARAMS(Structure):
    _fields_ = [
        ('rgrc', RECT*3),
        ('lppos', POINTER(PWINDOWPOS))
    ]



class NativeWindow(QMainWindow):
    BORDER_WIDTH = 5

    def __init__(self, *args, **kwargs):
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
        super(NativeWindow, self).__init__(*args, **kwargs)
        # 主屏幕的可用大小（去掉任务栏）
        self._rect = QGuiApplication.primaryScreen().availableGeometry()
        self.title_height = 30
        self.setWindowFlags(Qt.WindowType.Window |
                            Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowMinimizeButtonHint |
                            Qt.WindowType.WindowMaximizeButtonHint |
                            Qt.WindowType.WindowCloseButtonHint |
                            Qt.WindowType.WindowSystemMenuHint)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.__maxOrNormal2)
        self.timer.start(50)
        self.setStyleSheet("NativeWindow{background:rgb(255,255,255);}")
        self.__setWindowsBorder()
        self.__setWindowStatusMenu()

    def __setWindowsBorder(self):
        style = win32gui.GetWindowLong(int(self.winId()), win32con.GWL_STYLE)
        win32gui.SetWindowLong(int(self.winId()), win32con.GWL_STYLE,
                               style
                               | win32con.WS_THICKFRAME
                               | win32con.WS_MINIMIZEBOX
                               | win32con.WS_MAXIMIZEBOX
                               | win32con.WS_CAPTION
                               | win32con.CS_DBLCLKS)
       
    def setWindowTitle(self, title: str):
        super().setWindowTitle(title)
        self.titlebackground = QLabel(self)
        self.titlebackground.setStyleSheet("QLabel {"
                                           "background-color:rgba(30,30,30,1);"
                                           "}")
        self.titleBar = QLabel(f" {title}", self)
        self.titleBar.setStyleSheet("QLabel {"
                                    'font: normal normal 15px "微软雅黑";'
                                    "background-color:rgba(0,0,0,0);"
                                    "color:rgb(255,255,255)"
                                    "}")
        self.titlebackground.setGeometry(0,0,self.size().width(), self.title_height)
        self.titleBar.setGeometry(self.title_height, 0, self.size().width(), self.title_height)
        self.__raiseEvent()
        self.setMinimumHeight(self.title_height)
        self.__setthreebutton()

    def setWindowIcon(self, icon):
        super().setWindowIcon(icon)
        self.iconimage = QPushButton(self)
        self.iconimage.setIcon(icon)
        self.iconimage.setIconSize(QSize(self.title_height - 10, self.title_height - 10))
        self.iconimage.setFixedSize(self.title_height, self.title_height)
        self.iconimage.setStyleSheet("QPushButton {"
                                     "border:none;"
                                     "background-color:rgba(0,0,0,0);}")
        self.iconimage.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.iconimage.customContextMenuRequested.connect(self.__showWindowStatusMenuFromIcon)
        self.iconimage.move(0,0)
        self.__raiseEvent()

    def __setWindowStatusMenu(self):
        self.WindowStatusMenu = QMenu(self)
        self.WindowStatusMenu_qss = ("QMenu {"
                                     "background-color:rgb(40, 40, 40);"
                                     "color:rgb(255, 255, 255);"
                                     "border: 1px solid rgb(127, 127, 127);"
                                     "}"
                                     "QMenu:item:selected {"
                                     "background-color:rgb(80, 80, 80);"
                                     "}"
                                     "QMenu:separator{"
                                     "height:1px;"
                                     "background-color:rgba(123,123,123,1);"
                                     "margin-left:22px;"
                                     "margin-right:1px;"
                                     "}"
                                     "QMenu:item:disabled {"
                                     "color:rgb(100,100,100);"
                                     "background-color:rgb(40, 40, 40);"
                                     "}")
        self.WindowStatusMenu.setStyleSheet(self.WindowStatusMenu_qss)
        self.NormalAction = QAction("还原(&R)", self)
        self.NormalAction.setEnabled(False)
        self.NormalAction.triggered.connect(self.showNormal)
        self.NormalAction.setIcon(QIcon("normalborder.png"))
        self.WindowStatusMenu.addAction(self.NormalAction)
        self.MoveAction = QAction("移动(&M)", self)
        self.WindowStatusMenu.addAction(self.MoveAction)
        self.SizeAction = QAction("大小(&S)", self)
        self.WindowStatusMenu.addAction(self.SizeAction)
        self.MinAction = QAction("最小化(&N)", self)
        self.MinAction.setIcon(QIcon("minborder.png"))
        self.MinAction.triggered.connect(self.showMinimized)
        self.WindowStatusMenu.addAction(self.MinAction)
        self.MaxAction = QAction("最大化(&X)", self)
        self.MaxAction.triggered.connect(self.showMaximized)
        self.MaxAction.setIcon(QIcon("maxborder.png"))
        self.WindowStatusMenu.addAction(self.MaxAction)
        self.WindowStatusMenu.addSeparator()
        self.CloseAction = QAction("关闭(&C)", self)
        self.CloseAction.setShortcut("Alt+F4")
        self.CloseAction.setIcon(QIcon("closeborder.png"))
        self.CloseAction.triggered.connect(self.close)
        self.WindowStatusMenu.addAction(self.CloseAction)

    def __setWindowStatusMenuOnMax(self):
        self.WindowStatusMenu = QMenu(self)
        self.WindowStatusMenu.setStyleSheet(self.WindowStatusMenu_qss)
        self.NormalAction = QAction("还原(&R)", self)
        self.NormalAction.triggered.connect(self.showNormal)
        self.NormalAction.setIcon(QIcon("normalborder.png"))
        self.WindowStatusMenu.addAction(self.NormalAction)
        self.MoveAction = QAction("移动(&M)", self)
        self.MoveAction.setEnabled(False)
        self.WindowStatusMenu.addAction(self.MoveAction)
        self.SizeAction = QAction("大小(&S)", self)
        self.SizeAction.setEnabled(False)
        self.WindowStatusMenu.addAction(self.SizeAction)
        self.MinAction = QAction("最小化(&N)", self)
        self.MinAction.setIcon(QIcon("minborder.png"))
        self.MinAction.triggered.connect(self.showMinimized)
        self.WindowStatusMenu.addAction(self.MinAction)
        self.MaxAction = QAction("最大化(&X)", self)
        self.MaxAction.setEnabled(False)
        self.MaxAction.triggered.connect(self.showMaximized)
        self.MaxAction.setIcon(QIcon("maxborder.png"))
        self.WindowStatusMenu.addAction(self.MaxAction)
        self.WindowStatusMenu.addSeparator()
        self.CloseAction = QAction("关闭(&C)", self)
        self.CloseAction.setShortcut("Alt+F4")
        self.CloseAction.setIcon(QIcon("closeborder.png"))
        self.CloseAction.triggered.connect(self.close)
        self.WindowStatusMenu.addAction(self.CloseAction)

    def __showWindowStatusMenuFromIcon(self):
        if not self.isMaximized():
            self.__setWindowStatusMenu()
            self.WindowStatusMenu.exec(QPoint(self.pos().x(),self.title_height + self.pos().y()))
        else:
            self.__setWindowStatusMenuOnMax()
            self.WindowStatusMenu.exec(QPoint(self.pos().x(), self.title_height + self.pos().y() + 8))

    def __setthreebutton(self):
        clqss = ("QPushButton {"
               "background-color:rgba(0,0,0,0);"
               "border:none;"
               "}"
               "QPushButton:hover {"
               "background-color:rgba(255,0,0,1);"
               "}"
               "QPushButton:pressed {"
               "background-color:rgba(255,100,100,1);"
               "}"
               )
        blqss = ("QPushButton {"
                 "background-color:rgba(0,0,0,0);"
                 "border:none;"
                 "}"
                 "QPushButton:hover {"
                 "background-color:rgba(60,60,60,1);"
                 "}"
                 "QPushButton:pressed {"
                 "background-color:rgba(100,100,100,1);"
                 "}"
                 )
        psize = QSize(self.title_height + 10, self.title_height)
        isize = QSize(self.title_height - 17, self.title_height - 17)
        self.exitbutton = QPushButton(self)
        self.exitbutton.setIcon(QIcon("close.png"))
        self.exitbutton.setIconSize(isize)
        self.exitbutton.resize(psize)
        self.exitbutton.setStyleSheet(clqss)
        self.exitbutton.setToolTip("关闭")
        self.exitbutton.clicked.connect(self.close)
        self.maxbutton = QPushButton(self)
        self.maxbutton.setIcon(QIcon("max.png"))
        self.maxbutton.setToolTip("最大化")
        self.maxbutton.setIconSize(isize)
        self.maxbutton.resize(psize)
        self.maxbutton.setStyleSheet(blqss)
        self.maxbutton.clicked.connect(self.__maxOrNormal)
        self.minbutton = QPushButton(self)
        self.minbutton.setIcon(QIcon("min.png"))
        self.minbutton.setToolTip("最小化")
        self.minbutton.setIconSize(isize)
        self.minbutton.resize(psize)
        self.minbutton.setStyleSheet(blqss)
        self.minbutton.clicked.connect(self.showMinimized)

    def showNormal(self):
        super().showNormal()
        self.maxbutton.setIcon(QIcon("max.png"))
        self.maxbutton.setToolTip("最大化")
        QCursor.setPos(QCursor.pos().x(), QCursor.pos().y() - 1)

    def showMaximized(self):
        super().showMaximized()
        self.maxbutton.setIcon(QIcon("normal.png"))
        self.maxbutton.setToolTip("向下还原")
        QCursor.setPos(QCursor.pos().x(), QCursor.pos().y() - 1)

    def __maxOrNormal(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def __maxOrNormal2(self):
        if self.isMaximized():
            self.maxbutton.setIcon(QIcon("normal.png"))
            self.maxbutton.setToolTip("向下还原")
        else:
            self.maxbutton.setIcon(QIcon("max.png"))
            self.maxbutton.setToolTip("最大化")

    def __raiseEvent(self):
        try:
            self.titlebackground.raise_()
            self.titleBar.raise_()
            self.exitbutton.raise_()
            self.maxbutton.raise_()
            self.minbutton.raise_()
        except:
            pass
        try:
            self.iconimage.raise_()
        except:
            pass

    def resizeEvent(self, a0):
        self.__resizeEvent__()

    def __resizeEvent__(self):
        try:
            self.titlebackground.setGeometry(0, 0, self.size().width(), self.title_height)
            self.titleBar.setGeometry(self.title_height, 0, self.size().width(), self.title_height)
            self.exitbutton.move(self.size().width() - self.exitbutton.size().width(), 0)
            self.maxbutton.move(self.exitbutton.pos().x() - self.maxbutton.size().width(), 0)
            self.minbutton.move(self.maxbutton.pos().x() - self.minbutton.size().width(), 0)
        except:
            pass

    def __isWindowMaximized(self, hWnd) -> bool:
        """ 判断窗口是否最大化 """
        # 返回指定窗口的显示状态以及被恢复的、最大化的和最小化的窗口位置，返回值为元组
        windowPlacement = win32gui.GetWindowPlacement(hWnd)
        if not windowPlacement:
            return False
        return windowPlacement[1] == win32con.SW_MAXIMIZE

    def nativeEvent(self, eventType, message):
        """ 处理windows消息 """
        msg = MSG.from_address(message.__int__())
        pos = QCursor.pos()
        x = pos.x() - self.frameGeometry().x()
        y = pos.y() - self.frameGeometry().y()
        if msg.message == win32con.WM_NCHITTEST:
            xPos = win32api.LOWORD(msg.lParam) - self.frameGeometry().x()
            yPos = win32api.HIWORD(msg.lParam) - self.frameGeometry().y()
            w, h = self.width(), self.height()
            lx = xPos < self.BORDER_WIDTH
            rx = xPos + 9 > w - self.BORDER_WIDTH
            ty = yPos < self.BORDER_WIDTH
            by = yPos > h - self.BORDER_WIDTH
            if lx and ty and not self.isMaximized():
                return True, win32con.HTTOPLEFT
            elif rx and by and not self.isMaximized():
                return True, win32con.HTBOTTOMRIGHT
            elif rx and ty and not self.isMaximized():
                return True, win32con.HTTOPRIGHT
            elif lx and by and not self.isMaximized():
                return True, win32con.HTBOTTOMLEFT
            elif ty and not self.isMaximized():
                return True, win32con.HTTOP
            elif by and not self.isMaximized():
                return True, win32con.HTBOTTOM
            elif lx and not self.isMaximized():
                return True, win32con.HTLEFT
            elif rx and not self.isMaximized():
                return True, win32con.HTRIGHT
            elif self.pos().y() <= QCursor.pos().y() <= self.pos().y() + self.title_height and self.childAt(x,y) == self.titleBar:
                return True, win32con.HTCAPTION
        elif msg.message == win32con.WM_NCCALCSIZE:
            if self.__isWindowMaximized(msg.hWnd):
                self.__monitorNCCALCSIZE(msg)
            return True, 0
        elif msg.message == win32con.WM_GETMINMAXINFO:
            if self.__isWindowMaximized(msg.hWnd):
                window_rect = win32gui.GetWindowRect(msg.hWnd)
                if not window_rect:
                    return False, 0
                # 获取显示器句柄
                monitor = win32api.MonitorFromRect(window_rect)
                if not monitor:
                    return False, 0
                # 获取显示器信息
                work_area = (self._rect.x(), self._rect.y(), self._rect.width() + 5, self._rect.height())
                # 将lParam转换为MINMAXINFO指针
                info = cast(msg.lParam, POINTER(MINMAXINFO)).contents
                # 调整窗口大小
                info.ptMaxSize.x = work_area[2]
                info.ptMaxSize.y = work_area[3]
                info.ptMaxTrackSize.x = info.ptMaxSize.x
                info.ptMaxTrackSize.y = info.ptMaxSize.y
                # 修改左上角坐标
                info.ptMaxPosition.x = 0
                info.ptMaxPosition.y = 0
                return True, 1
        elif msg.message == win32con.WM_SYSKEYDOWN:
            if msg.wParam == win32con.VK_F4:
                QApplication.sendEvent(self, QCloseEvent())
                return False, 0
        return QMainWindow.nativeEvent(self, eventType, message)

    def __monitorNCCALCSIZE(self, msg: MSG):
        """ 处理 WM_NCCALCSIZE 消息 """
        monitor = win32api.MonitorFromWindow(msg.hWnd)
        # 如果没有保存显示器信息就直接返回，否则接着调整窗口大小
        if monitor is None and not self.monitor_info:
            return
        elif monitor is not None:
            self.monitor_info = win32api.GetMonitorInfo(monitor)
        # 调整窗口大小
        params = cast(msg.lParam, POINTER(NCCALCSIZE_PARAMS)).contents
        params.rgrc[0].left = self.monitor_info['Work'][0]
        params.rgrc[0].top = self.monitor_info['Work'][1]
        params.rgrc[0].right = self.monitor_info['Work'][2]
        params.rgrc[0].bottom = self.monitor_info['Work'][3]


if __name__ == '__main__':
    app = QApplication(argv)
    w = NativeWindow()
    w.setWindowTitle("NativeWindow 示例")
    w.setWindowIcon(QIcon("icon.png"))
    w.setMinimumWidth(450)
    w.resize(800,450)
    w.show()
    sys_exit(app.exec())
