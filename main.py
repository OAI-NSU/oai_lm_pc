import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush
import main_win
import lm_data
import time
import os
import data_vis
import can_unit
import pay_load
import cyclogram_result

version = "0.14.3"


class MainWindow(QtWidgets.QMainWindow, main_win.Ui_MainWindow):
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        # и т.д. в файле main_win.py
        #
        super().__init__()
        self.setupUi(self)  # Это нужно для инициализации нашего дизайна
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setWindowTitle("Norby - Linking Module. Version {:s}".format(version))
        # класс для управления устройством
        self.lm = lm_data.LMData( serial_numbers=
                                  ["0000ACF0", "205135995748", "205B359A", "2056359A",
                                   "2059359A", "365938753038", "365638633038", "365638633038",
                                   "206E359D5748"],
                                  debug=True, address=6)
        self.connectionPButt.clicked.connect(self.lm.usb_can.reconnect)
        # таб с кан-терминалом
        self.can_usb_client_widget = can_unit.ClientGUIWindow(self, interface=self.lm.usb_can)
        self.canTerminalVBLayout = QtWidgets.QVBoxLayout()
        self.canTerminalTab.setLayout(self.canTerminalVBLayout)
        self.canTerminalVBLayout.addWidget(self.can_usb_client_widget)
        # второе окно с графиками
        self.graph_window = data_vis.Widget()
        self.graph_window.restart_graph_signal.connect(self.restart_graph)
        self.openGraphPButton.clicked.connect(self.open_graph_window)
        # управление питанием МС
        self.pwrChsSetPButton.clicked.connect(self.pwr_set_channels_state)
        #
        self.get_general_data_inh = 0  # переменая для запрета опроса на момент других опросов
        self.genDataGetPButton.clicked.connect(self.get_general_data)
        self.cycleReadGenDataPButton.clicked.connect(self.cycle_get_general_data)
        self.genDataReadTimer = QtCore.QTimer()
        self.genDataReadTimer.timeout.connect(self.get_general_data)
        #
        self.allChannelsChBox.clicked.connect(self.pwr_all_channel_choice)
        self.pwr_channels_list = [self.lmChannelsChBox, self.plSOLChannelsChBox, self.pl11bChannelsChBox,
                                  self.pl12ChannelsChBox, self.pl20ChannelsChBox, self.dcr1ChannelsChBox,
                                  self.dcr2ChannelsChBox]
        # работ с ПН СОЛ
        self.plSOLRunCgPButton.clicked.connect(self.pl_sol_start_cg)
        self.plSOLStopCgPButton.clicked.connect(self.pl_sol_stop_cg)
        self.pl_sol_mem_rd_ptr = 0
        self.pl_sol_mem_rd_num = 0
        self.pl_sol_mem_data = []
        self.plSolReadFullMemPButt.clicked.connect(self.pl_sol_read_full_mem_start)
        self.plSolReadMemTimer = QtCore.QTimer()
        self.plSolReadMemTimer.timeout.connect(self.pl_sol_read_full_mem_process)
        # окно с результатом циклограммы
        self.cycl_result_win = cyclogram_result.Widget()
        # общие функции
        self.initLMPButton.clicked.connect(self.init_lm)
        self.synchLMTimePButton.clicked.connect(self.synch_lm_time)
        self.softResetPButton.clicked.connect(self.soft_reset)
        # работа с памятью
        self.memSetRDPointerPButt.clicked.connect(self.set_rd_pointer)
        self.memInitPButt.clicked.connect(self.init_mem_part)
        # обновление gui
        self.DataUpdateTimer = QtCore.QTimer()
        self.DataUpdateTimer.timeout.connect(self.update_ui)
        self.DataUpdateTimer.start(1000)
        # логи
        self.data_log_file = None
        self.data_log_file_title = None
        self.cycl_res_log_file = None
        self.pl_sol_mem_log_file = None
        self.log_str = ""

        self.logRestartPButt.clicked.connect(self.recreate_log_files)
        self.recreate_log_files()

        # UI #
    def update_ui(self):
        try:
            # отрисовка графика
            pass
            # логи
            if self.lm.get_log_file_title() is not None and self.data_log_file_title is None:
                self.data_log_file_title = self.lm.get_log_file_title()
                self.data_log_file.write(self.data_log_file_title)
            elif self.data_log_file_title:
                log_str_tmp = self.lm.get_log_file_data()
                if len(log_str_tmp) < 10:
                    pass
                elif self.log_str == log_str_tmp:
                    pass
                else:
                    self.log_str = log_str_tmp
                    self.data_log_file.write(self.log_str.replace(".", ","))
            # отображение состояния подключения
            self.statusLEdit.setText(self.lm.usb_can.state_string[self.lm.usb_can.state])
            # передача данных в графики
            self.graph_window.set_graph_data(self.lm.general_data)
        except Exception as error:
            print("update_ui: " + str(error))

    def open_graph_window(self):
        if self.graph_window.isVisible():
            self.graph_window.close()
        elif self.graph_window.isHidden():
            self.graph_window.show()
        pass

    # управление питанием
    def pwr_all_channel_choice(self):
        if self.allChannelsChBox.isChecked():
            for channel_ChBox in self.pwr_channels_list:
                channel_ChBox.setChecked(True)
        else:
            for channel_ChBox in self.pwr_channels_list:
                channel_ChBox.setChecked(False)
        pass

    def pwr_set_channels_state(self):
        channel_state = 0x00
        for num, channel_ChBox in enumerate(self.pwr_channels_list):
            if channel_ChBox.isChecked():
                channel_state |= 1 << num
        self.lm.send_cmd_reg(mode="lm_pn_pwr_switch", data=[channel_state & 0xFF])
        pass

    # constant mode
    def constant_mode_on(self):
        self.lm.send_cmd_reg(mode="const_mode", data=[0x01])
        pass

    def constant_mode_off(self):
        self.lm.send_cmd_reg(mode="const_mode", data=[0x00])
        pass

    # general data_read
    def get_general_data(self):
        if self.get_general_data_inh == 0:
            self.lm.read_tmi(mode="lm_full_tmi")
        pass

    def cycle_get_general_data(self):
        if self.genDataReadTimer.isActive():
            self.genDataReadTimer.stop()
        else:
            self.genDataReadTimer.start(1000)
        pass

    def restart_graph(self):
        self.lm.reset_general_data()
        pass

    # General function #
    def init_lm(self):
        self.lm.send_cmd(mode="lm_init")
        pass

    def synch_lm_time(self):
        time_s_from_2000 = time.mktime(time.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))
        time_tmp_s = int(time.time() - time_s_from_2000)
        self.lm.send_cmd_reg(mode="synch_time", data=self.get_list_from_int32_val(time_tmp_s))

    def soft_reset(self):
        self.lm.send_cmd_reg(mode="lm_soft_reset", data=[0xA5])
        pass

    # работа с памятью
    def set_rd_pointer(self):
        mem_num = self.memPartNumSBox.value()
        rd_ptr = self.memSetRDPointerSBox.value()
        data = [mem_num]
        data.extend(self.get_list_from_int32_val(rd_ptr))
        self.lm.send_cmd_reg(mode="mem_rd_ptr", data=data)
        pass

    def init_mem_part(self):
        mem_num = self.memPartNumSBox.value()
        data = [0xAA, mem_num]
        self.lm.send_cmd_reg(mode="mem_init", data=data)
        pass

    # pl sol
    def pl_sol_start_cg(self):
        num = self.plSOLCGNumSBox.value()
        self.lm.send_cmd_reg(mode="pl_sol_cg_start", data=[num & 0xFF])
        pass

    def pl_sol_stop_cg(self):
        self.lm.send_cmd_reg(mode="pl_sol_cg_stop", data=[0x00])
        pass

    def pl_sol_read_full_mem_start(self):
        self.pl_sol_mem_rd_num = 1002
        self.pl_sol_mem_rd_ptr = 0
        self.plSolReadMemTimer.start(400)
        self.pl_sol_mem_data = []
        #
        self.lm.read_mem(mode="pl_sol_mem")
        #
        self.plSolReadFullMemPBar.setValue(0)
        pass

    def pl_sol_read_full_mem_process(self):
        self.pl_sol_mem_data.append(self.lm.get_mem_data(1))
        if self.pl_sol_mem_rd_ptr < self.pl_sol_mem_rd_num:
            self.lm.read_mem(mode="pl_sol_mem")
        #
        self.plSolReadFullMemPBar.setValue(100*self.pl_sol_mem_rd_ptr/self.pl_sol_mem_rd_num)
        #
        if self.pl_sol_mem_rd_ptr < self.pl_sol_mem_rd_num:
            self.pl_sol_mem_rd_ptr += 1
        else:
            self.plSolReadMemTimer.stop()

            self.close_log_file(self.pl_sol_mem_log_file)
            self.pl_sol_mem_log_file = self.create_log_file(self.pl_sol_mem_log_file, sub_dir="PL_SOL_Mem", prefix="PL_SOL_Mem", extension=".txt")
            self.pl_sol_mem_log_file.write("".join(self.pl_sol_mem_data))
            return
        pass

    @staticmethod
    def get_list_from_int32_val(val):
        return [((val >> 0) & 0xff), ((val >> 8) & 0xff), ((val >> 16) & 0xff), ((val >> 24) & 0xff)]

    @staticmethod
    def get_u32_from_ledit(line_edit):
        str = line_edit.text()
        str_list = str.split(" ")
        str = "".join(str_list)
        u32val = 0x00000000
        try:
            u32val = int(str, 16)
        except ValueError:
            line_edit.setText("0000 0000")
        return u32val

    @staticmethod
    def get_u16_from_ledit(line_edit):
        str = line_edit.text()
        u16val = 0x0000
        try:
            u16val = int(str, 16)
        except ValueError:
            line_edit.setText("0000")
        return u16val

    @staticmethod
    def set_u32_to_ledit(line_edit, u32val):
        line_edit.setText("%04X %04X" % ((u32val >> 16) & 0xFFFF, (u32val >> 0) & 0xFFFF))
        return u32val

    @staticmethod
    def set_u16_to_ledit(line_edit, u16val):
        line_edit.setText("%04X" % (u16val & 0xFFFF))
        return u16val

    # LOGs #
    @staticmethod
    def create_log_file(file=None, sub_dir="Log", sub_sub_dir=True,  prefix="", extension=".csv"):
        dir_name = "Logs"
        sub_dir_name = dir_name + "\\" + time.strftime("%Y_%m_%d", time.localtime()) + " " + sub_dir
        if sub_sub_dir:
            sub_sub_dir_name = sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                               time.localtime()) + sub_dir
        else:
            sub_sub_dir_name = sub_dir_name
        try:
            os.makedirs(sub_sub_dir_name)
        except (OSError, AttributeError) as error:
            print(error)
            pass
        try:
            if file:
                file.close()
        except (OSError, NameError, AttributeError) as error:
            print(error)
            pass
        file_name = sub_sub_dir_name + "\\" + time.strftime("%Y_%m_%d %H-%M-%S ",
                                                            time.localtime()) + prefix + " " + extension
        file = open(file_name, 'a')
        return file

    def recreate_log_files(self):
        # перезапуск лог файла
        self.data_log_file_title = None
        self.data_log_file = self.create_log_file(file=self.data_log_file, sub_dir="Log", sub_sub_dir=True,
                                                  prefix="Norby_LM",
                                                  extension=".csv")
        pass

    @staticmethod
    def close_log_file(file=None):
        if file:
            try:
                file.close()
            except (OSError, NameError, AttributeError) as error:
                print(error)
            finally:
                file = None
        pass

    #
    def closeEvent(self, event):
        self.close_log_file(file=self.data_log_file)
        self.graph_window.close()
        self.close()
        pass


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    # QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # os.environ["QT_SCALE_FACTOR"] = "1.0"
    #
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainWindow()  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение
