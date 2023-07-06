# Welcome to lights.py! Please set your network settings here:
NETWORK_NAME = ""
NETWORK_PASSWORD = ""

# This will be added to your setup.json file

import tft_buttons
import tft_config
import utime
import vga2_8x16 as font
import st7789
import hue
import os
import network
import json
import sys
import urequests


# print(os.stat("hue.py"))

# check if file exists featur to check if first time use
# add philips hue

tft = tft_config.config(3)

buttons = tft_buttons.Buttons()

if buttons.name == 'tdisplay_esp32':
    left_button = buttons.left
    right_button = buttons.right

elif buttons.name == 'tdisplay_rp2040':
    left_button = buttons.left
    right_button = buttons.right

elif buttons.name == 't-display-s3':
    left_button = buttons.left
    right_button = buttons.right

elif buttons.name == 'ws_pico_114':
    left_button = buttons.key3
    right_button = buttons.key2

elif buttons.name == 'ws_pico_13':
    left_button = buttons.y
    right_button = buttons.a

elif buttons.name == 'ws_pico_2':
    left_button = buttons.key2
    right_button = buttons.key1

elif buttons.name == 'wio_terminal':
    left_button = buttons.center
    right_button = buttons.button1

elif buttons.name == 't-dongle-s3':
    left_button = buttons.button
    right_button = buttons.button
    
def center(text):
    """Show text in the center of the screen"""
    length = len(text)
    tft.text(
        font,
        text,
        tft.width() // 2 - length // 2 * font.WIDTH,
        tft.height() // 2 - font.HEIGHT,
        st7789.WHITE,
        st7789.BLACK)
    
def refresh_screen():
    """Refreshes screen so new conten can be displayed"""
    tft.deinit()
    tft.init()
#     tft.fill(0x000)

def soft_refresh_screen():
    """Removes everything from screen by drawing a black square over the screen"""
    tft.fill(0x000)
    
# Check if path exists.
# Works for relative and absolute path.
def path_exists(path):
    parent = ""  # parent folder name
    name = path  # name of file/folder

    # Check if file/folder has a parent folder
    index = path.rstrip('/').rfind('/')
    if index >= 0:
        index += 1
        parent = path[:index-1]
        name = path[index:]

    # Searching with iterator is more efficient if the parent contains lost of files/folders
    # return name in uos.listdir(parent)
    return any((name == x[0]) for x in uos.ilistdir(parent))
    
def truncate_string(text, length, suffix='...'):
    if len(text) <= length:
        return text
    else:
        return text[:length-len(suffix)] + suffix
    
def rgb_to_hex(r, g, b):
    """Converts r, g, b to a HEX color. Does not include the hashtag"""
    return ('{:X}{:X}{:X}').format(r, g, b)

def rgb_to_xy(rgb):
    r = float(rgb[0])
    g = float(rgb[1])
    b = float(rgb[2])
    X = 0.412453 * r + 0.357580 * g + 0.180423 * b
    Y = 0.212671 * r + 0.715160 * g + 0.072169 * b
    Z = 0.019334 * r + 0.119193 * g + 0.950227 * b
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    return x, y

def hexa_to_xy(hexa):
    rgb = hexa.lstrip('#')
    rgb = tuple(int(rgb[i:i + 2], 16) for i in (0, 2, 4))
    return rgb_to_xy(rgb=rgb)
        
def scroll_menu(options, selector_index = 0, is_rerun = False, start_index = 0):
#     refresh_screen()
#     tft.init()
    soft_refresh_screen()
    utime.sleep(0.3)

#     if is_rerun == False:
#         tft.fill(0x000)
    
    last_height = 10
    index = start_index
    if len(options) == 0:
        center("No options!")
        return 0
    for option in options:
        index += 1
        if last_height + 20 <= tft.height() and index <= len(options):
            if index -1 == selector_index:
                text_input = tft.text(font, f"> [{index}] {truncate_string(options[index-1], 30, suffix='...')}", 10, last_height, 0xef476f)
                current_selected_item = index-1
                if last_height + 20  >= tft.height():
                    start_index = index
            else:
                text_input = tft.text(font, f"[{index}] {truncate_string(options[index-1], 30, suffix='...')}", 10, last_height)
            last_height += 20
    check_button = True
    while check_button == True:
        if left_button.value() == 0:
            if len(options) <= selector_index + 1:
                selector_index = 0
                start_index = 0
            else:
                selector_index += 1
