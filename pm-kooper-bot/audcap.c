/* minimal mupen64plus audio plugin: appends every audio buffer the game hands the AI (16-bit stereo) to the file
 * named by AUDCAP_FILE, in emulation order, so audio stays in sync with emulated frames. The DAC rate is written to
 * AUDCAP_FILE.rate. Samples are written as little-endian L,R int16. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "m64p_types.h"
#include "m64p_plugin.h"
#define EXPORT __attribute__((visibility("default")))
static AUDIO_INFO ai; static FILE *f; static unsigned rate;
EXPORT m64p_error CALL PluginStartup(m64p_dynlib_handle h, void *c, void (*d)(void *, int, const char *)) {
    const char *p = getenv("AUDCAP_FILE"); if (p) f = fopen(p, "ab"); return M64ERR_SUCCESS; }
EXPORT m64p_error CALL PluginShutdown(void) { if (f) fclose(f); f = NULL; return M64ERR_SUCCESS; }
EXPORT m64p_error CALL PluginGetVersion(m64p_plugin_type *t, int *v, int *a, const char **n, int *cap) {
    if (t) *t = M64PLUGIN_AUDIO; if (v) *v = 0x010000; if (a) *a = 0x020000; if (n) *n = "audcap"; if (cap) *cap = 0; return M64ERR_SUCCESS; }
EXPORT void CALL AiDacrateChanged(int sys) {
    unsigned dac = *ai.AI_DACRATE_REG; unsigned clk = sys == SYSTEM_PAL ? 49656530 : sys == SYSTEM_MPAL ? 48628316 : 48681812;
    rate = clk / (dac + 1);
    const char *p = getenv("AUDCAP_FILE");
    if (p) { char b[512]; snprintf(b, sizeof b, "%s.rate", p); FILE *r = fopen(b, "w"); if (r) { fprintf(r, "%u\n", rate); fclose(r); } } }
EXPORT void CALL AiLenChanged(void) {
    if (!f) return;
    unsigned addr = *ai.AI_DRAM_ADDR_REG & 0xFFFFFF, len = *ai.AI_LEN_REG & 0x3FFF8;
    unsigned char *src = ai.RDRAM + addr;
    for (unsigned i = 0; i + 4 <= len; i += 4) {     /* host-endian word = (L << 16) | R */
        unsigned w; memcpy(&w, src + i, 4);
        short s[2] = { (short)(w >> 16), (short)(w & 0xFFFF) };
        fwrite(s, 2, 2, f);
    }
    fflush(f); }
EXPORT int CALL InitiateAudio(AUDIO_INFO info) { ai = info; return 1; }
EXPORT void CALL ProcessAList(void) {}
EXPORT int CALL RomOpen(void) { return 1; }
EXPORT void CALL RomClosed(void) {}
EXPORT void CALL SetSpeedFactor(int p) {}
EXPORT void CALL VolumeUp(void) {}
EXPORT void CALL VolumeDown(void) {}
EXPORT int CALL VolumeGetLevel(void) { return 100; }
EXPORT void CALL VolumeSetLevel(int l) {}
EXPORT void CALL VolumeMute(void) {}
EXPORT const char * CALL VolumeGetString(void) { return "100%"; }
