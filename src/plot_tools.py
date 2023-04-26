#  Copyright (c) 2023.   Adam Buruzs
import os, sys
import pandas as pd
import numpy as np
import cv2 as cv
import math

import logging
import matplotlib.pyplot as plt

logging.basicConfig(stream = sys.stdout, level = logging.INFO)

logging.getLogger('matplotlib.font_manager').disabled = True
logging.getLogger('PIL.PngImagePlugin').disabled = True



def imgResize(img, width):
    """ resizing an image"""
    logging.debug(f"original image size {img.shape}")
    newheight = int(img.shape[0] * width/ img.shape[1])
    res_img = cv.resize(img, dsize = (width, newheight), interpolation = cv.INTER_AREA)
    return res_img

def show2Image(imgs, titles = ["left", "right"], rotate180 = False,
               addhlines = False, horizontal = True, mainTitle = None,
               printclick = False, figheight = 6,  **plotops):
    """ shows 2 or more images side by side
    Sometimes BGR and RGB is mixed, then mixed colors: to solve that use img[...,::-1] as input (Red<->Blue exchange)

    :param imgs: list of 2 images
    :param titles:
    :param rotate180:
    :param addhlines: add horizontal lines
    :param horizontal:
    :param mainTitle:
    :param printclick: print the coordinates of the clicked points
    :return:
    """
    nimages = len(imgs)
    if horizontal:
        fig, ax = plt.subplots(1,nimages, figsize=(15, figheight), **plotops)
    else: # vertical
        fig, ax = plt.subplots(nimages, 1, figsize = (8,figheight), **plotops)
    for k in range(len(imgs)):
        img = imgs[k]
        if rotate180:
            iflip = np.flip(img, axis= 0)
            img2show = np.flip(iflip, axis= 1)
        else:
            img2show = img
        #if img2show.ndim == 3:
        ## change BGR from RGB
        ## img2show = img2show[...,::-1]
        ax[k].imshow(img2show)
        ax[k].set_title(titles[k])
        if addhlines:
            for kh in range(100, min(1000, imgs[0].shape[0]), 100):
                ax[k].axhline(y = kh, color= "r", alpha = 0.4, linestyle = "--")
    plt.tight_layout()
    if mainTitle is not None:
        plt.suptitle(mainTitle )
    if printclick:
        callback = lambda event : print(event.xdata, event.ydata)
        fig.canvas.callbacks.connect('button_press_event', callback)
    return ax, fig

def showNImage(imgs, titles = ["left", "right"], ncols= 2, rotate180 = False,
               addhlines = False, horizontal = True, mainTitle = None,
               printclick = False, figheight = 6,  **plotops):
    """ shows 2 or more images in nrows rows
    Sometimes BGR and RGB is mixed, then mixed colors: to solve that use img[...,::-1] as input (Red<->Blue exchange)

    :param imgs: list of 2 images
    :param ncols: number of rows
    :param titles:
    :param rotate180:
    :param addhlines: add horizontal lines
    :param horizontal:
    :param mainTitle:
    :param printclick: print the coordinates of the clicked points
    :return:
    """
    nimages = len(imgs)
    nrows = math.ceil(nimages/ncols)
    fig, ax = plt.subplots(ncols , math.ceil(nimages/ncols), figsize = (ncols*5,nrows*5), **plotops)
    for k in range(len(imgs)):
        kx = math.floor(k/ncols)
        ky = k%ncols
        img = imgs[k]
        if rotate180:
            iflip = np.flip(img, axis= 0)
            img2show = np.flip(iflip, axis= 1)
        else:
            img2show = img
        #if img2show.ndim == 3:
        ## change BGR from RGB
        ## img2show = img2show[...,::-1]
        ax[kx,ky].imshow(img2show)
        ax[kx,ky].set_title(titles[k])
        if addhlines:
            for kh in range(100, min(1000, imgs[0].shape[0]), 100):
                ax[kx,ky].axhline(y = kh, color= "r", alpha = 0.4, linestyle = "--")
    plt.tight_layout()
    if mainTitle is not None:
        plt.suptitle(mainTitle )
    if printclick:
        callback = lambda event : print(event.xdata, event.ydata)
        fig.canvas.callbacks.connect('button_press_event', callback)
    return ax, fig

def plotOver(imgray, img2, rgb= "r"):
    """ plot image 1 in grayscale, and add over it the img2 with red colors
    :param imgray: normal grayscale image
    :param img2: binary image for edges, or some small number of unique values (for segments)
    :param rgb: which color to use ? "r" red "g" green or "b" blue
    :return: a colored image with img1, and img2 in red over it
    """
    imgout1 = np.repeat(imgray[:, :, np.newaxis], 3, axis=2)
    redshift = img2/np.max(img2)
    if rgb == "r":
        colshift = np.dstack((redshift * 255, np.zeros(redshift.shape), np.zeros(redshift.shape) ))
    elif rgb =="g":
        colshift = np.dstack((np.zeros(redshift.shape), redshift * 255, np.zeros(redshift.shape) ))
    elif rgb == "b":
        colshift = np.dstack((np.zeros(redshift.shape),np.zeros(redshift.shape), redshift*255))
    imgShifted = imgout1 + colshift
    #reduceRed = lambda rgb: (round(min(rgb[2], 255)), round(rgb[0]), round(rgb[1]))
    #imgout = np.apply_along_axis(reduceRed, 2, imgShifted)
    imgout = np.clip(imgShifted, a_min=-255, a_max=255).astype("int")
    return  imgout


if __name__ == "__main__":
    picdir = "../Data/Vamsis"
    imgpath = "house4.jpg"
    src = cv.imread(os.path.join(picdir, imgpath), cv.IMREAD_COLOR)
    re_width = 500
    img_col = imgResize(src, re_width)
    img_gray = cv.cvtColor(img_col, cv.COLOR_BGR2GRAY)
    img2 = np.zeros(img_gray.shape)
    img2[100:150, 100:300] = 1
    imgMerged = plotOver(img_gray, img2)
    plt.imshow(img_col)
    plt.imshow(img2)
    plt.imshow(imgMerged)
    ax = show2Image([img_col, imgMerged], ["orig image", "segments and filtered edge segments"], horizontal=True)