#             refresh_screen()
            return scroll_menu(options, selector_index, True, start_index)
        elif right_button.value() == 0:
            check_button = False
            refresh_screen()
            return current_selected_item
        
def long_text(text: str):
    refresh_screen()

    last_height = 10
    last_width = 0
    special_chars = [" ", ".", "!", "?", ","]
    text_array = text.split(" ")
    index = 0

    for word in text_array:
        letter_index = 0
        if word == "\n":
            last_height += 20
            last_width = 0
            continue
        for letter in word:
            if last_width + 20 >= tft.width():
                if letter not in special_chars or text_array[index + 1][0] not in special_chars:
                    if letter_index != 0 and letter_index != len(word):
                        tft.text(font, "-", last_width, last_height)
                
                    last_height += 20
                    last_width = 10
                    tft.text(font, letter, 0, last_height)
            else:
                tft.text(font, f"{letter} ", last_width, last_height)
                last_width += 10
            letter_index += 1
        
        last_width += 5
        index += 1
        
def settings():
    REQUEST_HEADERS = {
        "Cache-Control": "no-cache",
        "Expires": "0"
    }
    settings_menu = ["Zoek naar updates", "<--"]
    choice = scroll_menu(settings_menu)
    if choice == 0:
        center("Zoeken naar updates...")
        response = urequests.get(
            "https://raw.githubusercontent.com/dante-nl/lovehue-remote/main/version.json", headers=REQUEST_HEADERS)
        if response.status_code != 200:
            soft_refresh_screen()
            long_text(f"Kon niet naar update zoeken, foutcode {response.status_code}")
            return
    
        RequestText = response.text
        data = json.loads(RequestText)
        if data["version"] != "1.0.0":
            r = urequests.get(
                "https://raw.githubusercontent.com/dante-nl/lovehue-remote/main/lights.py", headers=REQUEST_HEADERS)
            if r.status_code != 200:
                sof_refresh_screen()
                long_text(f"Kon update niet downloaden, foutcode {r.status_code}")
                return
            try:
                open(__file__, 'wb').write(r.content)
            except Exception as e:
                soft_refresh_screen()
                long_text(f"Kon bestand ({__file__}) niet overschrijven, fout: {str(e)}")
                return
            
            soft_refresh_screen()
            center("Update succesvol!")
            tft.text(font, f"^ Herstart apparaat", 10, 10)
            sys.exit(0)
        else:
            soft_refresh_screen()
            center("Geen updates!")
            utime.sleep(10)
            return
    elif choice == 1:
        return
                      
def room_selection(bridge: bridge, room = None):
    center("Laden...")
    if room == None:
        choices = ["[Instellingen]"]
        rooms_array = []
        rooms = bridge.getGroups()
        for room in rooms:
            choices.append(rooms[room])
            rooms_array.append(room)
        room = scroll_menu(choices)
        if room == 0:
            settings()
            room_selection(bridge)
            return
        room = rooms_array[room -1]
        center("Laden...")
    room_data = bridge.getGroup(room)
    
    print(room_data)
# 
# # Listing names of lights in room. Perhaps useful later.
# #     for light in room_data["lights"]:
# #         print(bridge.getLight(light)["name"])
#     print(room_data)
    soft_refresh_screen()
    if room_data["state"]["any_on"] == True:
        first_option = "Zet uit"
    else:
        first_option = "Zet aan"
    options = [first_option,"Verander helderheid", "Speel animatie", "<--"]
    chosen_option = scroll_menu(options)
    if chosen_option == 0:
        if room_data["state"]["any_on"] == True:
            # turn off
            bridge.setGroup(room, on=False, transitiontime=2)
        else:
            # turn on
            bridge.setGroup(room, on=True, bri=255, transitiontime=2)
        room_selection(bridge, room=room)
    elif chosen_option == 1:
        # set brightness
        brightness_options = ["0%", "25%", "50%", "75%", "100%", "<--"]
        brightness_option = scroll_menu(brightness_options)
        if brightness_option == 0:
            # 0%
            bridge.setGroup(room, on=False, transitiontime=2)
            room_selection(bridge, room=room)
            return
        if brightness_option == 1:
            # 25%
            brightness = 25
        if brightness_option == 2:
            # 50%
            brightness = 50
        if brightness_option == 3:
            # 75%
            brightness = 75
        if brightness_option == 4:
            # 100%
            brightness = 100
