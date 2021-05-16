#!/usr/bin/env python3

# Copyright (C) 2021 Raffaele Mancuso

import sys
if sys.version_info[0] < 3:
    raise Exception("You must run the script with Python >= 3")
if sys.version_info[0] == 3 and sys.version_info[1] < 6:
    raise Exception("You must run the script with Python >= 3.6")

import requests
from bs4 import BeautifulSoup   
import os.path
import datetime
import json
import argparse
import subprocess
import time
import deskenv
import os
import re

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
    
def downloadFile(url, output_filepath):
    print("Downloading '"+url+"' into '"+output_filepath+"'")
    r = requests.get(url)
    with open(output_filepath, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=128):
            fd.write(chunk)

# Get the link of the Smithsonian image of the day
def getSmithLink(out_file):    
    #Download web page
    print("Downloading Smithsonian webpage...")
    r = requests.get('https://www.smithsonianmag.com/category/photo-of-the-day/')    
    if(r.status_code != 200):
        print("ERROR: no image of the day found for Smithsonian")
        return None
    # Get POTD webpage
    soup = BeautifulSoup(r.content,"lxml")    
    div_item = soup.find("aside", class_="day-feature")    
    assert(div_item is not None)
    link = div_item.find('a')['href']
    assert(link is not None)
    print(f"Link: {link}")
    # Scrape the real image link
    r = requests.get(link)    
    if(r.status_code != 200):
        print("Image webpage error")
        return None
    soup = BeautifulSoup(r.content,"lxml")    
    div_item = soup.find("div", class_="photo_detail_wrapper")
    assert(div_item is not None)
    div_item2 = div_item.find("div", class_="photo-detail")
    assert(div_item2 is not None)
    img_link = div_item.find("img")["src"]
    downloadFile(img_link, out_file)
    return out_file
    
# Get the link of the WikiMedia image of the day
def getWikiMediaLink(out_file):    
    #Download web page
    print("Downloading WikiMedia webpage...")
    r = requests.get('https://commons.wikimedia.org/wiki/Main_Page')    
    if(r.status_code != 200):
        print("ERROR: status_code: "+r.status_code)
        sys.exit()    
    #get binary response content
    cont = r.content
    soup = BeautifulSoup(cont,"lxml")    
    img_item = soup.find("img")    
    if(img_item is None):
        print("ERROR: img_item not found")    
    img_link = img_item['src'].replace("thumb/","")    
    pos = img_link.rfind("/")
    img_link = img_link[0:pos]
    downloadFile(img_link, out_file)
    return out_file

#Get link of the National Geographics image of the day
def getNGLink(out_file):
    #Download web page
    print("Downloading NG webpage...")
    r = requests.get('http://www.nationalgeographic.com/photography/photo-of-the-day/')    
    if(r.status_code != 200):
        print("ERROR: status_code: "+r.status_code)
        sys.exit()    
    #get binary response content
    cont = r.content
    #print(cont)
    soup = BeautifulSoup(cont,"lxml")    
    s_url = soup.find("meta", {"property":"og:url"})
    s_desc = soup.find("meta", {"name":"description"})
    s_image = soup.find("meta", {"property":"og:image"})    
    if(s_image is None):
        print("ERROR: s_image not found")    
    img_link = s_image['content']
    downloadFile(img_link, out_file)
    return out_file

#Get link of the Bing image of the day
def getBingLink(out_file):
    #Download web page
    print("Downloading Bing webpage...")
    r = requests.get('https://www.bing.com', stream=True)    
    if(r.status_code != 200):
        print("ERROR: status_code: "+r.status_code)
        sys.exit()    
    #get text
    soup = BeautifulSoup(r.content,"lxml")   
    #re.match -> only matches AT THE BEGINNING OF THE STRING
    # *? is the non-greedy version
    div_img = soup.find("div", {"class", "img_cont"})
    assert(div_img is not None)    
    img_link = div_img["style"]
    img_link = re.search(r"url\((.*)&", img_link).group(1)
    img_link = 'https://www.bing.com'+img_link
    print(img_link)
    
    downloadFile(img_link, out_file)
    return out_file
    
