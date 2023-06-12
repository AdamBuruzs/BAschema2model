#  Copyright (c) 2023.   Adam Buruzs

import os, sys
import numpy as np
import cv2 as cv
from matplotlib.patches import Rectangle

import logging
import matplotlib.pyplot as plt

from src import plot_tools

logging.basicConfig(stream = sys.stdout, level = logging.INFO)

logging.getLogger('matplotlib.font_manager').disabled = True
logging.getLogger('PIL.PngImagePlugin').disabled = True

def imgResize(img, width):
    """ resizing an image"""
    logging.debug(f"original image size {img.shape}")
    newheight = int(img.shape[0] * width/ img.shape[1])
    res_img = cv.resize(img, dsize = (width, newheight), interpolation = cv.INTER_AREA)
    return res_img

def showLines4(axis , edges :np.ndarray, lines :np.ndarray, color = "red", cmap = 'viridis'):
    """ Plotting hough lines on image
    :param axis: matplotlib axis to show the lines and edges
    :param edges: a binary image with cany edges
    :param lines: Hough line segments obtained by cv.HoughLinesP shape (N, 1, 4)
    :param cmap: 'viridis' for dark, 'Grey' for white background..
    :return: show the image
    """
    axis.imshow(edges, cmap=cmap,  interpolation=None) #  interpolation='nearest'
    if(lines.__len__() == 0):
        logging.error("no lines detected")
        return
    for li in lines:
        #print(li)
        if li.ndim == 2:
            x1,y1,x2, y2 = li[0]
        else:
            x1, y1, x2, y2 = li
        axis.plot([x1,x2], [y1,y2], color= color, alpha = 0.7)
    #axis.set_title("cany edges & Prob-Hough segments")

def showRectangles(axis , rectangles :np.ndarray, color = "#11BB13", alpha = 0.7):
    for ri in rectangles:
        x_lt,y_lt, x_rb,y_rb = ri
        axis.add_patch(Rectangle((x_lt, y_lt),
                               x_rb-x_lt, y_rb - y_lt,
                               fc='none',
                               ec=color,
                               alpha = alpha,
                               lw=3))
        plt.show()


def getHLines(bim, minlen = 50):
    """ get horizontal lines from binary image
    :param bim: image NXM of True or FAlse or 0 or 1 values
    :return: vertical or horizontal line segments list of (x0, y0, x1, y1) values for the corner points for each line
    """
    vstat = bim.sum(axis = 1)
    candidates = vstat > minlen
    hix = np.where(candidates)[0]
    hlines = []
    for hi in hix:
        #logging.debug(f"processing line {hi}")
        row = bim[hi, :]
        startSeq = np.r_[row[0], ~ row[:-1] & row[1:] ]
        #startSeq = np.concatenate(([False],  ~ row[:-1] & row[1:]))
        endSeq = np.r_[False, row[:-1] & ~ row[1:] ]
        startIx = np.where(startSeq)[0]
        endIx = np.where(endSeq)[0]
        spans = list(zip(startIx, endIx))
        longlines = [spi for spi in spans if spi[1]-spi[0] >= minlen ]
        for li in longlines:
            hlines.append(np.array([li[0],hi, li[1], hi]))
    return np.array(hlines)

def detecRectangles(lines : np.array, tol = 5):
    """ detect rectangles from a set of straight horizontal/vertical lines
    :param lines: array of rows [x1,y1,x2,y2]
    :return: list of rectangles, where rectangles are defined by
        (topleft_x, topleft_y , bottomright_x, bottomright_y) coordinates
    """
    hLines = lines[ lines[:,1] == lines[:,3],:] # horizontal lines
    vLines = lines[ lines[:,0] == lines[:,2],:] # vertical lines
    rectangles = []
    for i in range(hLines.shape[0]):
        thisLine = hLines[i,:] # this is a horizontal line
        ## match if same xleft, xright, and y bigger
        matches = (abs(hLines[:,0] -thisLine[0]) <= tol) & (abs(hLines[:,2] -thisLine[2]) <= tol) & (hLines[:,1] > thisLine[1])
        matchix = np.where(matches)[0]
        realmatch = matchix[matchix != i]
        if realmatch.__len__() > 0:
            #[print(f" hline {i} match with {mi}") for mi in realmatch]
            for mi in realmatch:
                ## the corners of the left-side and right-side vertical lines
                matchLine = hLines[mi] # the matching horizontal line
                leftside = np.array([thisLine[0], thisLine[1], matchLine[0], matchLine[1]])
                rightside = np.array([thisLine[2], thisLine[3], matchLine[2], matchLine[3]])
                leftmatch = vLines[ abs(vLines-leftside).sum(axis = 1) < tol*2 ]
                rightmatch = vLines[ abs(vLines-rightside).sum(axis = 1) < tol*2 ]
                if ((leftmatch.__len__()) > 0) &  (rightmatch.__len__() > 0):
                    print(f"found matching {i} vline to h lines {thisLine} + {matchLine}:\n"
                          f"left: {leftmatch} and right: {rightmatch}")
                    rectangles.append(np.array([thisLine[0], thisLine[1], matchLine[2], matchLine[3] ]))
    return rectangles

