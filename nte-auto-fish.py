import pyautogui
import time
import threading
import customtkinter as ctk
import tkinter as tk
import ctypes
import mss
import numpy as np
import os
import json
import cv2
import random

# ==========================================
# DISABLE WINDOWS DPI SCALING
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass
# ==========================================

CONFIG_FILE = "settings.json"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FishingBot:
    def __init__(self, root):
        self.root = root
        self.bot_running = False
        self.purchase_session_count = 0
        
        self.active_key_left = "a"
        self.active_key_right = "d"
        self.active_key_sell = "q"
        self.active_key_bait = "e"
        
        self.setup_ui()
        self.load_settings()

        try:
            import keyboard
            keyboard.add_hotkey('ctrl+alt', self.toggle_bot)
        except Exception:
            pass

    def setup_ui(self):
        self.root.title("NTE Auto Fishing Bot")
        self.root.geometry("600x520")
        self.root.resizable(False, False)

        try:
            self.root.iconbitmap('icon.ico') 
        except Exception:
            pass

        # === KEYBIND SETUP FRAME ===
        self.keybind_frame = ctk.CTkFrame(self.root)
        self.keybind_frame.pack(pady=10, padx=15, fill="x")

        # Variables
        self.var_key_left = tk.StringVar(value="A")
        self.var_key_right = tk.StringVar(value="D")
        self.var_key_sell = tk.StringVar(value="Q")
        self.var_key_bait = tk.StringVar(value="E")

        self.var_key_left.trace_add("write", lambda *a: self.format_key(self.var_key_left))
        self.var_key_right.trace_add("write", lambda *a: self.format_key(self.var_key_right))
        self.var_key_sell.trace_add("write", lambda *a: self.format_key(self.var_key_sell))
        self.var_key_bait.trace_add("write", lambda *a: self.format_key(self.var_key_bait))

        ctk.CTkLabel(self.keybind_frame, text="Keybind Setup", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=4, pady=(5, 10))

        ctk.CTkLabel(self.keybind_frame, text="Left (<-):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        ctk.CTkEntry(self.keybind_frame, textvariable=self.var_key_left, width=60, justify='center').grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(self.keybind_frame, text="Right (->):").grid(row=1, column=2, padx=10, pady=5, sticky="e")
        ctk.CTkEntry(self.keybind_frame, textvariable=self.var_key_right, width=60, justify='center').grid(row=1, column=3, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(self.keybind_frame, text="Sell Fish:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        ctk.CTkEntry(self.keybind_frame, textvariable=self.var_key_sell, width=60, justify='center').grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(self.keybind_frame, text="Bait Menu:").grid(row=2, column=2, padx=10, pady=5, sticky="e")
        ctk.CTkEntry(self.keybind_frame, textvariable=self.var_key_bait, width=60, justify='center').grid(row=2, column=3, padx=10, pady=5, sticky="w")

        # Make columns responsive
        for i in range(4):
            self.keybind_frame.grid_columnconfigure(i, weight=1)

        # === MIDDLE SECTION ===
        self.middle_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.middle_frame.pack(pady=5, padx=15, fill="x")
        self.middle_frame.grid_columnconfigure(0, weight=1)
        self.middle_frame.grid_columnconfigure(1, weight=1)

        # Output Visualizer
        self.output_frame = ctk.CTkFrame(self.middle_frame)
        self.output_frame.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

        ctk.CTkLabel(self.output_frame, text="Output Visualizer", font=("Arial", 12)).pack(pady=5)
        
        self.btn_vis_frame = ctk.CTkFrame(self.output_frame, fg_color="transparent")
        self.btn_vis_frame.pack(pady=10)

        self.vis_left = ctk.CTkButton(self.btn_vis_frame, text="A", width=60, height=60, font=("Arial", 24, "bold"), fg_color="#1f538d", hover=False)
        self.vis_left.grid(row=0, column=0, padx=10)

        self.vis_right = ctk.CTkButton(self.btn_vis_frame, text="D", width=60, height=60, font=("Arial", 24, "bold"), fg_color="#1f538d", hover=False)
        self.vis_right.grid(row=0, column=1, padx=10)
        
        ctk.CTkLabel(self.output_frame, text="Tips : CTRL + ALT to start / stop bot", font=("Arial", 10, "italic"), text_color="gray").pack(side="bottom", pady=(0, 10))

        # Controls
        self.control_frame = ctk.CTkFrame(self.middle_frame)
        self.control_frame.grid(row=0, column=1, padx=(5, 0), sticky="nsew")

        self.status_label = ctk.CTkLabel(self.control_frame, text="Status: Ready", font=("Arial", 14))
        self.status_label.pack(pady=15)

        self.start_btn = ctk.CTkButton(self.control_frame, text="Start Fishing", font=("Arial", 16, "bold"), fg_color="#2FA572", hover_color="#1D7B50", height=45, command=self.start_click)
        self.start_btn.pack(pady=5, padx=20, fill="x")

        self.stop_btn = ctk.CTkButton(self.control_frame, text="Stop", font=("Arial", 14, "bold"), fg_color="#E03131", hover_color="#C92A2A", height=35, state="disabled", command=self.stop_click)
        self.stop_btn.pack(pady=5, padx=20, fill="x")

        # === LOG FRAME ===
        self.log_frame = ctk.CTkFrame(self.root)
        self.log_frame.pack(pady=10, padx=15, fill="both", expand=True)

        self.log_text = ctk.CTkTextbox(self.log_frame, font=("Consolas", 11), fg_color="#1e1e1e", text_color="#00FF00", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.configure(state="disabled")

        self.log_message("System initialized. Ready to Fishing - Good Luck!")

    def format_key(self, var):
        val = var.get()
        if len(val) > 0 and val != val[-1].upper():
            var.set(val[-1].upper())
        # Update visualizer text dynamically
        if hasattr(self, 'vis_left') and var == self.var_key_left:
            self.vis_left.configure(text=var.get())
        if hasattr(self, 'vis_right') and var == self.var_key_right:
            self.vis_right.configure(text=var.get())

    def update_visualizer(self, key, is_down):
        color = "#2FA572" if is_down else "#1f538d"
        if key == self.active_key_left:
            self.vis_left.configure(fg_color=color)
        elif key == self.active_key_right:
            self.vis_right.configure(fg_color=color)

    def load_settings(self):
        config_data = {
            "key_left": "A",
            "key_right": "D",
            "key_sell": "Q",
            "key_bait": "E"
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config_data.update(json.load(f))
            except Exception:
                pass
        self.var_key_left.set(config_data["key_left"])
        self.var_key_right.set(config_data["key_right"])
        self.var_key_sell.set(config_data["key_sell"])
        self.var_key_bait.set(config_data["key_bait"])
        
        # Manually update visualizer text on load
        if hasattr(self, 'vis_left'):
            self.vis_left.configure(text=self.var_key_left.get())
        if hasattr(self, 'vis_right'):
            self.vis_right.configure(text=self.var_key_right.get())

    def save_settings(self):
        try:
            new_config = {
                "key_left": self.var_key_left.get(),
                "key_right": self.var_key_right.get(),
                "key_sell": self.var_key_sell.get(),
                "key_bait": self.var_key_bait.get()
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(new_config, f, indent=4)
            self.log_message("[Info] Settings auto-saved to file!") 
        except Exception as e:
            self.log_message(f"[ERROR] Failed to save: {str(e)}")

    def log_message(self, message):
        self.root.after(0, self._insert_log, message)

    def _insert_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.configure(text=f"Status: {message}"))

    def safety_delay(self, seconds):
        end_time = time.time() + seconds
        while time.time() < end_time:
            if not self.bot_running: return False
            time.sleep(0.1)
        return True

    def press_hold(self, key):
        pyautogui.keyDown(key)
        if key in [self.active_key_left, self.active_key_right]:
            self.root.after(0, self.update_visualizer, key, True)

    def release_key(self, key):
        pyautogui.keyUp(key)
        if key in [self.active_key_left, self.active_key_right]:
            self.root.after(0, self.update_visualizer, key, False)

    def press_key(self, key, duration=0.2):
        self.press_hold(key)
        time.sleep(duration)
        self.release_key(key)

    def human_move_and_click(self, x, y):
        target_x = int(x) + random.randint(-5, 5)
        target_y = int(y) + random.randint(-5, 5)
        move_duration = random.uniform(0.15, 0.35)
        pyautogui.moveTo(target_x, target_y, duration=move_duration, tween=pyautogui.easeInOutQuad)
        time.sleep(random.uniform(0.05, 0.15))
        pyautogui.click()

    def click_and_wait(self, x, y, delay):
        self.human_move_and_click(x, y)
        return self.safety_delay(delay)

    def start_click(self):
        self.save_settings()
        
        self.active_key_left = self.var_key_left.get().lower()
        self.active_key_right = self.var_key_right.get().lower()
        self.active_key_sell = self.var_key_sell.get().lower()
        self.active_key_bait = self.var_key_bait.get().lower()
        
        if not self.bot_running:
            self.bot_running = True
            self.purchase_session_count = 0 
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.update_status("Running...")
            
            thread = threading.Thread(target=self.bot_logic)
            thread.daemon = True 
            thread.start()

    def stop_click(self):
        if self.bot_running:
            self.update_status("Stopping...")
            self.log_message(">>> STOPPING BOT... <<<")
            self.log_message("(Waiting for current action to finish)")
            self.bot_running = False

    def toggle_bot(self):
        if self.bot_running:
            self.stop_click()
        else:
            self.start_click()

    def on_stop_cleanup(self):
        self.log_message(">>> BOT STOPPED <<<")
        self.update_status("Ready")
        
        self.release_key(self.active_key_left)
        self.release_key(self.active_key_right)
        self.release_key('esc') 
        
        self.bot_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def get_hsv_mask(self, img, lower_hsv, upper_hsv):
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv_img, np.array(lower_hsv), np.array(upper_hsv))
        return np.sum(mask > 0)

    def manage_inventory(self, screen_width, screen_height, sct):
        self.purchase_session_count += 1
        self.log_message(f"\n>>> BAIT EMPTY! Auto-Inventory Session (#{self.purchase_session_count}) <<<")
        
        self.log_message("[1/3] Selling fish...")
        self.press_key(self.active_key_sell)
        if not self.safety_delay(2): return 
        
        if not self.click_and_wait(screen_width * 0.07, screen_height * 0.36, 1.0): return # Fish Market tab
        if not self.click_and_wait(screen_width * 0.55, screen_height * 0.89, 1.5): return # Quick Submit
        if not self.click_and_wait(screen_width * 0.61, screen_height * 0.66, 1.0): return # Confirm
        if not self.click_and_wait(screen_width * 0.5, screen_height * 0.5, 1.0): return # Close pop-up
        
        self.press_key('esc') 
        if not self.safety_delay(2): return 
        
        self.log_message("[2/3] Checking for bait...")
        self.press_key(self.active_key_bait) # Open Bait Switch menu
        if not self.safety_delay(1.5): return
        
        box_x = int(screen_width * 0.35)
        box_y = int(screen_height * 0.45)
        box_w = int(screen_width * 0.06)
        box_h = int(screen_height * 0.10)
        bait_monitor = {"top": box_y, "left": box_x, "width": box_w, "height": box_h}
        
        img_bait = np.array(sct.grab(bait_monitor))
        
        # HSV check for Pink Border
        pink_pixels = self.get_hsv_mask(img_bait, [140, 50, 150], [170, 255, 255])
        
        if pink_pixels > 50:
            self.log_message("Bait is already active (Pink Border). Skipping selection.")
        else:
            self.log_message("Selecting Universal Bait...")
            if not self.click_and_wait(screen_width * 0.38, screen_height * 0.50, 1.5): return
            
        if not self.click_and_wait(screen_width * 0.61, screen_height * 0.66, 2.0): return # Switch/Purchase
        
        check_monitor = {"top": int(screen_height * 0.50), "left": int(screen_width * 0.85), "width": 10, "height": 10}
        img_check = np.array(sct.grab(check_monitor))
        avg_bgr = np.mean(img_check, axis=(0,1)) 
        
        if avg_bgr[0] > 180 and avg_bgr[1] > 180 and avg_bgr[2] > 180:
            self.log_message("[Info] Out of bait. Entering Tackle Shop...")
            self.log_message("Scanning store inventory...")
            
            slot_list = [
                (0.08, 0.28), (0.17, 0.28), (0.26, 0.28),
                (0.08, 0.45), (0.17, 0.45), (0.26, 0.45),
                (0.08, 0.62), (0.17, 0.62), (0.26, 0.62)
            ]
            
            target_found = False
            for px, py in slot_list:
                center_x = int(screen_width * px)
                center_y = int(screen_height * py)
                
                self.human_move_and_click(center_x, center_y)
                time.sleep(0.5) 
                
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
                
                pink_bag = self.get_hsv_mask(img_icon, [140, 50, 100], [170, 255, 255])
                brown_pellets = self.get_hsv_mask(img_icon, [10, 50, 50], [25, 255, 200])
                
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
                shell_pixels = self.get_hsv_mask(img_price, [80, 50, 100], [110, 255, 255])
                
                if pink_bag > 100 and brown_pellets > 50 and shell_pixels > 10:
                    self.log_message(f"Target locked! Universal Bait found at grid ({px}, {py})")
                    target_found = True
                    break 
                else:
                    self.log_message(f"Skipping ({px}, {py}) -> Pink:{pink_bag} Brown:{brown_pellets} Shell:{shell_pixels}")
            
            if not target_found:
                self.log_message("[ERROR] Universal Bait not found! Safety shut down.")
                self.bot_running = False
                return
                
            self.log_message("Purchasing bait (Max Quantity)...")
            if not self.click_and_wait(screen_width * 0.90, screen_height * 0.88, 1.5): return # Slider
            if not self.click_and_wait(screen_width * 0.85, screen_height * 0.95, 1.5): return # Purchase
            
            self.log_message("Confirming bulk purchase...")
            if not self.click_and_wait(screen_width * 0.61, screen_height * 0.66, 1.5): return # Confirm

            
            self.log_message("Closing reward summary...")
            empty_area_y = int(screen_height * 0.75) 
            for _ in range(3):
                self.human_move_and_click(screen_width * 0.5, empty_area_y) 
                time.sleep(0.3)
                
            if not self.safety_delay(1.0): return 
            
            self.log_message("Exiting Tackle Shop...")
            self.press_key('esc') 
            if not self.safety_delay(2.0): return 
            
            self.log_message("Equipping newly purchased bait...")
            self.press_key('e') 
            if not self.safety_delay(1.5): return

            img_bait_v2 = np.array(sct.grab(bait_monitor))
            pink_pixels_v2 = self.get_hsv_mask(img_bait_v2, [140, 50, 150], [170, 255, 255])
            
            if pink_pixels_v2 > 50:
                self.log_message("Bait auto-equipped. Skipping selection.")
            else:
                if not self.click_and_wait(screen_width * 0.38, screen_height * 0.50, 1.0): return
            
            if not self.click_and_wait(screen_width * 0.61, screen_height * 0.66, 1.5): return # Switch Button
            
        else:
            self.log_message("[3/3] Bait stock available. Successfully equipped!")
            
        self.log_message(">>> Inventory Managed! Ready to fish. <<<")

    def bot_logic(self):
        KEY_LEFT = self.active_key_left
        KEY_RIGHT = self.active_key_right
        
        self.log_message("\n>>> BOT PREPARATION <<<")
        self.log_message(f"Active Keybinds -> LEFT: [{KEY_LEFT.upper()}], RIGHT <-: [{KEY_RIGHT.upper()}]")
        self.log_message(">>> SWITCHING TO THE GAME WINDOWS :) <<<")
        
        try:
            for i in range(5, 0, -1):
                if not self.bot_running: return 
                self.log_message(f"Starting in {i}...")
                if not self.safety_delay(1): return 
                
            if not self.bot_running: return

            screen_w, screen_h = pyautogui.size()
            self.log_message(f"Detected Resolution: {screen_w}x{screen_h}")
            
            # Force focus on the game window by clicking an empty area (top center-left)
            self.log_message("Focusing game window...")
            self.human_move_and_click(screen_w * 0.3, screen_h * 0.1)
            time.sleep(0.5)
            
            roi_x = int(screen_w * (612 / 1920))
            roi_y = int(screen_h * (50 / 1080))
            roi_w = int(screen_w * (701 / 1920))
            roi_h = int(screen_h * (50 / 1080))
            center_y_roi = roi_h // 2

            with mss.MSS() as sct:
                while self.bot_running: 
                    self.log_message("\n" + "="*30)
                    self.log_message("--- Casting Line ---")
                    
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
                    
                    if pixel_white_count > ((btn_w * btn_h) * 0.5): 
                        self.log_message("[Recovery] Preparation menu detected!")
                        self.human_move_and_click(start_btn_x, start_btn_y)
                        if not self.safety_delay(6.0): break 
                        self.press_key('f')
                        if not self.safety_delay(1.5): break
                    else:
                        self.press_key('f')
                        if not self.safety_delay(1.5): break 
                    
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
                        self.log_message("'Equip bait' warning detected!")
                        self.manage_inventory(screen_w, screen_h, sct)
                        if not self.bot_running: break
                        continue 

                    self.log_message("Spamming 'F' until fish hooks...")
                    bar_monitor = {"top": roi_y, "left": roi_x, "width": roi_w, "height": roi_h}
                    
                    minigame_started = False
                    while self.bot_running and not minigame_started:
                        self.press_key('f', duration=0.05)
                        
                        # Random tempo between 0.15s and 0.4s
                        sleep_time = random.uniform(0.15, 0.4)
                        end_sleep = time.time() + sleep_time
                        
                        # Wait and check for tension bar at the same time
                        while time.time() < end_sleep:
                            if not self.bot_running: break
                            
                            img_np = np.array(sct.grab(bar_monitor))
                            bar_line = img_np[center_y_roi, :, :] 
                            B = bar_line[:, 0].astype(np.int16)
                            G = bar_line[:, 1].astype(np.int16)
                            R = bar_line[:, 2].astype(np.int16)
                            mask_blue = (B > 160) & (G > 160) & (R < 140) & ((B - R) > 50)
                            mask_yellow = (R > 160) & (G > 150) & (B < 130) & ((R - B) > 50)
                            
                            # Ensure BOTH the blue safe zone AND yellow cursor are present to avoid triggering on blue sky
                            if len(np.where(mask_blue)[0]) > 5 and len(np.where(mask_yellow)[0]) > 0:
                                minigame_started = True
                                break
                                
                            time.sleep(0.05)

                    if not self.bot_running: break
                    self.log_message("Fish hooked! Mini-game started (Tension Bar)!")

                    last_seen_bar = time.time()
                    
                    while self.bot_running: 
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
                            self.log_message("Mini-game finished!")
                            self.release_key(KEY_LEFT)
                            self.release_key(KEY_RIGHT)
                            break 

                        if pos_yellow != -1 and len(blue_pixels) > 0:
                            blue_center = sum(blue_pixels) // len(blue_pixels)
                            blue_width = max(blue_pixels) - min(blue_pixels)
                            deadzone = max(2, blue_width // 3) 
                            
                            if pos_yellow < (blue_center - deadzone):
                                self.release_key(KEY_LEFT)
                                self.press_hold(KEY_RIGHT)
                            elif pos_yellow > (blue_center + deadzone):
                                self.release_key(KEY_RIGHT)
                                self.press_hold(KEY_LEFT)
                            else:
                                self.release_key(KEY_LEFT)
                                self.release_key(KEY_RIGHT) 
                        else:
                            self.release_key(KEY_LEFT)
                            self.release_key(KEY_RIGHT) 
                            
                       
                        time.sleep(0.008)
                    
                    if not self.bot_running: break 
                    
                    self.log_message("Displaying results...")
                    if not self.safety_delay(1.5): break
                    
                    self.log_message("Closing result window...")
                    self.human_move_and_click(screen_w / 2, screen_h / 1.5)
                    self.human_move_and_click(screen_w / 2, screen_h / 1.5)

                    self.human_move_and_click(screen_w / 2, screen_h / 1.5)
                    
                    self.log_message("Next cast in seconds...")
                    if not self.safety_delay(0.8): break
                    
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
        finally:
            self.root.after(0, self.on_stop_cleanup)

if __name__ == "__main__":
    root = ctk.CTk()
    app = FishingBot(root)
    root.mainloop()