#         print(255*(brightness/100))
        brightness = round(255*(brightness/100))
#         print(room)
        bridge.setGroup(room, on=True, bri=brightness, transitiontime=2)
#         print("done")
        room_selection(bridge, room=room)
        return

    elif chosen_option == 2:
        # play animation
#         print(hexa_to_xy("007aff"))
#         bridge.setGroup(room, on=True, xy=hexa_to_xy("007aff"), transitiontime=2)
#         room_selection(bridge, room=room)

#         files = [f for f in os.listdir('.') if os.path.isfile(f)]
        files = os.listdir()
        current_item = 0
        animation_list = []
        animations = []
        for f in files:
            # do something
            if f.endswith(".lhad"):
                with open(f) as dataFile:
                    f_json = json.load(dataFile)
                current_item += 1
                try:
                    animation_name = f_json["name"]
#                     print(f"{colors.OKCYAN}[{current_item}] {animation_name} {colors.END}")
                except KeyError:
#                     print(f"{colors.FAIL}[{current_item}] Invalid animation file ({f}) {colors.END}")
                    pass
                animation_list.append(f)
                animations.append(animation_name)
            else:
                pass
        selected_option = scroll_menu(animations)
        
        with open(animation_list[selected_option]) as dataFile:
            animation_json = json.load(dataFile)
            # As it uses JSON syntax, we can use json.load()
        try:
            animation_name = animation_json["name"]
            animation_colors = animation_json["colors"]
            # Try if animation is valid
        except KeyError:
            center("Ongeldig animatie bestand.")
            utime.sleep(5)
            room_selection(bridge, room=room)
            return False
            # Invalid file

        # repeat_times = input("How many times repeat?")
        total_time = 0
        current_item = 0        
        tft.text(font, f"< Stop animatie (ingedrukt houden)", 10, 10)
        center("Animatie aan het spelen")

        max_lenght = len(animation_json["colors"])
        current_item = 0
        current_number = 1
        execute_code = True
        
        if room_data["state"]["any_on"] == False:
            # turn off
            bridge.setGroup(room, on=True, bri=255, transitiontime=2)
            room_data["action"]["bri"] = 255
            
        
        while execute_code == True:
            # for _ in range(int(repeat_times)):
            for __ in range(max_lenght):
                if left_button.value() == 0:
                    soft_refresh_screen()
                    center("Animatie stopgezet")
                    execute_code = False
                    utime.sleep(5)
                    soft_refresh_screen()
                    room_selection(bridge, room=room)
                    return
                # Checking what data is set
                try:
                    animation_json["colors"][current_item]["color"]
                    from_memory = True
                except KeyError:
                    animation_json["colors"][current_item]["color"] = lamp.hue
                    from_memory = False
                # ^ If color value is not set, continue with current color

                try:
                    animation_json["colors"][current_item]["brightness"]
                except KeyError:
                    animation_json["colors"][current_item]["brightness"] = room_data["action"]["bri"] / 254 * 100
                # ^ If brightness value is not set, continue with current brightness
                
                try:
                    animation_json["colors"][current_item]["time_until_next"]
                except KeyError:
                    animation_json["colors"][current_item]["time_until_next"] = 5
                # ^ If time_until_next value is not set, continue with defualt (5 seconds)


                try:
                    # If using default color value
                    if from_memory == True:
#                                     lamp.set_color(hexa=animation_json["colors"][current_item]["color"].replace("#", ""))
                        bridge.setGroup(room, on=True, xy=hexa_to_xy(animation_json["colors"][current_item]["color"].replace("#", "")), transitiontime=2)
                        # huesdk does not accept the hashtag, removing it here and setting color
                    else:
