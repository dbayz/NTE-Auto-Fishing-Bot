import pyautogui
import time
import threading
import tkinter as tk
import ctypes
import mss
import numpy as np

# ==========================================
# DISABLE WINDOWS DPI SCALING
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass
# ==========================================

# ==========================================
# BOT SETTINGS
FISH_WAIT_TIME = 7 
# ==========================================

bot_running = False
purchase_session_count = 0 

def log_message(message):
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, message + "\n")
    log_text.see(tk.END)
    log_text.config(state=tk.DISABLED)

def safety_delay(seconds):
    global bot_running
    end_time = time.time() + seconds
    while time.time() < end_time:
        if not bot_running: return False
        time.sleep(0.1)
    return True

def press_key(key, duration=0.2):
    pyautogui.keyDown(key)
    time.sleep(duration)
    pyautogui.keyUp(key)

def manage_inventory(screen_width, screen_height, sct):
    global bot_running, purchase_session_count
    
    purchase_session_count += 1
    log_message(f"\n>>> BAIT EMPTY! Auto-Inventory Session (#{purchase_session_count}) <<<")
    
    # --- STAGE 1: SELL FISH (Q) ---
    log_message("[1/3] Selling fish...")
    press_key('q')
    if not safety_delay(2): return 
    
    # Click Fish Market tab
    pyautogui.click(int(screen_width * 0.07), int(screen_height * 0.36)) 
    if not safety_delay(1): return
    
    # Click Quick Submit
    pyautogui.click(int(screen_width * 0.55), int(screen_height * 0.89))
    #  change delay to 1,5 sec
    if not safety_delay(1.5): return
    
    # Click Confirm
    pyautogui.click(int(screen_width * 0.61), int(screen_height * 0.66))
    if not safety_delay(1.0): return 
    # Add second click to prevent miss frame
    pyautogui.click(int(screen_width * 0.61), int(screen_height * 0.66)) 
    if not safety_delay(1.5): return
    
    # Click any empty area to close pop-up
    pyautogui.click(int(screen_width * 0.5), int(screen_height * 0.5))
    if not safety_delay(1): return
    
    press_key('esc') 
    if not safety_delay(2): return 
    
    # --- STAGE 2: CHECK & EQUIP BAIT (E) ---
    log_message("[2/3] Checking for bait...")
    press_key('e') # Open Bait Switch menu
    if not safety_delay(1.5): return
    
    # === SMART DETECTOR 1: CHECK FOR PINK BORDER (ACTIVE BAIT) ===
    box_x = int(screen_width * 0.35)
    box_y = int(screen_height * 0.45)
    box_w = int(screen_width * 0.06)
    box_h = int(screen_height * 0.10)
    bait_monitor = {"top": box_y, "left": box_x, "width": box_w, "height": box_h}
    
    img_bait = np.array(sct.grab(bait_monitor))
    b_p = img_bait[:, :, 0]
    g_p = img_bait[:, :, 1]
    r_p = img_bait[:, :, 2]
    
    # Pink color filter: Red dominant, Green/Blue lower
    pink_pixels = np.sum((r_p > 150) & (r_p > g_p + 30) & (r_p > b_p + 30))
    
    if pink_pixels > 50:
        log_message("Bait is already active (Pink Border). Skipping selection.")
    else:
        log_message("Selecting Universal Bait...")
        pyautogui.click(int(screen_width * 0.38), int(screen_height * 0.50))
        if not safety_delay(1.5): return
        
    # Click "Switch" or "Purchase"
    pyautogui.click(int(screen_width * 0.61), int(screen_height * 0.66))
    if not safety_delay(2): return 
    
    # === SMART DETECTOR 2: IS TACKLE SHOP OPEN? ===
    # Check if we were redirected to the shop (White pixel check)
    check_monitor = {"top": int(screen_height * 0.50), "left": int(screen_width * 0.85), "width": 10, "height": 10}
    img_check = np.array(sct.grab(check_monitor))
    avg_bgr = np.mean(img_check, axis=(0,1)) 
    
    if avg_bgr[0] > 180 and avg_bgr[1] > 180 and avg_bgr[2] > 180:
        log_message("[Info] Out of bait. Entering Tackle Shop...")
        
        log_message("Scanning store inventory...")
        
        # Grid coordinates (X, Y ratios) for top 9 slots
        slot_list = [
            (0.08, 0.28), (0.17, 0.28), (0.26, 0.28), # Row 1
            (0.08, 0.45), (0.17, 0.45), (0.26, 0.45), # Row 2
            (0.08, 0.62), (0.17, 0.62), (0.26, 0.62)  # Row 3
        ]
        
        target_found = False
        
        for px, py in slot_list:
            center_x = int(screen_width * px)
            center_y = int(screen_height * py)
            
            # Click item in the grid
            pyautogui.click(center_x, center_y)
            time.sleep(0.8) # UI Delay
            
            # --- Check Right Panel ---
            icon_x = int(screen_width * 0.76)
            icon_y = int(screen_height * 0.26)
            icon_w = int(screen_width * 0.05)
            icon_h = int(screen_height * 0.09)
            
            icon_monitor = {
                "top": icon_y - (icon_h // 2), 
                "left": icon_x - (icon_w // 2), 
                "width": icon_w, 
                "height": icon_h
            }
            img_icon = np.array(sct.grab(icon_monitor))
            
            b_i = img_icon[:, :, 0].astype(np.int16)
            g_i = img_icon[:, :, 1].astype(np.int16)
            r_i = img_icon[:, :, 2].astype(np.int16)
            
            # COLOR DETECTION LOGIC
            # A. Pink Bag: Red dominant + Blue present
            pink_bag = np.sum((r_i > 140) & (r_i > g_i + 30) & (b_i > 90))
            # B. Brown Pellets: Darker Red/Orange, low Blue
            brown_pellets = np.sum((r_i > 70) & (r_i < 160) & (r_i > g_i + 20) & (b_i < 100))
            # C. Anti-Purple (Rod III)
            purple_bg = np.sum((r_i > 120) & (b_i > 140) & (g_i < 90))
            # D. Anti-Gold (Rod IV)
            gold_bg = np.sum((r_i > 150) & (g_i > 110) & (b_i < 80))
            
            # E. Currency Check (Shells)
            price_x = int(screen_width * 0.85)
            price_y = int(screen_height * 0.82)
            price_w = int(screen_width * 0.04)
            price_h = int(screen_height * 0.037)
            
            price_monitor = {
                "top": price_y - (price_h // 2), 
                "left": price_x - (price_w // 2), 
                "width": price_w, 
                "height": price_h
            }
            img_price = np.array(sct.grab(price_monitor))
            b_h = img_price[:, :, 0].astype(np.int16)
            g_h = img_price[:, :, 1].astype(np.int16)
            r_h = img_price[:, :, 2].astype(np.int16)
            shell_pixels = np.sum((b_h > 150) & (g_h > 100) & (r_h < 120))
            
            # FINAL VALIDATION: Must be Pink Bag, Brown Pellets, NOT Gold/Purple, using Shells
            if pink_bag > 150 and brown_pellets > 50 and purple_bg < 200 and gold_bg < 200 and shell_pixels > 10:
                log_message(f"Target locked! Universal Bait found at grid ({px}, {py})")
                target_found = True
                break 
            else:
                log_message(f"Skipping ({px}, {py}) -> Pnk:{pink_bag} Brwn:{brown_pellets} Gld:{gold_bg} Shll:{shell_pixels}")
        
        if not target_found:
            log_message("[ERROR] Universal Bait not found! Safety shut down.")
            global bot_running
            bot_running = False
            return
            
        # --- PHASE 4: PURCHASE ---
        log_message("Purchasing bait (Max Quantity)...")
        pyautogui.click(int(screen_width * 0.90), int(screen_height * 0.88)) # Slider to Max
        if not safety_delay(1): return
        
        pyautogui.click(int(screen_width * 0.85), int(screen_height * 0.95)) # Purchase Button
        if not safety_delay(1.5): return 

        log_message("Confirming bulk purchase...")
        pyautogui.click(int(screen_width * 0.61), int(screen_height * 0.66)) # Confirm Button
        if not safety_delay(1.0): return
        # Add another click to prevent miss frame
        pyautogui.click(int(screen_width * 0.61), int(screen_height * 0.66)) # Confirm Button
        if not safety_delay(1.8): return 
        
        log_message("Closing reward summary...")
        empty_area_y = int(screen_height * 0.75) 
        for _ in range(3):
            pyautogui.click(int(screen_width * 0.5), empty_area_y) 
            time.sleep(0.3)
            
        if not safety_delay(1.0): return 
        
        log_message("Exiting Tackle Shop...")
        press_key('esc') 
        if not safety_delay(2.0): return 
        
        log_message("Equipping newly purchased bait...")
        press_key('e') 
        if not safety_delay(1.5): return

        # Verify active border again
        img_bait_v2 = np.array(sct.grab(bait_monitor))
        r_p2 = img_bait_v2[:, :, 2].astype(np.int16)
        g_p2 = img_bait_v2[:, :, 1].astype(np.int16)
        b_p2 = img_bait_v2[:, :, 0].astype(np.int16)
        pink_pixels_v2 = np.sum((r_p2 > 150) & (r_p2 > g_p2 + 30) & (r_p2 > b_p2 + 30))
        
        if pink_pixels_v2 > 50:
            log_message("Bait auto-equipped. Skipping selection.")
        else:
            pyautogui.click(int(screen_width * 0.38), int(screen_height * 0.50))
            if not safety_delay(1): return
        
        pyautogui.click(int(screen_width * 0.61), int(screen_height * 0.66)) # Switch Button
        if not safety_delay(1.5): return
        
    else:
        log_message("[3/3] Bait stock available. Successfully equipped!")
        
    log_message(">>> Inventory managed! Ready to fish. <<<")

def bot_logic():
    global bot_running
    
    log_message("\n>>> BOT PREPARATION <<<")
    log_message("PLEASE SWITCH TO THE GAME WINDOW NOW!")
    
    for i in range(5, 0, -1):
        if not bot_running: return 
        log_message(f"Starting in {i}...")
        time.sleep(1)
        
    if not bot_running: return

    screen_w, screen_h = pyautogui.size()
    log_message(f"Detected Resolution: {screen_w}x{screen_h}")
    
    # Tension bar ROI coordinates (Normalized for 1920x1080)
    roi_x = int(screen_w * (612 / 1920))
    roi_y = int(screen_h * (50 / 1080))
    roi_w = int(screen_w * (701 / 1920))
    roi_h = int(screen_h * (50 / 1080))
    center_y_roi = roi_h // 2

    with mss.MSS() as sct:
        try:
            while bot_running: 
                log_message("\n" + "="*30)
                log_message("--- Casting Line ---")
                
                # === AUTO-RECOVERY: CHECK FOR PREPARATION MENU ===
                start_btn_x = int(screen_w * 0.82)
                start_btn_y = int(screen_h * 0.87)
                btn_w = int(screen_w * 0.02)
                btn_h = int(screen_h * 0.03)
                
                btn_monitor = {
                    "top": start_btn_y - (btn_h // 2), 
                    "left": start_btn_x - (btn_w // 2), 
                    "width": btn_w, 
                    "height": btn_h
                }
                img_btn = np.array(sct.grab(btn_monitor))
                pixel_white_count = np.sum((img_btn[:,:,2]>200) & (img_btn[:,:,1]>200) & (img_btn[:,:,0]>200))
                
                # Trigger When go to Fish Preparations
                if pixel_white_count > ((btn_w * btn_h) * 0.5): 
                    log_message("[Recovery] Preparation menu detected!")
                    pyautogui.click(start_btn_x, start_btn_y)
                    time.sleep(6.0) 
                    press_key('f')
                    time.sleep(1.5)
                else:
                    press_key('f')
                    time.sleep(1.5) 
                
                # === OUT OF BAIT DETECTION (WHITE TEXT CHECK) ===
                banner_y = int(screen_h * 0.48)
                banner_h = int(screen_h * 0.04)
                box_left_x = int(screen_w * 0.35)
                box_right_x = int(screen_w * 0.60)
                box_width = int(screen_w * 0.05)
                
                mon_left = {"top": banner_y, "left": box_left_x, "width": box_width, "height": banner_h}
                mon_right = {"top": banner_y, "left": box_right_x, "width": box_width, "height": banner_h}
                
                img_l = np.array(sct.grab(mon_left))
                img_r = np.array(sct.grab(mon_right))
                
                white_px = np.sum((img_l[::2,::3,2]>240)&(img_l[::2,::3,1]>240)&(img_l[::2,::3,0]>240)) + \
                           np.sum((img_r[::2,::3,2]>240)&(img_r[::2,::3,1]>240)&(img_r[::2,::3,0]>240))
                
                if white_px > 8:
                    log_message("'Equip bait' warning detected!")
                    manage_inventory(screen_w, screen_h, sct)
                    continue 

                log_message(f"Waiting for bite ({FISH_WAIT_TIME - 1}s)...")
                if not safety_delay(FISH_WAIT_TIME - 1): break 

                log_message("Fish hooked! Reeling in...")
                press_key('f')

                if not safety_delay(1.0): break
                log_message("Mini-game started (Tension Bar)!")

                last_seen_bar = time.time() 
                bar_monitor = {"top": roi_y, "left": roi_x, "width": roi_w, "height": roi_h}
                
                while bot_running: 
                    img_np = np.array(sct.grab(bar_monitor))
                    bar_line = img_np[center_y_roi, :, :] 
                    
                    B = bar_line[:, 0].astype(np.int16)
                    G = bar_line[:, 1].astype(np.int16)
                    R = bar_line[:, 2].astype(np.int16)
                    
                    mask_yellow = (R > 160) & (G > 150) & (B < 130) & ((R - B) > 50)
                    mask_blue = (B > 160) & (G > 160) & (R < 140) & ((B - R) > 50)
                    
                    idx_yellow = np.where(mask_yellow)[0]
                    idx_blue = np.where(mask_blue)[0]
                    
                    pos_yellow = idx_yellow[-1] if len(idx_yellow) > 0 else -1
                    blue_pixels = idx_blue.tolist()
                    
                    if pos_yellow != -1 and len(blue_pixels) > 5:
                        last_seen_bar = time.time()
                    
                    if time.time() - last_seen_bar > 3.0:
                        log_message("Mini-game finished!")
                        pyautogui.keyUp('a')
                        pyautogui.keyUp('d')
                        break 

                    if pos_yellow != -1 and len(blue_pixels) > 0:
                        blue_center = sum(blue_pixels) // len(blue_pixels)
                        blue_width = max(blue_pixels) - min(blue_pixels)
                        deadzone = max(2, blue_width // 3) 
                        
                        if pos_yellow < (blue_center - deadzone):
                            pyautogui.keyUp('a')
                            pyautogui.keyDown('d')
                        elif pos_yellow > (blue_center + deadzone):
                            pyautogui.keyUp('d')
                            pyautogui.keyDown('a')
                        else:
                            pyautogui.keyUp('a')
                            pyautogui.keyUp('d')
                    else:
                        pyautogui.keyUp('a')
                        pyautogui.keyUp('d')
                        
                    time.sleep(0.005) 
                
                if not bot_running: break 
                
                log_message("Displaying results...")
                # Change Delay to 3 sec
                if not safety_delay(3): break
                
                log_message("Closing result window...")
                pyautogui.click(screen_w / 2, screen_h / 1.5)
                # Add second click
                pyautogui.click(screen_w / 2, screen_h / 1.5)
                if not safety_delay(1): break
                pyautogui.click(screen_w / 2, screen_h / 1.5)
                
                log_message("Next cast in 2 seconds...")
                if not safety_delay(2): break
                
        except Exception as e:
            log_message(f"Error: {str(e)}")
        finally:
            log_message(">>> BOT STOPPED <<<")
            pyautogui.keyUp('a')
            pyautogui.keyUp('d')
            pyautogui.keyUp('esc') 
            bot_running = False
            start_btn.config(state=tk.NORMAL)
            stop_btn.config(state=tk.DISABLED)

def start_click():
    global bot_running, purchase_session_count
    if not bot_running:
        bot_running = True
        purchase_session_count = 0 
        start_btn.config(state=tk.DISABLED)
        stop_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=bot_logic)
        thread.daemon = True 
        thread.start()

def stop_click():
    global bot_running
    if bot_running:
        log_message(">>> STOPPING BOT... <<<")
        log_message("(Waiting for current action to finish)")
        bot_running = False

# GUI INITIALIZATION
root = tk.Tk()
root.title("Auto Fishing Bot - NTE")
root.geometry("470x380") 
root.resizable(False, False)
root.attributes("-topmost", True) 

try:
    root.iconbitmap('icon.ico') 
except Exception:
    pass

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

start_btn = tk.Button(btn_frame, text="START", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=12, command=start_click)
start_btn.grid(row=0, column=0, padx=10)

stop_btn = tk.Button(btn_frame, text="STOP", bg="#f44336", fg="white", font=("Arial", 12, "bold"), width=12, state=tk.DISABLED, command=stop_click)
stop_btn.grid(row=0, column=1, padx=10)

console_frame = tk.Frame(root, bg="#1e1e1e", bd=2, relief=tk.SUNKEN)
console_frame.pack(padx=15, pady=5, fill=tk.BOTH, expand=True)

width = 45
header_text = (
    f"{'=' * width}\n"
    f"{'NTE AUTO FISHING BOT v1.2'.center(width)}\n"
    f"{'[Ultimate Day/Night Fishing]'.center(width)}\n"
    f"{'=' * width}"
)

header_label = tk.Label(console_frame, text=header_text, bg="#1e1e1e", fg="#00FF00", font=("Consolas", 9), justify=tk.CENTER)
header_label.pack(pady=(5, 0))

log_text = tk.Text(console_frame, width=50, height=8, font=("Consolas", 9), state=tk.DISABLED, bg="#1e1e1e", fg="#00FF00", bd=0, highlightthickness=0)
log_text.pack(padx=5, pady=(0, 5))

log_message("Status: Ready. Press START to begin.")
root.mainloop()
