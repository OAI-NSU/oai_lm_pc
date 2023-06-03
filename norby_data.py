
#    модуль собирающий в себе стандартизованные функции разбора данных
#    Стандарт:
#    параметры:
#        frame - побайтовый листа данных
#    возвращает:
#        table_list - список подсписков (подсписок - ["Имя", "Значение"]) - оба поля текстовые

import threading

# замок для мультипоточного запроса разбора данных
data_lock = threading.Lock()
# раскрашивание переменных
# модули
linking_module = 6
eps = 3
# тип кадров
lm_beacon = 0x80
lm_tmi = 0x81
lm_full_tmi = 0x82
lm_cyclogram_result = 0x89
lm_load_param = 0x8A
pl_sol_tmi = 0x90
pl_sol_frr = 0x91
pl_sol_fr = 0x92
pl_brk_tmi = 0xA0
pl_brk_tmi = 0xA0

pl_brk_tmi_0 = 0x00
pl_brk_tmi_1 = 0x01
pl_brk_tmi_2 = 0x02
pl_brk_tmi_3 = 0x03
pl_brk_tmi_4 = 0x04

def frame_parcer(frame):
    try:
        with data_lock:
            data = []
            #
            while len(frame) < 128:
                frame.append(0xFE)
            #
            try:
                b_frame = bytes(frame)
            except Exception as error:
                print(error)
            if 0x0FF1 == val_from(frame, 0, 2):  # проверка на метку кадра
                if get_id_loc_data(val_from(frame, 4, 2))["dev_id"] == linking_module:
                    if get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_beacon:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        data.append(["Статус МС", "0x%02X" % val_from(frame, 12, 2)])
                        data.append(["Стутус ПН", "0x%04X" % val_from(frame, 14, 2)])
                        data.append(["Темп. МС, °С", "%d" % val_from(frame, 16, 1, signed=True)])
                        data.append(["Статус пит. ПН", "0x%02X" % val_from(frame, 17, 1)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_tmi:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        for i in range(6):
                            data.append(["ПН%d статус" % i, "0x%04X" % val_from(frame, (12 + i * 2), 2)])
                        for i in range(7):
                            data.append(["ПН%d напр., В" % i, "%.2f" % (val_from(frame, (24 + i * 2), 1, signed=True) / (2 ** 4))])
                            data.append(["ПН%d ток, А" % i, "%.2f" % (val_from(frame, (25 + i * 2), 1, signed=True) / (2 ** 4))])
                        data.append(["МС темп.,°С", "%.2f" % val_from(frame, 38, 1, signed=True)])
                        data.append(["NU темп.,°С", "%.2f" % val_from(frame, 39, 1, signed=True)])
                        for i in range(9):
                            data.append(["Пам.%d ук.чт." % i, "%d" % (val_from(frame, (40 + i * 8), 2))])
                            data.append(["Пам.%d ук.зап." % i, "%d" % (val_from(frame, (42 + i * 8), 2))])
                            data.append(["Пам.%d объем" % i, "%d" % (val_from(frame, (44 + i * 8), 2))])
                            data.append(["Пам.%d запол,%%" % i, "%.2f" % (val_from(frame, (46 + i * 8), 2)/256)])
                        #
                        offset = 112
                        data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                        data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                        data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                        data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                        data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                        data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                        data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_full_tmi:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        data.append(["LM:id", "0x%04X" % val_from(frame, 12, 2)])
                        data.append(["LM:status", "0x%04X" % val_from(frame, 14, 2)])
                        data.append(["LM:err.flgs", "0x%04X" % val_from(frame, 16, 2)])
                        data.append(["LM:err.cnt", "%d" % val_from(frame, 18, 1)])
                        data.append(["LM:rst.cnt", "%d" % val_from(frame, 19, 1)])
                        data.append(["LM:U,V", "%.3f" % (val_from(frame, 20, 2, signed=True) / 256)])
                        data.append(["LM:I,A", "%.3f" % (val_from(frame, 22, 2, signed=True) / 256)])
                        data.append(["LM:T,°C", "%.3f" % (val_from(frame, 24, 2, signed=True) / 256)])
                        data.append(["LM:ver", "%d.%d.%d" % ((val_from(frame, 26, 1)),
                                                             (val_from(frame, 27, 1)),
                                                             (val_from(frame, 28, 1)))])
                        #
                        pl_dict = ["LM", "PL_SOL", "PL_BRK_0"]
                        #
                        for i, pl in enumerate(pl_dict):
                            if pl != "LM":
                                offset = 12+i*18
                                data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                                data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                                data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                                data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                                data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                                data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                                data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                                data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                                data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])

                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == lm_load_param:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        data.append(["Версия", "%d.%02d.%02d" % (val_from(frame, 12, 2),
                                                                 val_from(frame, 14, 2),
                                                                 val_from(frame, 16, 2))])
                        data.append(["К. питания", "%d" % val_from(frame, 18, 2, signed=True)])
                        data.append(["К. темп", "%d" % val_from(frame, 20, 2, signed=True)])
                        data.append(["Циклограммы", "%d" % val_from(frame, 22, 2, signed=True)])
                        data.append(["CAN", "%d" % val_from(frame, 24, 2, signed=True)])
                        data.append(["Внеш. память", "%d" % val_from(frame, 26, 2, signed=True)])
                        data.append(["Загр. конфиг.", "%d" % val_from(frame, 28, 2, signed=True)])
                        data.append(["Часть flash", "%d" % val_from(frame, 30, 2, signed=True)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_sol_tmi:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        offset = 12
                        pl = "SOL"
                        data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                        data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                        data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                        data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                        data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                        data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                        data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                        data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                        data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])
                        #
                        data.append([f"{pl}:F/C", "0x%04X" % val_from(frame, 30+0, 2)])
                        data.append([f"{pl}:state", "0x%04X" % val_from(frame, 30+36, 2)])
                        data.append([f"{pl}:temp0", "%d" % (val_from(frame, 30+38, 1, signed=True) + 160)])
                        data.append([f"{pl}:temp1", "%d" % (val_from(frame, 30+39, 1, signed=True) + 160)])
                        data.append([f"{pl}:raddr", "%d" % (val_from(frame, 30+64, 2, signed=False))])
                        data.append([f"{pl}:eaddr", "%d" % (val_from(frame, 30+66, 2, signed=False))])
                        #
                        offset = 98
                        data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                        data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                        data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                        data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                        data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                        data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                        data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                        #
                        offset = 106
                        data.append([f"{pl}:ft num", "%d" % val_from(frame, offset + 0, 1)])
                        data.append([f"{pl}:ft mode", "%d" % val_from(frame, offset + 1, 1)])
                        data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, offset + 2, 1) & 0xF)])
                        data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, offset + 2, 1) >> 4)])
                        data.append([f"{pl}:ft step_num", "%d" % val_from(frame, offset + 3, 1)])
                        data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, offset + 4, 2)])
                        data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, offset + 6, 2)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        offset = 12
                        pl = "BRK"
                        data.append([f"{pl}:id", "%d" % val_from(frame, offset + 0, 2)])
                        data.append([f"{pl}:err.cnt", "%d" % val_from(frame, offset + 2, 2)])
                        data.append([f"{pl}:status", "0x%04X" % val_from(frame, offset + 4, 2)])
                        data.append([f"{pl}:voltage", "%.3f" % (val_from(frame, offset + 6, 2, signed=True) / 256)])
                        data.append([f"{pl}:current", "%.3f" % (val_from(frame, offset + 8, 2, signed=True) / 256)])
                        data.append([f"{pl}:wr_ptr", "%d" % val_from(frame, offset + 10, 2)])
                        data.append([f"{pl}:rd_ptr", "%d" % val_from(frame, offset + 12, 2)])
                        data.append([f"{pl}:full_volume", "%d" % val_from(frame, offset + 14, 2)])
                        data.append([f"{pl}:mem_fullness", "%.3f" % val_from(frame, offset + 16, 2)])
                        #
                        data.append([f"{pl}:ft num", "%d" % val_from(frame, 30, 1)])
                        data.append([f"{pl}:ft mode", "%d" % val_from(frame, 31, 1)])
                        data.append([f"{pl}:ft fun type", "%d" % (val_from(frame, 32, 1) & 0xF)])
                        data.append([f"{pl}:ft fun cmd", "%d" % (val_from(frame, 32, 1) >> 4)])
                        data.append([f"{pl}:ft step_num", "%d" % val_from(frame, 33, 1)])
                        data.append([f"{pl}:ft rpt_value", "%d" % val_from(frame, 34, 2)])
                        data.append([f"{pl}:ft frame_num", "%d" % val_from(frame, 36, 2)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    else:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        #
                        data.append(["Неизвестный тип данных", "0"])
                elif get_id_loc_data(val_from(frame, 4, 2))["dev_id"] == eps:
                    if get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi_0:
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        data.append(["Вер. ТМИ СЭС0 (PMM PDM)", "%d" % val_from(frame, 12, 2)])
                        data.append(["Режим констант", "0x%02X" % val_from(frame, 14, 1)])
                        data.append(["Режим СЭС", "0x%02X" % val_from(frame, 15, 1)])
                        data.append(["Перекл осн/рез", "0x%02X" % val_from(frame, 16, 1)])
                        data.append(["Выкл.Pass.CPU", "0x%02X" % val_from(frame, 17, 1)])
                        data.append(["Темп.PMM °C", "0x%02X" % val_from(frame, 18, 1, signed=True)])
                        data.append(["Ключи PMM", "0x%04X" % val_from(frame, 19, 2)])

                        data.append(["PwrGd PMM", "0x%04X" % val_from(frame, 21, 2)])
                        data.append(["Статус отказов PMM", "0x%08X" % val_from(frame, 23, 4)])
                        data.append(["Перезапуски осн", "0x%08X" % val_from(frame, 27, 4)])
                        data.append(["Перезапуски пезерв", "0x%08X" % val_from(frame, 31, 4)])
                        data.append(["U VBAT1, mV", "%d" % val_from(frame, 35, 2)])
                        data.append(["U VBAT2, mV", "%d" % val_from(frame, 37, 2)])
                        data.append(["U VBAT1 mean, mV", "%d" % val_from(frame, 39, 2)])
                        data.append(["U VBAT2 mean, mV", "%d" % val_from(frame, 41, 2)])
                        data.append(["I VBAT1, mA", "%d" % val_from(frame, 43, 2)])
                        data.append(["I VBAT2, mA", "%d" % val_from(frame, 45, 2)])
                        data.append(["I VBAT1 mean, mA", "%d" % val_from(frame, 47, 2)])
                        data.append(["I VBAT2 mean, mA", "%d" % val_from(frame, 49, 2)])
                        #
                        data.append(["I СЭС, мА", "%d" % val_from(frame, 51, 2)])
                        data.append(["U PMM, mV", "%d" % val_from(frame, 53, 2)])
                        data.append(["U сил. СЭС, mV", "%d" % val_from(frame, 55, 2)])
                        data.append(["P СЭС, мВт", "%d" % val_from(frame, 57, 2)])
                        data.append(["P КА+ПН, мВт", "%d" % val_from(frame, 59, 2)])
                        data.append(["Концевики", "0x%04X" % val_from(frame, 61, 2)])
                        data.append(["Версия ПО", "%d" % val_from(frame, 63, 2)])
                        #
                        data.append(["Ключи PDM", "0x%04X" % val_from(frame, 65, 2)])
                        data.append(["PwrGd PDM", "0x%04X" % val_from(frame, 67, 2)])
                        data.append(["Статус отказов PDM", "0x%08X" % val_from(frame, 69, 4)])
                        #
                        for i in range(4):
                            data.append([f"T PDM{i}, °C", "%d" % val_from(frame, 73+i, 1, signed=True)])
                        data.append([f"T PDM median, °C", "%d" % val_from(frame, 73+4, 1, signed=True)])
                        #
                        for i in range(6):
                            data.append([f"U PDM{i}, mV", "%d" % val_from(frame, 78+2*i, 2, signed=False)])
                            data.append([f"U PDM{i} mean, mV", "%d" % val_from(frame, 90+2*i, 2, signed=False)])
                            data.append([f"I PDM{i}, mA", "%d" % val_from(frame, 102+2*i, 2, signed=True)])
                            data.append([f"I PDM{i} mean, mA", "%d" % val_from(frame, 114+2*i, 2, signed=True)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi_1:  # ТМИ солнечных панелей 1
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        data.append(["Вер. ТМИ СЭС1 (PAM)", "%d" % val_from(frame, 12, 2)])
                        data.append(["P полн. PAM, мВт", "%d" % val_from(frame, 14, 2)])
                        data.append(["Ключи пит. PAM)", "0x%04X" % val_from(frame, 16, 2)])
                        data.append(["PWR GD", "0x%04X" % val_from(frame, 18, 2)])
                        data.append(["Статус отк.", "0x%08X" % val_from(frame, 20, 4)])
                        #
                        for i in range(4):
                            data.append([f"T PAM{i}, °C", "%d" % val_from(frame, 24+i, 1, signed=True)])
                        data.append([f"T median, °C", "%d" % val_from(frame, 24+4, 1, signed=True)])
                        #
                        data.append(["Ст. IdealDiod", "0x%04X" % val_from(frame, 29, 1)])
                        data.append(["Ст. ош. входных к.", "0x%04X" % val_from(frame, 30, 1)])
                        #
                        name_list = ["Ch1 Y+", "Ch2 X+", "Ch3 Y-", "Ch4 X-", "Ch5 X- F", "Ch6 Y+ F"]
                        for i, name in enumerate(name_list):
                            data.append([f"U {name}, mV", "%d" % val_from(frame, 31 + 2*i, 2)])
                            data.append([f"I {name}, mA", "%d" % val_from(frame, 43 + 2*i, 2, signed=True)])
                        #
                        name_list = ["Ch1 X- F", "Ch2 X-", "Ch3 X+ F", "Ch4 X+", "Ch5 Y+", "Ch6 Y-"]
                        for i, name in enumerate(name_list):
                            data.append([f"Статус {name}", "0x%04X" % val_from(frame, 55 + 2*i, 2)])
                        #
                        name_list = ["Ch1 X- F", "Ch2 X-", "Ch3 X+ F", "Ch4 X+", "Ch5 Y+", "Ch6 Y-"]
                        for i, name in enumerate(name_list):
                            for j in range(4):
                                data.append([f"T {name} к{j}, °C", "%d" % val_from(frame, 67 + j + 4*i, 1, signed=True)])
                        #
                        name_list = ["Ch1 X- F", "Ch2 X-", "Ch3 X+ F", "Ch4 X+", "Ch5 Y+", "Ch6 Y-"]
                        for i, name in enumerate(name_list):
                                data.append([f"T median {name}, °C", "%d" % val_from(frame, 91 + i, 1, signed=True)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi_2:  # ТМИ батарей 1
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        data.append(["Вер. ТМИ СЭС2 (PBM ч1)", "%d" % val_from(frame, 12, 2)])
                        #
                        data.append(["P зар/раз, мВт", "%d" % val_from(frame, 14, 2, signed=True)])
                        data.append(["P нагр, мВт", "%d" % val_from(frame, 16, 2)])
                        data.append(["Заряд, mAh", "%d" % val_from(frame, 18, 2)])
                        data.append(["Заряд, %", "%d" % val_from(frame, 20, 1)])
                        data.append(["Кл. зар/раз", "0x%04X" % val_from(frame, 21, 2)])
                        data.append(["Кл. термост", "0x%02X" % val_from(frame, 23, 1)])
                        data.append(["Кл. нагр. PBM", "0x%02X" % val_from(frame, 24, 1)])
                        data.append(["Кл. ав.зар.", "0x%02X" % val_from(frame, 25, 1)])
                        data.append(["Автокорр. зар.", "0x%02X" % val_from(frame, 26, 1)])
                        #
                        for i in range(4):
                            data.append([f"Ош.PBM{i}", "0x%04X" % val_from(frame, 27+2*i, 2)])
                        for i in range(4):
                            data.append([f"Ош.контр.1 PBM{i}", "0x%04X" % val_from(frame, 35+4*i, 2)])
                            data.append([f"Ош.контр.2 PBM{i}", "0x%04X" % val_from(frame, 37+4*i, 2)])
                        for i in range(4):
                            data.append([f"Ур.зар. в.1 PBM{i}, %", "%d" % val_from(frame, 51+2*i, 1)])
                            data.append([f"Ур.зар. в.2 PBM{i}, %", "%d" % val_from(frame, 52+2*i, 1)])
                        for i in range(4):
                            data.append([f"Ур.зар. в.1 PBM{i}, mAh", "%d" % val_from(frame, 59+4*i, 2)])
                            data.append([f"Ур.зар. в.2 PBM{i}, mAh", "%d" % val_from(frame, 61+4*i, 2)])
                        for i in range(4):
                            data.append([f"I зар. в.1 PBM{i}, mA", "%d" % val_from(frame, 75+4*i, 2, signed=True)])
                            data.append([f"I зар. в.2 PBM{i}, mA", "%d" % val_from(frame, 77+4*i, 2, signed=True)])
                        for i in range(4):
                            data.append([f"T PBM{i} кнтр.1, °C", "%d" % val_from(frame, 91+6*i, 1, signed=True)])
                            data.append([f"T PBM{i} кнтр.2, °C", "%d" % val_from(frame, 92+6*i, 1, signed=True)])
                            for j in range(4):
                                data.append([f"T PBM{i} пл.{j}, °C", "%d" % val_from(frame, 93+1*j+6*i, 1, signed=True)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                    elif get_id_loc_data(val_from(frame, 4, 2))["data_code"] == pl_brk_tmi_3:  # ТМИ батарей 2
                        #
                        data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                        data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                        data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                        data.append(["Номер кадра, шт", "%d" % val_from(frame, 6, 2)])
                        data.append(["Время кадра, с", "%d" % val_from(frame, 8, 4)])
                        #
                        data.append(["Вер. ТМИ СЭС3 (PBM ч2)", "%d" % val_from(frame, 12, 2)])
                        #
                        for i in range(4):
                            for j in range(2):
                                for k in range(2):
                                    data.append([f"U PBM{i} в{j} акк{k}, мВ", "%d" % val_from(frame, 14 + k*2 + j*4 + 8*i, 2)])
                        #
                        for i in range(4):
                            for j in range(2):
                                    data.append([f"I max PBM{i} в{j}, мA", "%d" % val_from(frame, 46 + j*4 + 8*i, 2, signed=True)])
                                    data.append([f"I min PBM{i} в{j}, мA", "%d" % val_from(frame, 48 + j*4 + 8*i, 2, signed=True)])
                        #
                        for i in range(4):
                            for j in range(2):
                                    data.append([f"Ubat min PBM{i} в{j}, мВ", "%d" % val_from(frame, 78 + j*2 + 4*i, 2)])
                        #
                        for i in range(4):
                            for j in range(2):
                                    data.append([f"I нагр PBM{i} в{j}, мA", "%d" % val_from(frame, 94 + j*2 + 4*i, 2, signed=True)])
                        #
                        for i in range(4):
                            for j in range(2):
                                    data.append([f"Возраст PBM{i} в{j}", "%d" % val_from(frame, 110 + j*1 + 2*i, 1)])
                        #
                        for i in range(4):
                            for j in range(2):
                                    data.append([f"Кол-во циклов PBM{i} в{j}", "%d" % val_from(frame, 118 + j*1 + 2*i, 1)])
                        #
                        data.append(["CRC-16", "0x%04X" % crc16_calc(frame, 128)])
                else:
                    #
                    data.append(["Метка кадра", "0x%04X" % val_from(frame, 0, 2)])
                    data.append(["SAT_ID", "0x%04X" % val_from(frame, 2, 2)])
                    data.append(["Определитель", "0x%04X" % val_from(frame, 4, 2)])
                    #
                    data.append(["Неизвестный определитель", "0"])
            else:
                data.append(["Данные не распознаны", "0"])
            return data
    except Exception as error:
        print(error)
        return None


def get_id_loc_data(id_loc):
    """
    разбор переменной IdLoc
    :param id_loc: переменная, содржащая IdLoc по формату описания на протокол СМКА
    :return: кортеж значений полей переменной IdLoc: номер устройства, флаги записи, код данных
    """
    device_id = (id_loc >> 12) & 0xF
    flags = (id_loc >> 8) & 0xF
    data_id = (id_loc >> 0) & 0xFF
    return {"dev_id": device_id, "flags": flags, "data_code": data_id}


def val_from(frame, offset, leng, byteorder="little", signed=False, debug=False):
    """
    обертка для функции сбора переменной из оффсета и длины, пишется короче и по умолчанию значения самый используемые
    :param frame: лист с данными кадра
    :param offset: оффсет переменной в байтах
    :param leng: длина переменной в байтах
    :param byteorder: порядок следования байт в срезе ('little', 'big')
    :param signed: знаковая или не знаковая переменная (True, False)
    :return: интовое значение переменной
    """
    retval = int.from_bytes(frame[offset + 0:offset + leng], byteorder=byteorder, signed=signed)
    if debug:
        print(frame[offset + 0:offset + leng], " %04X" % int.from_bytes(frame[offset + 0:offset + leng], byteorder=byteorder, signed=signed))
    return retval


# алгоритм подсчета crc16 для кадра
crc16tab = [0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
            0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
            0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
            0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
            0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
            0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
            0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
            0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
            0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
            0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
            0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
            0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
            0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
            0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
            0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
            0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
            0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
            0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
            0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
            0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
            0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
            0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
            0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
            0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
            0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
            0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
            0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
            0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
            0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
            0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
            0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
            0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0]


def crc16_calc(buf, length):
    d = 1
    crc = 0x1D0F
    for i in range(length):
        index = ((crc >> 8) ^ buf[i + d]) & 0x00FF
        crc = (crc << 8) ^ crc16tab[index]
        crc &= 0xFFFF
        d = -d
    return crc