def getRectangles(edgesbin, minlen= 40 , tol = 15):
    """ extract rectangles from inary image of
    :param edgesbin: binary image of edges
    :param minlen: minimum side length of a rectangle to be detected
    :param tol: tolerance in pixels
    :return: numpy array of rectangles
    """
    print(f"getting rectangles with tol= {tol}")
    hLines = getHLines(edgesbin, minlen=minlen)
    vLinesT = getHLines(np.transpose(edgesbin), minlen=minlen)
    if vLinesT.__len__() == 0 :
        logging.info(f"no vertical line found")
        return [], hLines
    vLines = vLinesT[:, [1, 0, 3, 2]]
    lines = np.concatenate((hLines, vLines), axis=0)
    rectans = detecRectangles(lines, tol=tol)
    ## filter by the size
    rectans = [ri for ri in rectans if (abs(ri[2] - ri[0]) > minlen - 5) & (abs(ri[3] - ri[1]) > minlen - 5)]
    rectangles = np.array(rectans)
    ## TODO: calculate overlap between rectangles, and remove with high overlap
    keep_mask = np.ones(rectangles.shape[0])
    for i in range(1, rectangles.shape[0]):
        others = rectangles[0:i,:]
        diffs = others- rectangles[i,:] # difference to line-i
        smallest_diff = min(abs(diffs).sum(axis = 1))
        if smallest_diff < 4 :
            keep_mask[i]= 0
    rect_filtered  = rectangles[keep_mask == 1]
    #rectangles = [ri for ri in rectangles if (abs(ri[2] - ri[0]) > minlen -5 ) & (abs(ri[3] - ri[1]) > minlen -5 )]
    return rect_filtered, lines

if __name__ == "__main__":
    #def linesFromImg(imgfile):
    re_width = 1000
    blurN = 3
    rho = 1
    theta = 0.017
    th1 = 50
    th2 = 100
    aps = 3
    hough_treshold = 50
    minLineLength = 20
    maxLineGap = 10
    picdir = "ControlDiagrams"
    imgpath = "page7Regler.jpg"
    src = cv.imread(os.path.join(picdir, imgpath), cv.IMREAD_COLOR)
    #img = imgResize(src, re_width)
    img = src
    img_blur = cv.GaussianBlur(img,(blurN,blurN), sigmaX=0, sigmaY=0)
    edges = cv.Canny(image=img_blur, threshold1= th1, threshold2=th2, edges=None, apertureSize=aps,
                   L2gradient=None)

    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    edg2 = gray < 250

    ## this returns line segments with endpoints
    houghLinesProb = cv.HoughLinesP(edges, rho = rho, theta= theta, threshold=hough_treshold,
                                 minLineLength= minLineLength, maxLineGap=maxLineGap)
    ax, fig = plot_tools.show2Image([img, edg2], ["orig image", f"Canny"], horizontal = False, figheight = 2)
    #showLines4(ax[1], edges, houghLinesProb)
    # houghLinesProb = cv.HoughLinesP(binedges.astype('uint8'), rho=1, theta=0.02, threshold=hough_treshold,
    #                                 minLineLength=minLineLength, maxLineGap=maxLineGap)

    hLines = getHLines(edg2, minlen = 50)
    vLinesT = getHLines(np.transpose(edg2), minlen = 40)
    vLines = vLinesT[:,[1,0,3,2]]
    showLines4(ax[1], edg2, hLines, color = "#11FF00")
    showLines4(ax[1], edg2, vLines, color = "#AAAAAA")
    lines = np.concatenate( (hLines,vLines) , axis = 0)
    rectans = detecRectangles(lines, tol= 15)
    rectangles = np.array(rectans)
    minsize = 10
    rectangles = [ri for ri in rectangles if (abs(ri[2] -ri[0]) > minsize) &  (abs(ri[3] -ri[1]) > minsize) ]
    ax[1].set_title("horizontal/vertical edges and detected rectangles")
    showRectangles(ax[1], rectangles, color = "#FF1177", alpha = 0.95)