#                                     lamp.set_color(hue=animation_json["colors"][current_item]["color"])
                        bridge.setGroup(room, on=True, hue=animation_json["colors"][current_item]["color"], transitiontime=2)
                        # Setting color to one previously set
                    

                    factor = int(animation_json["colors"][current_item]["brightness"]) / 100
                    bridge.setGroup(room, on=True, bri=round(factor * 254), transitiontime=2)
                    # Converting from percentage to hard value

                    utime.sleep(int(animation_json["colors"][current_item]["time_until_next"]))

                    current_item += 1
                    if current_item == max_lenght:
                        current_item = 0
                    # If we're at the end of the animation, reset to beginning
                except KeyError:
                    pass
                
    elif chosen_option == 3:
#         Back
        room_selection(bridge)
        return
    
    
    
def main():
    if path_exists("setup.json") == False:
#         refresh_screen()
        refresh_screen()
        center("Gefeliciteerd! :D")
        tft.text(font, f"< Volgende", 10, 150)
        
        right_button_press = False
        while right_button_press == False:
            if right_button.value() == 0:
                refresh_screen()
                right_button_press = True
                
        long_text("Gefeliciteerd met je verjaardag papa! Dit is niet helemaal op je lijst, maar ik hoop wel dat je er plezier aan hebt! :D \n -Dante \n \n PS: Druk op onderste knop")
        #long_text("Hi Luck! Hope you're doing alright! :D This might not seem like much either, but it still took quite a while xD")

        right_button_press = False
        while right_button_press == False:
            if right_button.value() == 0:
                refresh_screen()
                right_button_press = True
                
        center("Besturingen")
        tft.text(font, f"< Selecteer", 10, 10)
        tft.text(font, f"< Bevestig keuze", 10, 150)
        
        right_button_press = False
        while right_button_press == False:
            if right_button.value() == 0:
                refresh_screen()
                right_button_press = True
            if left_button.value() == 0:
                tft.deinit()
                tft.init()
                center("(druk onderste knop om verder te gaan)")

        refresh_screen()
        
        SetupDict = {
            "_comment1": "SETUP FILE",
            "_comment2": "Important settings are stored here. Do not delete.",
            "SetupVersion": 0.2,
            "network_name": NETWORK_NAME,
            "network_password": NETWORK_PASSWORD
        }

        SetupDictStr = json.dumps(SetupDict, separators=(',', ': '))
        with open('setup.json', 'w') as SetupJSON:
            SetupJSON.write(SetupDictStr)
        
    refresh_screen()
    center("Verbinden...")
    
    with open('setup.json') as dataFile:
        data = json.load(dataFile)
        
    if data["SetupVersion"] != 0.2:
        os.remove("setup.json")
        refresh_screen()
        main()
        sys.exit(0)
        
        
    # connect to network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    # might already be connected somehow.
    
    if wlan.isconnected() == False:
        wlan.connect(data["network_name"], data["network_password"])

    # Wait for connection.
    while wlan.isconnected() == False:
        pass
    center("Laden...")
    bridge = hue.Bridge(autosetup=False, debug=1)
    success = bridge.loadSettings()
    soft_refresh_screen()
    if success:
        # verify bridge settings work
        try:
            bridge.idLights()
            success = True
        except:
            success = False
    soft_refresh_screen()
    if not success:
        left_button_press = False
        tft.text(font, f"< Zoek naar Hue Bridge", 10, 10)
        while left_button_press == False:
            if left_button.value() == 0:
                soft_refresh_screen()
                if bridge.discover() == None:
                    center("Geen Hue bridge op netwerk")
                    utime.sleep(10)
                    sys.exit(0)
                center("Druk op Hue link knop")
                setup = bridge.setup()
                if setup != None:
                    soft_refresh_screen()
                    left_button_press = True
                    center("Knop gedruk!")
                else:
                    soft_refresh_screen()
                    center("Knop niet gedrukt of kon niet verbinden")
                    utime.sleep(5)
                    soft_refresh_screen()
                    tft.text(font, f"< Zoek opnieuw", 10, 10)
    soft_refresh_screen()
    room_selection(bridge)
    
tft.deinit()
tft.init()
try:
    main()
except Exception as e:
    refresh_screen()
    tft.text(font, f"^ Herstart apparaat", 10, 10)
    tft.text(font, f"< Zie fout bericht", 10, 150)
    center("Er is iets misgegaan :(")
    
    print(e)
    
    look_for_button_press = True
    while look_for_button_press == True:
        if right_button.value() == 0:
            soft_refresh_screen()
            long_text(str(e))
            look_for_button_press = False
            
    sys.exit(0)
    


