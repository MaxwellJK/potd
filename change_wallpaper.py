#!/usr/bin/env python3

import os
import subprocess

# Change the wallpaper
def changeWallpaper(env, img_path, mode):
    print("changeWallpaper: changing wallpaper to '{}'".format(img_path))
    if env == "gnome":
        setWallpaperGnome(img_path, mode)
    elif env == "unity":
        setWallpaperGnome(img_path)
    elif env == "windows":
        setWallpaperWindows(img_path)
    elif env == "kde":
        setWallpaperPlasma5(img_path)
    elif env == "xfce4":
        setWallpaperXfce4(img_path)
    else:
        print("Error in changeWallpaper(): Platform '{}' not implemented yet".format(env))

# Set wallpaper on PLASMA 5 desktop
def setWallpaperPlasma5(image_file):
    import dbus
    jscript = """
    var allDesktops = desktops();
    print (allDesktops);
    for (i=0;i<allDesktops.length;i++) {
        d = allDesktops[i];
        d.wallpaperPlugin = "org.kde.image";
        d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
        d.writeConfig("Image", "file://""" + image_file + """");
        }"""
    bus = dbus.SessionBus()
    plasma = dbus.Interface(bus.get_object('org.kde.plasmashell', '/PlasmaShell'), dbus_interface='org.kde.PlasmaShell')
    plasma.evaluateScript(jscript)
    
# Set wallpaper on MAC OSX desktop (untested) 
# See: https://stackoverflow.com/questions/431205/how-can-i-programmatically-change-the-background-in-mac-os-x
def setWallpaperMac(image_file):
    from appscript import app, mactypes
    app('Finder').desktop_picture.set(mactypes.File(image_file))

# Set wallpaper on Windows desktop
def setWallpaperWindows(image_file):
    import ctypes
    SPI_SETDESKWALLPAPER = 20 
    SPIF_UPDATEINIFILE = 1
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, os.path.abspath(image_file), SPIF_UPDATEINIFILE)

#Set wallpaper on GNOME desktop
def setWallpaperGnome(image_file, mode="scaled"):
    image_file = os.path.abspath(image_file)
    # Set background image
    command = "/usr/bin/gsettings set org.gnome.desktop.background picture-uri file://" + image_file
    #print("COMMAND: "+command)
    subprocess.run(command.split())
    # Set "scaled" option to avoid image is stretched
    command = f"/usr/bin/gsettings set org.gnome.desktop.background picture-options {mode}"
    #print("COMMAND: "+command)
    subprocess.run(command.split())

#Set wallpaper on XFCE4 desktop
def setWallpaperXfce4(image_file):
    image_file = os.path.abspath(image_file)
    command = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "./change_xfce4_wallpaper.sh") + " " + image_file
    print("COMMAND: "+command)
    subprocess.run(command.split())
