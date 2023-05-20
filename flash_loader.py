import lm_data
import time
import crc16
import copy
import random
import norby_data


class FlashLoader():
    def __init__(self, lm_data):
        self.lm = lm_data
        self.wr_file_info = {"path": "", "size": 0, "block_num": 0, "block_tail": 0}
        self.rd_file_info = {"path": "", "size": 0, "block_num": 0, "block_tail": 0}
        self.status = {"Status": "", "CurrentBlock": "", "PrefBlock": "", "ResetSrc": "", "Others": ""}
        self.ctrl = {"size": 0x000000, "cmd": 0x00, "crc": 0x00}

    def read_status(self):
        self.lm.read_flash_ctrl()
        self.lm.wait_busy()
        time.sleep(1.0)
        status_list = lm.flash_data["ctrl_reg"]
        if status_list:
            self.status["Status"] = f"0x{status_list[0]:02X}"
            self.status["CurrentBlock"] = f"0x{status_list[1]:02X}"
            self.status["PrefBlock"] = f"0x{status_list[2]:02X}"
            self.status["ResetSrc"] = f"0x{status_list[3]:02X}"
            self.status["Others"] = f"0x{self.list_to_hex(status_list[4:])}"
        return self.status

    def check_file_setup(self, bin_file_path):
        with open(bin_file_path, mode='rb') as file:  # b is important -> binary
            file_content = file.read()
        u32_file_content = []
        for i in range(len(file_content)//4):
            u32_file_content.append((int.from_bytes(file_content[i*4:(i+1)*4], byteorder="little") + 1) & 0xFFFFFFFF)  # +1 из-за особенностей алгоритма АА
        f_crc = crc16.CalcCRC32(0xFFFFFFFF, u32_file_content)
        setup = 4*int.from_bytes(file_content[-4:], byteorder="little")
        f_size = len(file_content)
        return f_crc, f_size

    def write_bin(self, bin_file_path):
        with open(bin_file_path, mode='rb') as file:  # b is important -> binary
            file_content = file.read()
        self.wr_file_info["path"] = bin_file_path
        self.wr_file_info["size"] = len(file_content)
        self.wr_file_info["block_num"] = len(file_content)//128
        self.wr_file_info["block_tail"] = len(file_content) % 128
        for block_num in range(self.wr_file_info["block_num"]):
            self.lm.write_flash_sw(offset=block_num*128, data=file_content[block_num*128:(block_num+1)*128])
            print(f"\rwr: {block_num} from {self.wr_file_info['block_num']}", end="")
            fl.lm.wait_busy()
            time.sleep(0.01)
        self.lm.write_flash_sw(offset=self.wr_file_info["block_num"] * 128,
                               data=file_content[
                                    (self.wr_file_info["block_num"] * 128):(self.wr_file_info["block_num"] * 128 +
                                                                         self.wr_file_info["block_tail"])])
        fl.lm.wait_busy()
        print(f"\r{self.wr_file_info['block_num']} from {self.wr_file_info['block_num']}")
        print(f"WR: head:", self.list_to_hex(file_content[:10]), f"tail:", self.list_to_hex(file_content[-10:]))

    def check_bin(self, bin_file_path):
        """
        Проверка записанного bin-файла
        :param self:
        :param bin_file_path:
        :return:
        """
        with open(bin_file_path, mode='rb') as file:  # b is important -> binary
            wr_file_content = file.read()
        self.rd_file_info["path"] = bin_file_path
        self.rd_file_info["size"] = len(wr_file_content)
        self.rd_file_info["block_num"] = len(wr_file_content) // 128
        self.rd_file_info["block_tail"] = len(wr_file_content) % 128
        self.lm.reset_flash_sw_data()
        for block_num in range(self.rd_file_info["block_num"]):
            self.lm.read_flash_sw(offset=block_num * 128)
            print(f"\rrd: {block_num} from {self.rd_file_info['block_num']}", end="")
            fl.lm.wait_busy()
        self.lm.read_flash_sw(offset=self.rd_file_info["block_num"] * 128)
        fl.lm.wait_busy()
        time.sleep(0.01)
        print(f"\r{self.rd_file_info['block_num']} from {self.rd_file_info['block_num']}")
        self.lm.flash_data['rd'] = self.lm.flash_data['rd'][:self.rd_file_info["size"]]
        print(f"RD: head:", self.list_to_hex(self.lm.flash_data['rd'][:10]), f"tail:",
              self.list_to_hex(self.lm.flash_data['rd'][-10:]))
        with open(bin_file_path.split(".")[0]+"_rd.bin", mode='wb') as file:  # b is important -> binary
            file.write(bytearray(self.lm.flash_data['rd']))

    def form_and_send_ctrl_data(self):
        ctrl_data = b""
        ctrl_data += self.ctrl["size"].to_bytes(3, byteorder="little")
        ctrl_data += self.ctrl["cmd"].to_bytes(1, byteorder="little")
        ctrl_data += self.ctrl["crc"].to_bytes(4, byteorder="little")
        # print(self.list_to_hex(ctrl_data))
        lm.write_flash_ctrl(data=list(ctrl_data))

    def restart(self):
        self.ctrl["size"] = 0x000000
        self.ctrl["cmd"] = 0x0E
        self.ctrl["crc"] = 0x00000000
        self.form_and_send_ctrl_data()
        pass

    def check_crc(self, part=0, f_crc=0, f_size=0):
        self.ctrl["size"] = f_size
        self.ctrl["cmd"] = 0x04 + (part & 0x01)
        self.ctrl["crc"] = f_crc
        self.form_and_send_ctrl_data()
        pass

    def set_pref_block(self, part=0):
        self.ctrl["size"] = 0x00
        self.ctrl["cmd"] = 0x0A + (part & 0x01)
        self.ctrl["crc"] = 0x00
        self.form_and_send_ctrl_data()
        pass

    def erase(self):
        self.ctrl["size"] = 0x00
        self.ctrl["cmd"] = 0x02
        self.ctrl["crc"] = 0x00
        self.form_and_send_ctrl_data()
        pass

    def __repr__(self):
        ret_str = f"Flash loader module: usb-can open - {lm.usb_can.is_open}"
        return ret_str

    @staticmethod
    def list_to_hex(data):
        return [f"{var:02X}" for var in data]


def get_time():
    return time.strftime("%H-%M-%S", time.localtime()) + "." + ("%.3f:" % time.perf_counter()).split(".")[1]


sw_path_p1 = "bin\\oai_lm_mcu_v2_10_0.bin"
sw_path_p2 = "bin\\oai_lm_mcu_v2_10_1.bin"


if __name__ == "__main__":
    start = time.perf_counter()
    print(get_time(), f"Script start")
    # класс для управления устройством
    lm = lm_data.LMData(serial_numbers=["0000ACF0", "205135995748", "205B359A", "2056359A",
                        "2059359A", "365938753038", "365638633038", "365638633038", "206E359D5748"],
                        address=6, debug=False)
    lm.usb_can.reconnect()
    fl = FlashLoader(lm)
    print(get_time(), fl)
    #
    # проверка работы CAN
    lm.read_tmi(mode="lm_full_tmi")
    time.sleep(1)
    print(lm.get_time(), "Used_part", lm.tmi_dict.get("LM:status", "Read error"))
    #
    lm.read_tmi(mode="lm_load_param")
    time.sleep(1)
    print(lm.get_time(), "sw_version:", lm.load_parameters_data.get("Версия", "Read error"))
    #
    print(fl.read_status())
    #
    f_crc, f_size = fl.check_file_setup(sw_path_p1)
    print(f'crc=0x{f_crc:08X}, size={f_size}')
    fl.check_crc(part=0, f_crc=f_crc, f_size=f_size)
    fl.lm.wait_busy()
    print(fl.read_status())
    #
    f_crc, f_size = fl.check_file_setup(sw_path_p2)
    print(f'crc=0x{f_crc:08X}, size={f_size}')
    fl.check_crc(part=1, f_crc=f_crc, f_size=f_size)
    fl.lm.wait_busy()
    print(fl.read_status())
    #
    fl.set_pref_block(part=0)
    fl.lm.wait_busy()
    time.sleep(1)
    print(fl.read_status())
    # #
    # fl.erase()
    # fl.lm.wait_busy()
    # time.sleep(2)
    # #
    if False:
        # #
        fl.erase()
        fl.lm.wait_busy()
        time.sleep(2)
        print(fl.read_status())
        # тестирование записи/чтения прошивки
        fl.write_bin(sw_path_p1)
        print("file_info", fl.wr_file_info)
        fl.check_bin(sw_path_p1)
        #
        f_crc, f_size = fl.check_file_setup(sw_path_p1)
        print(f'crc=0x{f_crc:08X}, size={f_size}')
        fl.check_crc(part=0, f_crc=f_crc, f_size=f_size)
        fl.lm.wait_busy()
        time.sleep(1)
        print("Part0 crc ", fl.read_status())
        #
        f_crc, f_size = fl.check_file_setup(sw_path_p2)
        print(f'crc=0x{f_crc:08X}, size={f_size}')
        fl.check_crc(part=1, f_crc=f_crc, f_size=f_size)
        fl.lm.wait_busy()
        time.sleep(1)
        print("Part1 crc", fl.read_status())
        # #
        #
        fl.set_pref_block(part=0)
        fl.lm.wait_busy()
        time.sleep(1)
        print(fl.read_status())
        #
        fl.restart()
        fl.lm.wait_busy()
        #
    stop = time.perf_counter()
    print(get_time(), f"Script finish: run time is {(stop-start):.3f}")

