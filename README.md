# Picture of the Day

## Description
"Picture of the Day" (POTD) downloads the photo of the day from any or all of the following websites:

* The Smithsonian
* Wikimedia
* National Geographic
* Bing
* The Guardian
* NASA

## Disclaimer
This software is not affiliated with or sponsored by any of those websites.

## Requirements
In order to install the required packages, run:
```pip3 install -r requirements.txt```

## Command line arguments

* The `--site <website>` option can be passed to POTD to set which website you would like to download the wallpaper from. As <website> you can use:
  * `smith` for The Smithsonian
  * `wiki` for Wikimedia
  * `ng` for National Geographic
  * `bing` for Bing
  * `guardian` for The Guardian
  * `nasa` for NASA
  
## Examples
* `python potd.py --site ng`
Download the Photo of the Day from the National Geographic website and set it as the wallpaper of your desktop.

