"""python side of the headless mupen64plus harness (harness.c)."""
import ctypes
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.environ.get('M64P_CORE', os.path.join(HERE, 'mupen64plus-core', 'projects', 'unix', 'libmupen64plus.so.2'))
RSP = os.environ.get('M64P_RSP', '/usr/lib/x86_64-linux-gnu/mupen64plus/mupen64plus-rsp-hle.so')

# n64 controller bits as the input plugin expects them (BUTTONS.Value)
R_DPAD, L_DPAD, D_DPAD, U_DPAD = 0x0001, 0x0002, 0x0004, 0x0008
START, Z, B, A = 0x0010, 0x0020, 0x0040, 0x0080
R_CBUTTON, L_CBUTTON, D_CBUTTON, U_CBUTTON = 0x0100, 0x0200, 0x0400, 0x0800
R_TRIG, L_TRIG = 0x1000, 0x2000


class Emu:
    def __init__(self, rom, datadir, verbose=False):
        os.makedirs(datadir, exist_ok=True)
        self.lib = ctypes.CDLL(os.path.join(HERE, 'harness.so'))
        self.lib.h_rdram.restype = ctypes.c_void_p
        self.lib.h_frame.restype = ctypes.c_uint
        r = self.lib.h_init(os.path.abspath(CORE).encode(), RSP.encode(), rom.encode(),
                            datadir.encode(), int(verbose))
        if r != 0:
            raise RuntimeError('h_init failed: %d' % r)
        self.ram = (ctypes.c_uint32 * (0x800000 // 4)).from_address(self.lib.h_rdram())

    # rdram is stored as host-endian 32-bit words
    def u32(self, addr):
        return self.ram[(addr & 0x7FFFFF) >> 2]

    def s32(self, addr):
        v = self.u32(addr)
        return v - (1 << 32) if v & 0x80000000 else v

    def u16(self, addr):
        w = self.u32(addr & ~3)
        return (w >> (16 - (addr & 2) * 8)) & 0xFFFF

    def s16(self, addr):
        v = self.u16(addr)
        return v - 0x10000 if v & 0x8000 else v

    def u8(self, addr):
        w = self.u32(addr & ~3)
        return (w >> (24 - (addr & 3) * 8)) & 0xFF

    def s8(self, addr):
        v = self.u8(addr)
        return v - 0x100 if v & 0x80 else v

    def f32(self, addr):
        return struct.unpack('<f', struct.pack('<I', self.u32(addr)))[0]

    def w32(self, addr, v):
        self.ram[(addr & 0x7FFFFF) >> 2] = v & 0xFFFFFFFF

    def w16(self, addr, v):
        i = (addr & 0x7FFFFF) >> 2
        sh = 16 - (addr & 2) * 8
        self.ram[i] = (self.ram[i] & ~(0xFFFF << sh) & 0xFFFFFFFF) | ((v & 0xFFFF) << sh)

    def w8(self, addr, v):
        i = (addr & 0x7FFFFF) >> 2
        sh = 24 - (addr & 3) * 8
        self.ram[i] = (self.ram[i] & ~(0xFF << sh) & 0xFFFFFFFF) | ((v & 0xFF) << sh)

    def wf32(self, addr, v):
        self.w32(addr, struct.unpack('<I', struct.pack('<f', v))[0])

    def step(self, buttons=0, x=0, y=0, n=1):
        if self.lib.h_step(buttons, x, y, n) != 0:
            raise RuntimeError('emulator stopped')

    def save(self, path):
        self.lib.h_save(os.path.abspath(path).encode())

    def load(self, path, frame=0):
        self.lib.h_load(os.path.abspath(path).encode(), frame)

    @property
    def frame(self):
        return self.lib.h_frame()

    @property
    def polls(self):
        return self.lib.h_polls()
