from io import BytesIO
import logging
from pkg_resources import resource_string
import re
import requests
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps


# In:  (String) direct url of the image to download
# Out: (Image) downloaded image, unmodified, RGB
def download_image(url):
    """Downloads the specified image and returns it as a PIL image object"""
    try:
        r = requests.get(url,
                         headers={'User-Agent': 'wallpaper-reddit python script: ' +
                                                'github.com/markubiak/wallpaper-reddit'},
                         stream=True)
        logging.info("Downloading %s" % url)
        img = Image.open(r.raw).convert('RGB')
        if img.mode == "RGBA":
            logging.debug("Removing alpha layer...")
            img = pure_pil_alpha_to_color_v2(img)
        return img
    except IOError:
        logging.error("Error downloading image!")
        sys.exit(1)


# In:  (Image) input image
#      (int) width of image in px
#      (int) height of image in px
# Out: (Image) resized and cropped image
def resize_image(img, width, height):
    """Resizes the image object to the specified dimensions"""
    logging.debug("Resizing the downloaded wallpaper...")
    return ImageOps.fit(img, (width, height), Image.ANTIALIAS)


# NOTE: Image should be rescaled and cropped, else the title will look very weird
# In:  (Image) input image without title
#      (String) title to overlay on image
#      (String) case insensitive verbal description of title location. ex
#               "topleft", "BOTTOM", "center right"
#      (int, int) padding in x direction, padding in y direction
#      (int) font size in px
# Out: (Image) output image with title
def set_image_title(img, title, gravity, padding, fontsize):
    """Overlays the title of the image onto the image"""
    logging.debug("Setting title")
    # clean up the title and gravity strings
    title = remove_tags(title)
    gravity = gravity.lower().replace(' ', '').strip()
    # setup the new image and load in the font
    ret_img = img.copy()
    draw = ImageDraw.Draw(ret_img)
    font_bytes = resource_string(__name__, "fonts/Cantarell-Regular.otf")
    font = ImageFont.truetype(font=BytesIO(font_bytes), size=fontsize)
    # topleft point of the generated title
    text_x = font.getsize(title)[0]
    text_y = font.getsize(title)[1]
    # parsing x location
    if "left" in gravity:
        title_top_left_x = padding[0]
    elif "right" in gravity:
        title_top_left_x = ret_img.size[0] - text_x - padding[0]
    else: # center
        title_top_left_x = (ret_img.size[0] - text_x) / 2
    # parsing y location
    if "top" in gravity:
        title_top_left_y = padding[1]
    elif "bottom" in gravity:
        title_top_left_y = ret_img.size[1] - text_y - padding[1]
    else: # center
        title_top_left_y = (ret_img.size[1] - text_y) / 2
    # draw a shadow then the actual text
    draw.text((title_top_left_x+2, title_top_left_y+2), title, font=font, fill=(0, 0, 0, 127))
    draw.text((title_top_left_x, title_top_left_y), title, font=font)
    del draw
    return ret_img


# In:  (String) directory to save info in
#      (String) url of the image
#      (String) image title
#      (String) image permalink
def save_info(basepath, url, title, permalink):
    """Saves the url of the image to url.txt, the title of the image to title.txt,
    and the permalink to permalink.txt just for reference"""
    # Reddit escapes the unicode in json, so when the json is downloaded, the info has to be manually re-encoded
    # and have the unicode characters reprocessed
    # title = title.encode('utf-8').decode('unicode-escape')
    with open(basepath + '/url.txt', 'w') as url_info:
        url_info.write(url)
    with open(basepath + '/title.txt', 'w') as title_info:
        title_info.write(title)
    with open(basepath + '/permalink.txt', 'w') as link_info:
        link_info.write(permalink)


# In:  (String) title of the picture
# Out: (String) title without any annoying tags
def remove_tags(str):
    """Removes the undesirable [tags] and (tags) throughout the image"""
    return re.sub(' +', ' ', re.sub("[\[\(\<].*?[\]\)\>]", "", str)).strip()


# Alpha composite an RGBA Image with a specified color.
# Source: http://stackoverflow.com/a/9459208/284318
# In:  (Image) PIL RGBA Image object - image with alpha channel
#      (int, int, int) Tuple r, g, b (default 255, 255, 255) color
#                      of the background to paste the img on top of.
def pure_pil_alpha_to_color_v2(image, color=(255, 255, 255)):
    image.load()  # needed for split()
    background = Image.new('RGB', image.size, color)
    background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
    return background
