#define _GNU_SOURCE
/*
 * headless mupen64plus harness for bots.
 *
 * the emulator runs on its own thread.  it stops at "blocking points":
 *   - the end of every rendered game frame (the core's frame callback)
 *   - right after a savestate was saved or loaded
 * at a blocking point the controller thread (python through ctypes) can:
 *   h_step(buttons, x, y)  set the controller and run to the end of the next frame
 *   h_save(path)           save a state, block again right after it
 *   h_load(path)           load a state, block again right after it
 * this library is also the input plugin: the core calls GetKeys on it.
 */
#include <dlfcn.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M64P_CORE_PROTOTYPES 1
#include "m64p_types.h"
#include "m64p_plugin.h"
#include "m64p_frontend.h"
#include "m64p_config.h"
#include "m64p_debugger.h"

static void *core;
static ptr_CoreStartup       pCoreStartup;
static ptr_CoreDoCommand     pCoreDoCommand;
static ptr_CoreAttachPlugin  pCoreAttachPlugin;
static ptr_DebugMemGetPointer pDebugMemGetPointer;
static ptr_ConfigOpenSection pConfigOpenSection;
static ptr_ConfigSetParameter pConfigSetParameter;

static pthread_t emu_thread;
static pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t  cv  = PTHREAD_COND_INITIALIZER;
/* emu_blocked: emulator is waiting at a blocking point.  go: controller released it */
static int emu_blocked, go, emu_done, verbose;
static unsigned frame_no;
static BUTTONS cur_input;
static int poll_count;

/* ---- blocking ---- */
static void block_here(void){
    pthread_mutex_lock(&mtx);
    emu_blocked = 1;
    go = 0;
    pthread_cond_broadcast(&cv);
    while(!go) pthread_cond_wait(&cv, &mtx);
    emu_blocked = 0;
    pthread_mutex_unlock(&mtx);
}

static void wait_blocked(void){
    pthread_mutex_lock(&mtx);
    while(!emu_blocked && !emu_done) pthread_cond_wait(&cv, &mtx);
    pthread_mutex_unlock(&mtx);
}

static void release(void){
    pthread_mutex_lock(&mtx);
    emu_blocked = 0;
    go = 1;
    pthread_cond_broadcast(&cv);
    pthread_mutex_unlock(&mtx);
}

static void frame_cb(unsigned int n){
    frame_no++;
    block_here();
}

static void state_cb(void *ctx, m64p_core_param p, int v){
    if(p == M64CORE_STATE_SAVECOMPLETE || p == M64CORE_STATE_LOADCOMPLETE) {
        if(verbose) fprintf(stderr, "harness: state %s %d\n", p == M64CORE_STATE_SAVECOMPLETE ? "saved" : "loaded", v);
        block_here();
    }
}

static void debug_cb(void *ctx, int level, const char *msg){
    if(verbose || level <= M64MSG_WARNING) fprintf(stderr, "core: %s\n", msg);
}

static void *emu_main(void *arg){
    pCoreDoCommand(M64CMD_EXECUTE, 0, NULL);
    pthread_mutex_lock(&mtx);
    emu_done = 1;
    pthread_cond_broadcast(&cv);
    pthread_mutex_unlock(&mtx);
    return NULL;
}

/* ---- input plugin ---- */
static CONTROL *controls;
EXPORT m64p_error CALL PluginStartup(m64p_dynlib_handle h, void *c, void (*d)(void *, int, const char *)){ return M64ERR_SUCCESS; }
EXPORT m64p_error CALL PluginShutdown(void){ return M64ERR_SUCCESS; }
EXPORT m64p_error CALL PluginGetVersion(m64p_plugin_type *type, int *ver, int *api, const char **name, int *caps){
    if(type) *type = M64PLUGIN_INPUT;
    if(ver) *ver = 0x010000;
    if(api) *api = 0x020100;
    if(name) *name = "bot input";
    if(caps) *caps = 0;
    return M64ERR_SUCCESS;
}
EXPORT void CALL InitiateControllers(CONTROL_INFO info){
    controls = info.Controls;
    controls[0].Present = 1;
    controls[0].RawData = 0;
    controls[0].Plugin = PLUGIN_NONE;
}
EXPORT void CALL GetKeys(int ctl, BUTTONS *keys){
    if(ctl == 0) { *keys = cur_input; poll_count++; }
    else keys->Value = 0;
}
EXPORT void CALL ControllerCommand(int c, unsigned char *cmd){}
EXPORT void CALL ReadController(int c, unsigned char *cmd){}
EXPORT int  CALL RomOpen(void){ return 1; }
EXPORT void CALL RomClosed(void){}
EXPORT void CALL SDL_KeyDown(int k, int s){}
EXPORT void CALL SDL_KeyUp(int k, int s){}