#Get link of the Guardian image of the day
def getGuardianLink(out_file, n=1):

    # Download Home
    print("Downloading Guardian home page...")
    r = requests.get('http://www.theguardian.com/international')    
    if(r.status_code != 200):
        print("ERROR: status_code is not 200, but instead it's "+str(r.status_code))
        sys.exit()
    
    # Get "Best Photographs of the day" card
    soup = BeautifulSoup(r.content, "lxml")    
    span = soup.find("span", text="Best photographs of the day")
    assert(span is not None)
    
    # Get link to webpage with picture of the day
    link = span.parent["href"]
    
    # Download gallery webpage
    print("Downloading Guardian gallery page...")
    r = requests.get(link)    
    if(r.status_code != 200):
        print("ERROR: status_code is not 200, but instead it's "+str(r.status_code))
        sys.exit()
    
    # Get first picture of the gallery
    soup = BeautifulSoup(r.content, "lxml") 
    picture = soup.find("li", {"id":f"img-{n}"})
    picture = picture.figure.find("a", class_="gallery__img-container")
    picture = picture.find("div", class_="u-responsive-ratio").picture
    picture = picture.find("source")["srcset"]
    picture = picture.split()[0]
    downloadFile(picture, out_file)
    return out_file
    
#Get link of the NASA image of the day
def getNASALink(out_file):
    #Download web page
    print("Downloading NASA webpage...")
    base_url = 'http://apod.nasa.gov'
    r = requests.get(base_url)    
    if(r.status_code != 200):
        print("ERROR: status_code is not 200, but instead it's "+str(r.status_code))
        sys.exit()    
    #get binary response content
    soup = BeautifulSoup(r.content,"lxml")    
    div_img = soup.find("img")
    highest_res_link = base_url + "/" + div_img['src']
    downloadFile(highest_res_link, out_file)
    return out_file
   
# Get the directory in which the POTD will be saved
def getOutputDir(env):
    if env in ["gnome", "kde", "xfce4", "unity"]:
        img_dir = os.path.expandvars("$HOME/.potd")
    elif env=="windows":
        #img_dir = os.path.expandvars("%HOMEPATH%/Pictures/potd")
        img_dir = os.path.expandvars("%USERPROFILE%/Pictures/potd")
        # Get absolute path, otherwise it expands to \Users\...
        img_dir = os.path.abspath(img_dir)
    else:
        raise Exception("Cannot establish an output directory for environment '{}'".format(env))
    os.makedirs(img_dir, exist_ok=True)
    return img_dir
        
