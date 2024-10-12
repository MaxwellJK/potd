#!/usr/bin/python

# Copyright (C) 2023 Raffaele Mancuso

import requests
from bs4 import BeautifulSoup
import datetime
import argparse
import os
import random
import re
from pathlib import Path
import subprocess
import sys


def downloadFile(url, output_filepath):
    #print("Downloading '" + str(url) + "' into '" + str(output_filepath) + "'")
    r = requests.get(url)
    if r.status_code != 200:
        #print("ERROR: Image download failed with requests.get")
        # cmd = ["wget", url, "-O", output_filepath]
        cmd = ["curl", url, "-O", output_filepath]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print("ERROR: Image download failed with wget")
            return None
    else:
        # Save file downloaded with requests.get
        with open(output_filepath, "wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)


# Get the link of the Smithsonian image of the day
def getSmithLink(out_file):
    # Download web page
    r = requests.get("https://www.smithsonianmag.com/category/photo-of-the-day/")
    if r.status_code != 200:
        print("ERROR: no image of the day found for Smithsonian")
        return None
    # Get POTD webpage
    soup = BeautifulSoup(r.content, "lxml")
    div_item = soup.find("aside", class_="day-feature")
    assert div_item is not None
    link = div_item.find("a")["href"]
    assert link is not None
    # Scrape the real image link
    r = requests.get(link)
    if r.status_code != 200:
        print("ERROR: Image webpage error")
        return None
    soup = BeautifulSoup(r.content, "lxml")
    div_item = soup.find("div", class_="photo_detail_wrapper")
    assert div_item is not None
    div_item2 = div_item.find("div", class_="photo-detail")
    assert div_item2 is not None
    img_link = div_item.find("img")["src"]
    downloadFile(img_link, out_file)
    return out_file


# Get the link of the WikiMedia image of the day
def getWikiMediaLink(out_file):
    r = requests.get("https://commons.wikimedia.org/wiki/Main_Page")
    if r.status_code != 200:
        print("ERROR: status_code: " + r.status_code)
        sys.exit()
    # get binary response content
    cont = r.content
    soup = BeautifulSoup(cont, "lxml")
    img_item = soup.find("img")
    if img_item is None:
        print("ERROR: img_item not found")
    img_link = img_item["src"].replace("thumb/", "")
    pos = img_link.rfind("/")
    img_link = img_link[0:pos]
    downloadFile(img_link, out_file)
    return out_file


# Get link of the National Geographics image of the day
def getNGLink(out_file):
    r = requests.get("http://www.nationalgeographic.com/photography/photo-of-the-day/")
    if r.status_code != 200:
        print("ERROR: status_code: " + r.status_code)
        sys.exit()
    # get binary response content
    cont = r.content
    # print(cont)
    soup = BeautifulSoup(cont, "lxml")
    s_url = soup.find("meta", {"property": "og:url"})
    s_desc = soup.find("meta", {"name": "description"})
    s_image = soup.find("meta", {"property": "og:image"})
    if s_image is None:
        print("ERROR: s_image not found")
    img_link = s_image["content"]
    downloadFile(img_link, out_file)
    return out_file


# Get link of the Bing image of the day
def getBingLink(out_file):
    r = requests.get("https://www.bing.com", stream=True)
    if r.status_code != 200:
        print("ERROR: status_code: " + r.status_code)
        sys.exit()
    # get text
    soup = BeautifulSoup(r.content, "lxml")
    # re.match -> only matches AT THE BEGINNING OF THE STRING
    # *? is the non-greedy version
    # div_img = soup.find("div", {"class", "img_cont"})
    div_img = soup.find("link", id="preloadBg", href=True)
    assert div_img is not None
    img_link = div_img["style"]
    img_link = re.search(r"url\((.*)&", img_link).group(1)
    img_link = "https://www.bing.com" + img_link
    downloadFile(img_link, out_file)
    return out_file


# Get link of the Guardian image of the day
def getGuardianLink(out_file, n=1):
    r = requests.get("http://www.theguardian.com/international")
    if r.status_code != 200:
        print("ERROR: status_code is not 200, but instead it's " + str(r.status_code))
        sys.exit()
    # Get "Best Photographs of the day" card
    soup = BeautifulSoup(r.content, "lxml")
    div = soup.find("div", class_="fc-item--gallery")
    assert div is not None
    div = div.find("div", class_="fc-item__container")
    assert div is not None
    link = div.a["href"]
    assert link is not None
    # Download gallery webpage
    r = requests.get(link)
    if r.status_code != 200:
        print("ERROR: status_code is not 200, but instead it's " + str(r.status_code))
        sys.exit()
    # Get first picture of the gallery
    soup = BeautifulSoup(r.content, "lxml")
    picture = soup.find("li", {"id": f"img-{n}"})
    if picture is None:
        print("ERROR: Failed to find a picture in The Guardian")
        return None
    picture = picture.figure.find("a", class_="gallery__img-container")
    picture = picture.find("div", class_="u-responsive-ratio").picture
    picture = picture.find("source")["srcset"]
    picture = picture.split()[0]
    downloadFile(picture, out_file)
    return out_file


# Get link of the NASA image of the day
def getNASALink(out_file):
    base_url = "http://apod.nasa.gov"
    r = requests.get(base_url)
    if r.status_code != 200:
        print("ERROR: status_code is not 200, but instead it's " + str(r.status_code))
        sys.exit()
    # get binary response content
    soup = BeautifulSoup(r.content, "lxml")
    div_img = soup.find("img")
    highest_res_link = base_url + "/" + div_img["src"]
    downloadFile(highest_res_link, out_file)
    return out_file


# MAIN
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Download the Photo of the Day from various websites. DISCLAIMER: This software is NOT affiliated with or sponsored by any of these websites."
    )
    parser.add_argument(
        "--site",
        choices=["ng", "bing", "wiki", "guardian", "nasa", "smith", "random"],
        help="The website from which to download Photo of the Day.",
        default="random",
    )
    parser.add_argument(
        "--debug", action="store_true", default=False, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="If the website supports more than one POTD, specify which one to download. Ignored in case --site='all'. Currently supported only for The Guardian.",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        default=False,
        help="Force the download of the wallpaper regardless of whether we have already downloaded that wallpaper today",
    )
    args = parser.parse_args()

    # Ask the user which website to use
    if args.site == "":
        arr = [("ng", "National Geographic"), ("bing","Bing"), ("wiki", "Wikimedia"),
               ("guardian", "The Guardian"), ("nasa", "NASA"), ("smith", "The Smithsonian")]
        print("Choose a website:")
        for i,(_,site) in enumerate(arr):
            print(f"{i}. {site}")
        choice = input("Enter your choice: ")
        if not choice.isnumeric():
            print("ERROR: Not a number :(")
            sys.exit()
        choice = int(choice)
        if (choice<0 or choice>(len(arr)-1)):
            print("ERROR: Choice out of range")
            sys.exit()
        args.site = arr[choice][0]

    # Download wallpaper images
    # img_dir = Path(os.path.expandvars("$HOME")) / "Pictures" / "potd"
    img_dir = Path('/app/image/')
    img_dir.mkdir(exist_ok=True, parents=True)
    # todaystr = datetime.date.today().isoformat().replace("-", "")
    # spec_path = img_dir / f"{todaystr}-{args.site}-{args.n}.jpg"
    spec_path = img_dir / f"{args.site}-{args.n}.jpg"
    download = (not spec_path.is_file()) or args.force_download
    if download:
        if args.site == "ng":
            getNGLink(spec_path)
        elif args.site == "bing":
            getBingLink(spec_path)
        elif args.site == "wiki":
            getWikiMediaLink(spec_path)
        elif args.site == "guardian":
            getGuardianLink(spec_path, args.n)
        elif args.site == "nasa":
            getNASALink(spec_path)
        elif args.site == "smith":
            getSmithLink(spec_path)
        elif args.site == "random":
            sites_list = [getNGLink, getBingLink, getWikiMediaLink, getNASALink]
            random.choice(sites_list)(spec_path)
        else:
            print("ERROR: Unknown site")
    print(spec_path, end="")
