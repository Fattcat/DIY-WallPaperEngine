import ctypes
import ctypes.wintypes
import time

user32 = ctypes.windll.user32

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)

def get_class(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value

def get_title(hwnd):
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    return buf.value

# ──────────────────────────────────────────────
# 1. DIAGNOSTIKA – vypíše celý strom okien Progmanu
# ──────────────────────────────────────────────
def dump_progman_tree():
    progman = user32.FindWindowW("Progman", None)
    print(f"Progman: {progman:#010x}  class='{get_class(progman)}'  title='{get_title(progman)}'")

    child_list = []
    @EnumWindowsProc
    def collect_children(hwnd, _):
        child_list.append(hwnd)
        return True

    # Potomkovia Progmanu
    user32.EnumChildWindows(progman, collect_children, 0)
    for h in child_list:
        print(f"  child {h:#010x}  class='{get_class(h)}'  title='{get_title(h)}'")

    # Všetky top-level WorkerW okná
    print("\n--- Všetky top-level WorkerW ---")
    @EnumWindowsProc
    def find_all_ww(hwnd, _):
        if get_class(hwnd) == "WorkerW":
            print(f"  WorkerW {hwnd:#010x}  visible={bool(user32.IsWindowVisible(hwnd))}  title='{get_title(hwnd)}'")
            # Potomkovia tohto WorkerW
            @EnumWindowsProc
            def ww_children(ch, _):
                print(f"    child {ch:#010x}  class='{get_class(ch)}'")
                return True
            user32.EnumChildWindows(hwnd, ww_children, 0)
        return True

    user32.EnumWindows(find_all_ww, 0)

# ──────────────────────────────────────────────
# 2. HLAVNÁ FUNKCIA – 3 fallback stratégie
# ──────────────────────────────────────────────
def find_wallpaper_workerw():
    progman = user32.FindWindowW("Progman", None)
    if not progman:
        raise RuntimeError("Progman nenájdený")

    # Pokus spawniť WorkerW – skús viackrát s čakaním
    for attempt in range(3):
        result = ctypes.wintypes.DWORD(0)
        user32.SendMessageTimeoutW(
            progman, 0x052C, 0, 0,
            0x0002,   # SMTO_ABORTIFHUNG
            2000,
            ctypes.byref(result)
        )
        time.sleep(0.3)

        # --- Stratégia A (klasická) ---
        found = ctypes.wintypes.HWND(0)

        @EnumWindowsProc
        def enum_cb(hwnd, _):
            defview = user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
            if defview:
                ww = user32.FindWindowExW(None, hwnd, "WorkerW", None)
                if ww:
                    found.value = ww
            return True

        user32.EnumWindows(enum_cb, 0)
        if found.value:
            print(f"[A] Nájdený cez SHELLDLL_DefView sibling: {found.value:#010x}")
            return found.value

    # --- Stratégia B – hľadaj WorkerW priamo ako potomka Progmanu ---
    ww = user32.FindWindowExW(progman, None, "WorkerW", None)
    if ww:
        print(f"[B] WorkerW potomok Progmanu: {ww:#010x}")
        return ww

    # --- Stratégia C – prvý viditeľný WorkerW bez SHELLDLL_DefView ---
    candidates = []

    @EnumWindowsProc
    def find_visible_ww(hwnd, _):
        if get_class(hwnd) == "WorkerW" and user32.IsWindowVisible(hwnd):
            defview = user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
            if not defview:
                candidates.append(hwnd)
        return True

    user32.EnumWindows(find_visible_ww, 0)
    if candidates:
        print(f"[C] Fallback WorkerW (bez SHELLDLL_DefView): {candidates[0]:#010x}")
        return candidates[0]

    raise RuntimeError("WorkerW nenájdený ani po 3 pokusoch – spusti dump_progman_tree() pre diagnostiku")


if __name__ == "__main__":
    print("=" * 50)
    print("DIAGNOSTIKA STROMU OKIEN")
    print("=" * 50)
    dump_progman_tree()

    print("\n" + "=" * 50)
    print("HĽADÁM TAPETA WorkerW")
    print("=" * 50)
    try:
        hwnd = find_wallpaper_workerw()
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        print(f"\n✓ WorkerW HWND = {hwnd:#010x}")
        print(f"  Rozmer: {rect.right - rect.left} x {rect.bottom - rect.top} px")
    except RuntimeError as e:
        print(f"\n✗ {e}")