# MAIN
if __name__ == "__main__":  

    parser = argparse.ArgumentParser(description='Download the Photo of the Day from various websites and set it as the wallpaper of your desktop. '\
        'DISCLAIMER: This software is NOT affiliated with or sponsored by any of these websites.')
    parser.add_argument('--site', choices=['ng', 'bing', 'wiki', 'guardian','nasa', 'smith', 'all', 'ask'], 
    	help='The website from which to download Photo of the Day.', 
    	default="ask")
    parser.add_argument('--loop', action='store_true', default=False, help='Loop perdiocally over the wallpapers')
    parser.add_argument('--debug', action='store_true', default=False, help=argparse.SUPPRESS)
    parser.add_argument('--period', type=int, default=60, help='Period of wallpaper change, in seconds (only if --loop is set)')
    parser.add_argument('--n', type=int, default=1, help='If the website supports more than one POTD, specify which one to download. '\
        'Currently supported only for The Guardian.')
    parser.add_argument('--mode', type=str, default="scaled", help='Specify the mode in which wallpaper id displayed. ' \
        'Possible values are: none, wallpaper, centered, scaled, stretched, zoom, spanned. ' \
        'Currently only supported on GNOME.')
    parser.add_argument('--force-download', action='store_true', default=False, help='Force the download of the wallpaper ' \
        'regardless of whether we have already downloaded that wallpaper today')
    args = parser.parse_args()
    
    # Ask the user which website to use
    if args.site=="ask" and not args.loop:
    	print("Choose a website:")
    	print("1. National Geographic")
    	print("2. Bing")
    	print("3. Wikimedia")
    	print("4. The Guardian")
    	print("5. NASA")
    	print("6. Smithsosian")
    	choice = input("Enter your choice: ")    	
    	if choice=="1":
    		args.site="ng"
    	elif choice=="2":
    		args.site="bing"
    	elif choice=="3":
    		args.site="wiki"
    	elif choice=="4":
    		args.site="guardian"
    	elif choice=="5":
    		args.site="nasa"
    	elif choice=="6":
    		args.site="smith"
    	else:
    		print("Invalid choice")
    		sys.exit(1)
    		
    # If we loop over, download them all
    if args.loop:
        args.site = "all"

    # Generate file paths
    env = deskenv.get_desktop_environment()
    # name of the output image file
    img_dir = getOutputDir(env)
    todaystr = datetime.date.today().isoformat().replace("-","")
    img_path = os.path.join(img_dir, todaystr)
    json_path = os.path.splitext(img_path)[0] + ".json"

    # Download wallpaper images

    spec_path = None
    
    if args.site in ['ng', 'all']:
        spec_path = os.path.join(img_path+"ng.jpg")
        download = not os.path.isfile(spec_path)
        if args.force_download:
            download = True
        if download:
            getNGLink(spec_path)
        else:
            print("National Geographic wallpaper already downloaded")
            
    if args.site in ['bing', 'all']:
        spec_path = os.path.join(img_path+"bing.jpg")
        download = not os.path.isfile(spec_path)
        if args.force_download:
            download = True
        if download:
            getBingLink(spec_path)    
        else:
            print("Bing wallpaper already downloaded")
            
    if args.site in ['wiki', 'all']:
        spec_path = os.path.join(img_path+"wiki.jpg")
        download = not os.path.isfile(spec_path)
        if args.force_download:
            download = True
        if download:
            getWikiMediaLink(spec_path)
        else:
            print("Wikimedia wallpaper already downloaded")
        
    if args.site in ['guardian', 'all']:
        spec_path = os.path.join(f"{img_path}guardian{args.n}.jpg")
        download = not os.path.isfile(spec_path)
        if args.force_download:
            download = True
        if download:
            getGuardianLink(spec_path, args.n)
        else:
            print("The Guardian wallpaper already downloaded")
        
    if args.site in ['nasa', 'all']:
        spec_path = os.path.join(img_path+"nasa.jpg")
        download = not os.path.isfile(spec_path)
        if args.force_download:
            download = True
        if download:
            getNASALink(spec_path)
        else:
            print("NASA wallpaper already downloaded")
    
    if args.site in ['smith', 'all']:
        spec_path = os.path.join(img_path+"smith.jpg")
        download = not os.path.isfile(spec_path)
        if args.force_download:
            download = True
        if download:
            getSmithLink(spec_path)
        else:
            print("Smithsonian wallpaper already downloaded")
    
    # Set the image as the new desktop wallpaper
    # Periodically rotate among images
    if args.loop:
        filelist = [f for f in os.listdir(img_dir) if f[0:8]==todaystr]
        while True:
            print("Entering loop....")
            for file in filelist:
                changeWallpaper(env, spec_path, args.mode)
                print(f"Sleeping for {args.period} seconds...")
                time.sleep(args.period*1000)
            
    # Set the image one-shot
    else:
        if spec_path is None:
            print("ERROR: you haven't downloaded any wallpaper")
        else:
            changeWallpaper(env, spec_path, args.mode)