/* ---- api for python ---- */
int h_init(const char *corelib, const char *rsplib, const char *rom, const char *datadir, int verb){
    verbose = verb;
    core = dlopen(corelib, RTLD_NOW | RTLD_GLOBAL);
    if(!core) { fprintf(stderr, "%s\n", dlerror()); return -1; }
    pCoreStartup = dlsym(core, "CoreStartup");
    pCoreDoCommand = dlsym(core, "CoreDoCommand");
    pCoreAttachPlugin = dlsym(core, "CoreAttachPlugin");
    pDebugMemGetPointer = dlsym(core, "DebugMemGetPointer");
    pConfigOpenSection = dlsym(core, "ConfigOpenSection");
    pConfigSetParameter = dlsym(core, "ConfigSetParameter");
    if(pCoreStartup(0x020001, datadir, datadir, NULL, debug_cb, NULL, state_cb) != M64ERR_SUCCESS) return -2;

    m64p_handle sec;
    if(pConfigOpenSection("Core", &sec) == M64ERR_SUCCESS) {
        int v = 0;
        pConfigSetParameter(sec, "OnScreenDisplay", M64TYPE_BOOL, &v);
        pConfigSetParameter(sec, "SaveDiskFormat", M64TYPE_INT, &v);
        pConfigSetParameter(sec, "SaveStatePath", M64TYPE_STRING, datadir);
        pConfigSetParameter(sec, "SaveSRAMPath", M64TYPE_STRING, datadir);
        v = 1; /* r4300 emulator: 2 = dynarec */
        v = 2;
        pConfigSetParameter(sec, "R4300Emulator", M64TYPE_INT, &v);
    }

    FILE *f = fopen(rom, "rb");
    if(!f) return -3;
    fseek(f, 0, SEEK_END); long sz = ftell(f); fseek(f, 0, SEEK_SET);
    void *buf = malloc(sz);
    fread(buf, 1, sz, f); fclose(f);
    if(pCoreDoCommand(M64CMD_ROM_OPEN, sz, buf) != M64ERR_SUCCESS) return -4;
    free(buf);

    void *rsp = dlopen(rsplib, RTLD_NOW);
    if(!rsp) { fprintf(stderr, "%s\n", dlerror()); return -5; }
    m64p_error (*ps)(m64p_dynlib_handle, void *, void (*)(void *, int, const char *)) = dlsym(rsp, "PluginStartup");
    ps(core, NULL, debug_cb);
    if(pCoreAttachPlugin(M64PLUGIN_RSP, rsp) != M64ERR_SUCCESS) return -6;

    Dl_info di;
    dladdr((void*)h_init, &di);
    void *self = dlopen(di.dli_fname, RTLD_NOW);
    if(pCoreAttachPlugin(M64PLUGIN_INPUT, self) != M64ERR_SUCCESS) return -7;

    pCoreDoCommand(M64CMD_SET_FRAME_CALLBACK, 0, (void*)frame_cb);
    int zero = 0;
    pCoreDoCommand(M64CMD_CORE_STATE_SET, M64CORE_SPEED_LIMITER, &zero);

    pthread_create(&emu_thread, NULL, emu_main, NULL);
    wait_blocked();
    return emu_done ? -8 : 0;
}

void *h_rdram(void){
    return pDebugMemGetPointer(M64P_DBG_PTR_RDRAM);
}

unsigned h_frame(void){ return frame_no; }
int h_polls(void){ return poll_count; }

static void set_input(unsigned buttons, int x, int y){
    cur_input.Value = buttons & 0xFFFF;
    cur_input.X_AXIS = x;
    cur_input.Y_AXIS = y;
}

/* run n frames with this input; returns 0, or -1 if the emulator stopped */
int h_step(unsigned buttons, int x, int y, int n){
    set_input(buttons, x, y);
    for(int i = 0; i < n; i++) {
        release();
        wait_blocked();
        if(emu_done) return -1;
    }
    return 0;
}

int h_save(const char *path){
    pCoreDoCommand(M64CMD_STATE_SAVE, 1, (void*)path);
    release();
    wait_blocked();
    return emu_done ? -1 : 0;
}

int h_load(const char *path, unsigned frame){
    pCoreDoCommand(M64CMD_STATE_LOAD, 0, (void*)path);
    release();
    wait_blocked();
    frame_no = frame;
    return emu_done ? -1 : 0;
}
