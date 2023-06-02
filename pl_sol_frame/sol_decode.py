import sys
import os
import numpy as np
import csv
# from astropy.io import fits
import matplotlib.pyplot as plt

def read_bit(byte_str, value, byte_ind, bit_ind, buf):
    if bit_ind ==0:
        buf = int.from_bytes(byte_str[byte_ind:byte_ind+2], 'little')
        byte_ind+= 2
        bit_ind = 16
    value = (value << 1) | (buf & 1)
    buf >>= 1
    bit_ind-= 1
    return value, byte_ind, bit_ind, buf

def get_interval(low, high, value, cod, packet, byte_ind, bit_ind, buf):
    curr_range = high - low + 1    
    curr_cum = ( (value - low + 1) * 2**17 - 1 ) // curr_range  

    interval = ((cod//4)*4 <= curr_cum).sum()-1    # Andrey's x2-1      

    if (curr_range == 2**17):     # not needed?
        high = low + (cod[interval+1]//4)*4 - 1
        low = low + (cod[interval]//4)*4
    else:
        high = low + curr_range*(cod[interval+1]//4)*4 // 2**17 - 1
        low = low + curr_range*(cod[interval]//4)*4 // 2**17

    while True:
        if high < 2**16:
            pass
        elif low >= 2**16:
            value -= 2**16
            low -= 2**16
            high -= 2**16
        elif ((low >= 2**15) and (high < 3*2**15)):
            value -= 2**15
            low -= 2**15
            high -= 2**15
        else:
            break
        low*= 2
        high = high*2 + 1
        value, byte_ind, bit_ind, buf = read_bit(packet, value, byte_ind, bit_ind, buf)

    return interval, low, high, value, byte_ind, bit_ind, buf

def line_decode(in_line):
    llen = in_line.size
    out_line = np.zeros(llen)

    out_line[:-1:2] =  ( (74146 // 8)*in_line[:llen//2] + 4000) // 2**13
    out_line[1::2] = ( (57926 // 4)*in_line[llen//2:] + 8000) // 2**14

    out_line[2:-1:2] -= ( 15 * (out_line[1:-2:2] + out_line[3::2]) ) // 32      # 4
    out_line[0] -= (2 * 15 * out_line[1]) // 32

    out_line[1:-2:2] -= ( (52429 // 4) * (out_line[0:-3:2] + out_line[2:-1:2]) ) // 2**14     # 3
    out_line[-1] -= (2 * (52429 // 4) * out_line[-2]) // 2**14

    out_line[2:-1:2] -= (-1 * (out_line[1:-2:2] + out_line[3::2])) // 2**4      # 2
    out_line[0] -= (2 * -1 * out_line[1]) // 2**4

    out_line[1:-2:2] -= (-3 * (out_line[0:-3:2] + out_line[2:-1:2])) // 2      # 1
    out_line[-1] -= (2 * -3 * out_line[-2]) // 2

    return out_line


# ----------------- read data -----------------

if len(sys.argv) != 2:
    raise Exception('Valid format: sol_decode.py <input_file>')
infile = sys.argv[1]

infile_noext, in_ext = os.path.splitext(infile)
if in_ext == '.bin':
    with open(infile, "rb") as f:
        frames = f.read()
elif in_ext == '.txt':
    with open(infile, "r") as f:
        frames_txt = f.read()
    frames_txt = frames_txt.replace('XX','')
    frames = bytes.fromhex(frames_txt)
else:
    raise Exception('Input must be either binary (*.bin) or text (*.txt)')

frarr = np.frombuffer(frames, dtype=np.uint8)

# ----------------- telemetry -----------------

exp_vals = [0, 50, 63, 80, 100, 125, 160, 200, 250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000,
            2500, 3200,4000, 5000, 6300, 8000, 10000, 12500, 16000, 20000, 25000, 32000, 40000, 50000]

fr_start_mask = ((frarr[:-5] == 0x0F) & (frarr[1:-4] == 0xF1) &
                 (frarr[2:-3] == 0x00) & (frarr[3:-2] == 0x02) & 
                 (frarr[4:-1] == 0x60) & (frarr[5:] == 0x90))
fr_start_ind = np.where(fr_start_mask)[0]

telemerty = []

for fsi in fr_start_ind:
    frame = frames[fsi:fsi+128]
    fr_data = frame[12:126]
    
    F_C = int.from_bytes(fr_data[0:2], 'little')
    F = int.from_bytes(fr_data[2:4], 'little')
    SDRV = int.from_bytes(fr_data[8:10], 'little')
    SPV = int.from_bytes(fr_data[20:22], 'little')
    STATE = int.from_bytes(fr_data[36:38], 'little')
    
    telemerty.append({
        'F/C EXP': F_C & (2**5-1),    # exp_vals[F_C & (2**5-1)],   # 
        'F/C IC' : (F_C >> 5) & (2**3-1),
        'F/C LS/HS': (F_C >> 8) & 1,
        'F/C FSP': (F_C >> 9) & 1,
        'F/C FSV': (F_C >> 10) & 1,
        'F/C FT': (F_C >> 11) & 1,
        'F/C CD': (F_C >> 12) & 1,
        'F/C TRAIN': (F_C >> 13) & 1,
        'F/C RAW': (F_C >> 14) & 1,
        'F/C ST': (F_C >> 15) & 1,
        'F ST': (F >> 15) & 1,
        'SDRV SD': (SDRV >> 15) & 1,
        'SDRV[14:9]': (F_C >> 9) & (2**7-1),
        'SDRV[8:0]': SDRV & (2**8-1),
        'TTM': int.from_bytes(fr_data[16:18], 'little'),
        'SPV XYV': SPV & (2**3-1),
        'SPV XYW': (SPV >> 4) & (2**2-1),
        'SPV SI': (SPV >> 6) & (2**2-1),
        'SPV SDX': (SPV >> 8) & (2**4-1),
        'SPV SDY ': (SPV >> 12) & (2**4-1),
        'CDD': int.from_bytes(fr_data[28:30], 'little'),
        'STM': int.from_bytes(fr_data[34:36]+fr_data[32:34], 'little'),
        'STATE RDY': (STATE >> 15) & 1,
        'STATE DRV': (STATE >> 12) & 1,
        'STATE FYV': (STATE >> 11) & 1,
        'STATE FXV': (STATE >> 10) & 1,
        'STATE FYW': (STATE >> 9) & 1,
        'STATE FXW': (STATE >> 8) & 1,
        'STATE FI': (STATE >> 7) & 1,
        'STATE ST': STATE & (2**3-1),
        'TEMP0': fr_data[39],    # fr_data[39]+160-273,   # 
        'TEMP1': fr_data[38],    # fr_data[38]+160-273,   # 
        'SUNX': int.from_bytes(fr_data[40:42], 'little'),
        'SUNY': int.from_bytes(fr_data[42:44], 'little'),
        'SUNX1': int.from_bytes(fr_data[44:46], 'little'),
        'SUNY1': int.from_bytes(fr_data[46:48], 'little'),
        'SUNX2': int.from_bytes(fr_data[48:50], 'little'),
        'SUNY2': int.from_bytes(fr_data[50:52], 'little'),
        'SUNVX': int.from_bytes(fr_data[52:54], 'little'),
        'SUNVY': int.from_bytes(fr_data[54:56], 'little'),
        'SUNI': int.from_bytes(fr_data[56:58], 'little'),
        'ECC_ERR': int.from_bytes(fr_data[58:60], 'little'),
        'CDS': int.from_bytes(fr_data[60:62], 'little'),
        'RADDR': int.from_bytes(fr_data[62:64], 'little'),
        'EADDR': int.from_bytes(fr_data[64:66], 'little')
    })

with open(infile_noext+'.csv', 'w', newline='') as f:
    dict_writer = csv.DictWriter(f, telemerty[0].keys(), delimiter=';',)
    dict_writer.writeheader()
    dict_writer.writerows(telemerty)

# ----------------- unpack image -----------------

fr_start_mask = ((frarr[:-5] == 0x0F) & (frarr[1:-4] == 0xF1) &
                 (frarr[2:-3] == 0x00) & (frarr[3:-2] == 0x02) & 
                 (frarr[4:-1] == 0x60) & ( (frarr[5:] == 0x91) | (frarr[5:] == 0x92) ))
fr_start_ind = np.where(fr_start_mask)[0]    # equivalent to fr_start = start_mask.nonzero()[0]

image_data = b''
for fsi in fr_start_ind:
    frame = frames[fsi:fsi+128]
    
#     fr_num = int.from_bytes(frame[6:8], 'big')
#     fr_time_sec = int.from_bytes(frame[8:12], 'big')
#     fr_time = dt(year=2000, month=1, day=1) + td(seconds=fr_time_sec)
#     fr_crc = int.from_bytes(frame[126:], 'big')
    
    fr_data = frame[12:126]
#     addr = int.from_bytes(fr_data[0:2], 'little')
    image_data+= fr_data[2:64]
    
parr = np.frombuffer(image_data, dtype=np.uint8)
p_start_mask = ( (parr[:-3] == 0x7C)  & (parr[1:-2] == 0x6E) &
                 (parr[2:-1] == 0xA1) & (parr[3:] == 0x2C)   )
p_start_ind = np.where(p_start_mask)[0]
n_pack = p_start_ind.size

# ----------------- read image by quadrants -----------------

image = np.zeros((2048, 2048), dtype=np.short)
for pn in range(n_pack):
    packet = image_data[p_start_ind[pn]:p_start_ind[pn+1]] if pn < n_pack-1 else image_data[p_start_ind[pn]:]

    FRAME_ID = int.from_bytes(packet[4:6], 'little')
    EXP = (FRAME_ID >> 11) & (2**5-1)
    STM = (FRAME_ID & (2**11-1)) << 2

    FRAME_Descr = int.from_bytes(packet[6:8], 'little')
    QDRNT = FRAME_Descr & (2**6-1)
    IC_act = (FRAME_Descr >> 6) & (2**7-1)      # == Andrey's d_step
    HG = (FRAME_Descr >> 13) & 1
    
    stat = np.full(128, 2, dtype=np.uint32)
    for i in range(7):
        stat[(61+i) % 64] = int.from_bytes(packet[8+i*2:8+(i+1)*2], 'little')
    x = 4
    z = stat[3]
    while z > 7:
        z//= 4
        stat[x] = z
        x+= 1
    x = 60
    z = stat[61]
    while z > 7:
        z//= 4
        stat[x] = z
        x-= 1
    
    LP = int.from_bytes(packet[22:24], 'little')
    
# ----------------------- arythm decode --------------------------
    
    summ = stat.sum()
    cum = np.concatenate(( [0], stat.cumsum() ))
    cod = (cum * 2**16) // summ * 2

    Aout = np.zeros(256*256, dtype=int)
    Aout[0] = LP
    Qdec = np.zeros(256*256, dtype=int)
    Qdec[0] = LP
    
    bit_ind = 0
    byte_ind = 24
    value = 0
    buf = 0
    for i in range(17):
        value, byte_ind, bit_ind, buf = read_bit(packet, value, byte_ind, bit_ind, buf)
    low = 0
    high = 2**17-1

    for i in range(1, Aout.size):      
        interval, low, high, value, byte_ind, bit_ind, buf = get_interval(low, high, value, cod, packet, byte_ind, bit_ind, buf)

        if interval > 63:
            int_high = interval - 64
            int_low, low, high, value, byte_ind, bit_ind, buf = get_interval(low, high, value, cod, packet, byte_ind, bit_ind, buf)
            interval = (int_high << 6) | (int_low & (2**6-1))
            interval -= (2**12) * (interval > (2**11-1))
        else:
            interval -= (2**6) * (interval > (2**5-1)) 

        Aout[i] = interval

        dec = (interval * 256) // IC_act
        if interval >= 1:
            dec = (interval * 1024 + 512) // IC_act
        if (interval < 0):
            dec = (interval * 1024 - 512) // IC_act

        Qdec[i] = dec

# ------------------ wavelet ----------------------

    WL_enc = np.reshape(Qdec, (256,256))

    for p in range(int(np.log2(256))):
        z = 2**(p+1)
        for yi in range(z):
            WL_enc[yi,:z] = line_decode(WL_enc[yi,:z])
        for xi in range(z):
            WL_enc[:z,xi] = line_decode(WL_enc[:z,xi])
        
    qx = pn % 8
    qy = pn // 8
    image[qy*256:(qy+1)*256, qx*256:(qx+1)*256] = WL_enc
    
# ------------------ save image ----------------------

# exptime = exp_vals[EXP]/1e3
# hdu = fits.PrimaryHDU(image)
# hdu.header['EXPTIME'] = (exptime, 'Exposure time in seconds')
# hdu.writeto(infile_noext+'.fits', overwrite=True)

plt.figure(figsize=(20.48, 20.48), dpi=100)
plt.axis('off')
plt.imshow(image, origin='lower', cmap='gray') 
plt.savefig(infile_noext+'.png', bbox_inches='tight', pad_inches=0, dpi=100)
