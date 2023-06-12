#  Copyright (c) 2023.   Adam Buruzs
## code to identify line connections

# rough outline:
# 1. Load list of Lines with Elias program
# 2. Find joints: 45 degree small segments that connects lines. and add crresponding lines as joints.
# 2b Is there a 3 line joint with round thick circle shape? (page 18)
# 3.  Find corner joints with 2 lines: 1 vertical and 1 horizontal

# 4a define terminal points: inputTerminal : for the top vertical lines receiving inputs
# 4b terminals for the control blocks (recognized rectangles). And remove lines within the rectangles.
# find path (recursive function over the dict(line, [connected lines]) ) between terminals.
import logging, sys

from src import exportRegelStruktur

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
import fitz
import src.lineReader as lineReader
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Qt5Agg")
from src import straightLines
from src import readpdf
import cv2 as cv
from time import time


def regelstrukturY(page):
    """Extract y coordinates of the Reglerstruktur part of the WSCAD pdf page """
    label_Typ_coords = page.search_for("Typ")
    Y_before_Regel, Y_after_Regel, HSY = exportRegelStruktur.getSectionStrYLims(page, "Regelstruktur")
    y_top = math.ceil(label_Typ_coords[0].bottom_right.y) + 1
    try:
        print(f"Index position {Y_after_Regel}")
        y_bottom = math.floor(Y_after_Regel)
    except:
        print(f" anchor labels not found")
        y_bottom = page.mediabox_size[1] - 67
    print(f"medbox size {page.mediabox_size[1]}, Regelstruktur section between {y_top} - {y_bottom}")
    return y_top, y_bottom


def plotLines(ax, lines, Ymax, col="#BB2355", alpha=0.5, annotate=False):
    """ plot Elias lines to matpülotlib axis
    :param ax: plot axis
    :param lines: list of lines
    :param Ym: mediabox size, max Y
    """
    t0 = time()
    xvals = np.array([[li.startPoint[0], li.endPoint[0]] for li in lines]).transpose()
    yvals = np.array([[Ymax - li.startPoint[1], Ymax - li.endPoint[1]] for li in lines]).transpose()
    ax.plot(xvals, yvals, c=col, alpha=alpha)
    logging.info(f"{len(lines)} lines were plotted in {round(time() - t0, 3)} sec")
    if annotate:
        for i, li in enumerate(lines):
            xmid = (li.startPoint[0] + li.endPoint[0]) / 2.0
            ymid = (li.startPoint[1] + li.endPoint[1]) / 2.0
            # ax.annotate(i,(xmid, Ymax - ymid))
            ax.text(xmid, Ymax - ymid, f"l_{i}", style='italic', alpha=0.5, color="grey")
    # for li in lines:
    #     xv = [li.startPoint[0], li.endPoint[0]]
    #     yv = [Ymax - li.startPoint[1], Ymax - li.endPoint[1]]
    #     ax.plot(xv,yv, c = col, alpha = alpha)
    # if plotlabels:
    #     plt.text(np.array(xv).mean(),np.array(yv).mean(), li['seqno'],style='italic', alpha= 0.5, color = "grey" )
    # ax.invert_yaxis()
    plt.tight_layout()


def plotRectangles(ax, rectangles: np.array, Ymax, col="#11AA55", alpha=0.7, showIx=True):
    """ plot rectangles to matplotlib axis
    :param ax: plot axis
    :param rectangles: numpy array of rectangle corners
    :param Ym: mediabox size, max Y
    """
    yinp = rectangles.copy()
    yinp[:, 1] = Ymax - yinp[:, 1]
    yinp[:, 3] = Ymax - yinp[:, 3]
    straightLines.showRectangles(ax, yinp, color=col, alpha=alpha)
    if showIx:
        for ir in range(rectangles.shape[0]):
            ax.text(yinp[ir, 0] + 10, yinp[ir, 1] + 5, f"rect_{ir}", style='italic', alpha=0.5, color=col)
    plt.tight_layout()


def getConnections(lines, tol=0.3):
    """ make a dictionary of line connections
    Two lines are connected, if they have common points.
    (TODO : what if 4 lines connects in a cross?) - it usually does not happen.
    """
    # lineDict = dict(zip(range(lines.__len__),lines))
    lineConnects = {}
    connectArr = []
    for li in range(len(lines)):
        # lineConnects[li] = []
        connectArr.append([])
        ## TODO: this is slow for tol>0.0, you can write it to calc distance over a matrix (vectorized) to speed up.
        for ki in range(len(lines)):
            if lines[li].shareOnePoint(lines[ki], tolerance=tol):
                if f"l_{li}" not in lineConnects:
                    lineConnects[f"l_{li}"] = []
                lineConnects[f"l_{li}"].append(ki)
                connectArr[-1].append(ki)
    return lineConnects, connectArr


def getConnectionsFast(lines, tol=0.3):
    """ make a dictionary of line connections
    Two lines are connected, if they have common points.
    (TODO : what if 4 lines connects in a cross?) - it usually does not happen.
    """
    t0 = time()
    # if tol == 0:
    #     return getConnections(lines, tol= 0)
    # lineDict = dict(zip(range(lines.__len__),lines))
    lineConnects = {}
    connectArr = []
    startPoints = np.array([li.startPoint for li in lines])
    endPoints = np.array([li.endPoint for li in lines])
    for li in range(len(lines)):
        # lineConnects[li] = []
        connectArr.append([])
        start_dist = np.linalg.norm(startPoints - lines[li].startPoint, axis=1)
        se_dist = np.linalg.norm(endPoints - lines[li].startPoint, axis=1)
        es_dist = np.linalg.norm(startPoints - lines[li].endPoint, axis=1)
        end_dist = np.linalg.norm(endPoints - lines[li].endPoint, axis=1)
        smalldist = (start_dist <= tol) | (se_dist <= tol) | (es_dist <= tol) | (end_dist <= tol)
        matching_index = [ix for ix in np.where(smalldist)[0] if ix != li]
        for ki in matching_index:
            if f"l_{li}" not in lineConnects:
                lineConnects[f"l_{li}"] = []
            lineConnects[f"l_{li}"].append(ki)
            connectArr[-1].append(ki)
    print(f"connections calculated in {time() - t0} sec")
    return lineConnects, connectArr


def interfaceTerminals(lines, topy):
    """Terminal points of vertical lines that represent inputs or outputs
    :param topy: y value, lines crossing this vertical line are returned
    :return: lines crossing the topy, and it's indices in the lines list
    """
    horiz_tolerance = 5  # pixels
    verticalLines = [li for li in lines if abs(li.startPoint[0] - li.endPoint[0]) < horiz_tolerance]
    interfacemask = [(min(vi.startPoint[1], vi.endPoint[1]) < topy) & (max(vi.startPoint[1], vi.endPoint[1]) > topy) for
                     vi in verticalLines]
    vIx = np.where(interfacemask)[0]
    verticalMask = [abs(li.startPoint[0] - li.endPoint[0]) < horiz_tolerance for li in lines]
    cross_topy_mask = [(min(vi.startPoint[1], vi.endPoint[1]) < topy) & (max(vi.startPoint[1], vi.endPoint[1]) > topy)
                       for vi in lines]
    totalmask = np.array(verticalMask) & cross_topy_mask
    totIx = np.where(totalmask)[0]
    ## TODO: index in the total input
    interfaceLines = [vi for vi in verticalLines if
                      (min(vi.startPoint[1], vi.endPoint[1]) < topy) & (max(vi.startPoint[1], vi.endPoint[1]) > topy)]
    interfaceLines = np.array(verticalLines)[interfacemask]
    ## Top is the endpoint with the lower y value
    topPoint = lambda line: line.startPoint if (line.startPoint[1] < line.endPoint[1]) else line.endPoint
    interfacePoints = [topPoint(li) for li in interfaceLines]
    # out = list(zip(interfacePoints, interfaceLines, totIx))
    DL = {"terminalPoint": interfacePoints, "lines": interfaceLines, "index": totIx}
    ## make a list of dicts from dict of lists:
    out = [dict(zip(DL.keys(), t)) for t in zip(*DL.values())]
    return out


def closeToRectangle(rect, point, tol=10):
    """checks if a point is within tol distance to a rectangle
    :param rect: rectangle defined by [x_1,y_1, x_2,y_2] with corners 1 and 2
    """
    # print(f"rect received {rect}")
    rectX_b, rectX_t = min(rect[0], rect[2]), max(rect[0], rect[2])
    rectY_b, rectY_t = min(rect[1], rect[3]), max(rect[1], rect[3])
    ## point is close to a vertical side
    close2vert = (point[1] > rectY_b - tol) & (point[1] < rectY_t + tol) & (
                (abs(point[0] - rectX_b) < tol) | (abs(point[0] - rectX_t) < tol))
    ## point is close to a horizontal side
    close2hor = (point[0] > rectX_b - tol) & (point[0] < rectX_t + tol) & (
                (abs(point[1] - rectY_b) < tol) | (abs(point[1] - rectY_t) < tol))
    return close2hor | close2vert


def lineInRect(rect, line, tol):
    """ checks if the line lines within the rectangle (both endpoints is within the rectangle/ a tol increased rectangle )
    :param rect: rectange [x1, y1, x2, y2]
    :param tol: tolerance in pixels (the line can be max tol pixels far from the rectangle)
    """
    if min(line.startPoint[0], line.endPoint[0]) < (min(rect[0], rect[2]) - tol):
        return False
    elif max(line.startPoint[0], line.endPoint[0]) > (max(rect[0], rect[2]) + tol):
        return False
    elif min(line.startPoint[1], line.endPoint[1]) < (min(rect[1], rect[3]) - tol):
        return False
    elif max(line.startPoint[1], line.endPoint[1]) > (max(rect[1], rect[3]) + tol):
        return False
    else:
        return True


def controlTerminals(page, lines, rectangles=None, pixThr=250):
    """Identify control blocks as rectangles, and extract line terminals.
    :return: lines and endpoints which connects to a detected rectangle
     A list of lists for each rectangle for each terminal. For each terminal a tuple with
     (the point, the line- index, and the line object itself, and the rectangle )
    """
    if rectangles is None:
        rectangles, rinfo = extractRectangles(page, pixThr=pixThr)
    rectTerminals = []
    tol = 5
    ## TODO remove lines that are inside rectangles!
    for ri in rectangles:
        rectTerminals.append([])
        counter = 0
        # print(f"ri to close2rect {ri}")
        for li in lines:
            if closeToRectangle(ri, li.startPoint, tol):
                if not lineInRect(ri, li, tol=3):
                    rectTerminals[-1].append((li.startPoint, counter, li, ri))
                else:
                    logging.debug(f"line is close {li}, but inside the rectangle, point skipped {ri}")
            if closeToRectangle(ri, li.endPoint, tol):
                if not lineInRect(ri, li, tol=3):
                    rectTerminals[-1].append((li.endPoint, counter, li, ri))
                else:
                    logging.debug(f"line is close {li}, but inside the rectangle, point skipped {ri}")

            counter += 1
    return rectTerminals, rectangles

def label2ControlTerminals(ctrlTerminals, page ):
    """ take the rectangle/control terminals, and find the closest text-boxes (labels) corresponding to the terminals

    :param ctrTerminals: control terminals, the "rectTerminals" output of controlTerminals function
    :param page: fitz page
    :return: the controlterminals list with the label appended to each tuple
    """
    Y_before, Y_after, HSY = exportRegelStruktur.getSectionStrYLims(page, "egelstruktur", xmax=150)
    # textBlocks0 = page.get_text("blocks")
    # textBlocks = [tb for tb in textBlocks0 if (tb[1] > Y_before) & (tb[1] < Y_after) & (
    #     any(i.isalnum() for i in tb[4].replace("\n", " ")))]
    # textDict0 = page.get_text("rawdict")
    # textDict = [tb for tb in textDict0["blocks"] if (tb['bbox'][1] > Y_before) & (tb['bbox'][1] < Y_after)]
    textWords0 = page.get_text("words")
    textWords = [tb for tb in textWords0 if (tb[1] > Y_before) & (tb[1] < Y_after)]
    ### TODO : from the textDict words could be extracted
    textCenters = np.array([ [(tb[0]+tb[2])/2.0, (tb[1]+tb[3])/2.0]  for tb in textWords])
    for kb, ctBl in enumerate(ctrlTerminals):
        for kt , cti in enumerate(ctBl):
            print(f"block {kb}, terminal position = {cti[0]}.")
            dist2Text = np.linalg.norm(textCenters -cti[0], axis = 1)
            matchix = np.argmin(dist2Text)
            label = textWords[matchix][4]
            print(f"found label {label}")
            ctrlTerminals[kb][kt] = cti + (label,)
    return ctrlTerminals



def getTerminals(page, lines, connectDict, rectangles, topy):
    """ get interface and control terminals, and searching for connection
    :return : a dict with interfaceterminals as keys, and list of control blocks that are connected to this interface.
    """
    ifaceTerminals = interfaceTerminals(lines, topy)
    ifaceConnections = []
    ctrlTerminals, rectangles = controlTerminals(page, lines, rectangles=rectangles, pixThr=pixThreshold)
    iface2ctrl = {}
    for fi, ifT in enumerate(ifaceTerminals):
        print(f"terminal {ifT['terminalPoint']} connections are searched")
        lMatch = []
        ccls = findConnectedLines(connectDict, ix=ifT["index"], listMatches=lMatch)
        ifaceConnections.append((ifT['terminalPoint'], lMatch))
        iface2ctrl[fi] = []
        for ii, cterm in enumerate(ctrlTerminals):
            ctermLines = [ci[1] for ci in cterm]
            isec = set(lMatch).intersection(set(ctermLines))
            if isec.__len__() > 0:
                iface2ctrl[fi].append(ii)
    return iface2ctrl, ifaceTerminals, ctrlTerminals

def terminalConnections(ifaceTerminals, ctrlTerminals, connectDict):
    """ match interface terminals (input variable points) with control terminals"""
    ifaceConnections = []
    iface2ctrl = {}
    for fi, ifT in enumerate(ifaceTerminals):
        print(f"terminal {ifT['terminalPoint']} connections are searched")
        lMatch = []
        ccls = findConnectedLines(connectDict, ix=ifT["index"], listMatches=lMatch)
        ifaceConnections.append((ifT['terminalPoint'], lMatch))
        iface2ctrl[fi] = []
        for ii, cterm in enumerate(ctrlTerminals):
            ctermLines = [ci[1] for ci in cterm]
            isec = set(lMatch).intersection(set(ctermLines))
            if isec.__len__() > 0:
                iface2ctrl[fi].append(ii)
    return iface2ctrl

def terminalConnectionsLabelled(ifaceTerminals, ctrlTerminals, connectDict):
    """ match interface terminals (input variable points) with control terminals
    Also add the labels of the control terminals for example (x,y or w ). this is useful to determine if connection is
    input or output
    :return: for each interface a list of connected control terminals. & labels of the terminal connections
    """
    ifaceConnections = []
    iface2ctrl = {}
    for fi, ifT in enumerate(ifaceTerminals):
        print(f"terminal {ifT['terminalPoint']} connections are searched")
        lMatch = []
        ccls = findConnectedLines(connectDict, ix=ifT["index"], listMatches=lMatch)
        ifaceConnections.append((ifT['terminalPoint'], lMatch))
        ## lMatch = index of the lines which are connected to the interface
        iface2ctrl[fi] = []
        for ii, cBlock in enumerate(ctrlTerminals):
            for cTerminal  in cBlock:
                if cTerminal[1] in set(lMatch): # the index of the line of one of the terminals is matching the interface lines
                    iface2ctrl[fi].append((ii, cTerminal[4])) ## append the Block index, and the terminal label
    return iface2ctrl


def ctrl2ctrlConnections( ctrlTerminals, connectDict):
    """ find connections between control terminals
    :param ctrlTerminals: control block terminal points
    :param connectDict: dictionary with lines as keys, and indices of connected lines (graph of the line-connections)
    """
    # ifaceConnections = []
    ctrl2ctrl = []
    ## indices of lines connected to control blocks (one list per each ctrl block):
    linesOfBlocks = [ [ti[1] for ti in  cT] for cT in ctrlTerminals ]
    for fi, cB in enumerate(linesOfBlocks):
        logging.info(f"block {fi} connections are searched")

        ctrl2ctrl.append(np.array([]).astype(np.int64))
        for cT in cB: # cycle over all lines connected to block fi
            lMatch = []
            ccls = findConnectedLines(connectDict, ix=cT, listMatches=lMatch)
            # ifaceConnections.append((ifT['terminalPoint'], lMatch))
            ## the connected Blocks
            lMatch.append(cT) ## add the line itself
            ## list of connected blocks
            conBlocks = np.where([ set(lMatch).intersection(set(others)).__len__() for others in linesOfBlocks ])[0]
            conBlocks = conBlocks [ conBlocks != fi] # list of other block indices
            logging.info(f"block {fi} line {cT} connected to blocks {conBlocks} ")
            ctrl2ctrl[fi] = np.unique( np.concatenate((ctrl2ctrl[fi],conBlocks), axis = None))
    return ctrl2ctrl

def ctrl2ctrlConnectionsLabelled( ctrlTerminals, connectDict):
    """ find connections between control terminals, and also store the labels of the terminals, that are used to determine the
    information flow direction

    :param ctrlTerminals: control block terminal points
    :param connectDict: dictionary with lines as keys, and indices of connected lines (graph of the line-connections)
    """
    # ifaceConnections = []
    ctrl2ctrlL = []
    ## indices of lines connected to control blocks (one list per each ctrl block):
    linesOfBlocks = [ [ti[1] for ti in  cT] for cT in ctrlTerminals ]
    for fi, cB in enumerate(ctrlTerminals): # cycle over control blocks
        logging.info(f"block {fi} connections are searched")
        ctrl2ctrlL.append([])
        for cteri in cB: # cycle over all terminals of block fi
            cT = cteri[1] # the line of the control terminal
            termiLabel = cteri[4] # label of the terminal (x,y,w etc.)
            lMatch = []
            ccls = findConnectedLines(connectDict, ix=cT, listMatches=lMatch)
            # ifaceConnections.append((ifT['terminalPoint'], lMatch))
            ## the connected Blocks
            lMatch.append(cT) ## add the line itself
            ## list of connected blocks
            conBlocks = np.where([ set(lMatch).intersection(set(others)).__len__() for others in linesOfBlocks ])[0]
            conBlocks = conBlocks [ conBlocks != fi] # list of other block indices
            logging.info(f"block {fi} line {cT} connected to blocks {conBlocks} ")
            #ctrl2ctrlL[fi] = np.concatenate((ctrl2ctrlL[fi],(conBlocks, termiLabel) ), axis = None)
            if conBlocks.__len__() > 0:
                ctrl2ctrlL[fi] = ctrl2ctrlL[fi] + [(conBlocks, termiLabel)]
    return ctrl2ctrlL


def text2Rectangles_old(page, rectangles, maxdist=50):
    """ find closest text boxes to the rectangles
    :return: a list of tuples for each rectangle: (rectangle-coords, list of matching text-boxes)
    """
    textBlocks = page.get_text("blocks")
    # textBlocks = [(ti['lines'], ti["bbox"]) for ti in textdict["blocks"]]
    textMidpoints = [np.array([(tb[0] + tb[2]) / 2.0, (tb[1] + tb[3]) / 2.0]) for tb in textBlocks]
    out = []
    for ri in rectangles:
        rimid = np.array([(ri[0] + ri[2]) / 2.0, (ri[1] + ri[3]) / 2.0])
        width = abs(ri[2] - ri[0])
        distances = ((textMidpoints - rimid) ** 2.0).sum(axis=1) ** 0.5
        reldist = np.maximum(distances - width, 0)
        closeTextIX = np.where(reldist < maxdist)[0]
        # print(f"rectangle {ri} texts : \n {closeTextIX}")
        matchingblocks = [textBlocks[i] for i in closeTextIX] if (closeTextIX.__len__() > 0) else []
        # print(f"matching blocks {matchingblocks}")
        out.append((ri, matchingblocks))
    return out

def text2Rectangles(page, rectangles, maxdist=50):
    """ find closest text boxes to the rectangles
    :return: a list of tuples for each rectangle: (rectangle-coords, list of matching text-boxes)
    """
    textBlocks = page.get_text("words")
    # textBlocks = [(ti['lines'], ti["bbox"]) for ti in textdict["blocks"]]
    textMidpoints = [np.array([(tb[0] + tb[2]) / 2.0, (tb[1] + tb[3]) / 2.0]) for tb in textBlocks]
    out = []
    for ri in rectangles:
        rimid = np.array([(ri[0] + ri[2]) / 2.0, (ri[1] + ri[3]) / 2.0])
        width = abs(ri[2] - ri[0])
        distances = ((textMidpoints - rimid) ** 2.0).sum(axis=1) ** 0.5
        reldist = np.maximum(distances - width, 0)
        closeTextIX = np.where(reldist < maxdist)[0]
        # print(f"rectangle {ri} texts : \n {closeTextIX}")
        matchingblocks = [textBlocks[i] for i in closeTextIX] if (closeTextIX.__len__() > 0) else []
        # print(f"matching blocks {matchingblocks}")
        ## which textboxes are inside the rectangle (r)?
        textInside = lambda tb : (max(ri[0], ri[2]) > max(tb[0], tb[2])) & (min(ri[0],ri[2]) < min(tb[0], tb[2])) & \
                                 (max(ri[1], ri[3]) > max(tb[1], tb[3])) & (min(ri[1],ri[3]) < min(tb[1], tb[3]))
        textBlockInside = [tb for tb in textBlocks if textInside(tb)]
        ## alternative: sort by distance
        out.append((ri, matchingblocks, textBlockInside))
    return out


def extractRectangles(page, pixThr=250, minlen=30, tol=5, zoom_factor=3):
    """ extract rectangles from the Regelstruktur based on pixel graphics representation"""
    y_top, y_bottom = regelstrukturY(page)
    im_pil, im_np = readpdf.extractPage2Pixels(pdfdoc=None, pagenum=None, page=page,
                                               y_from=y_top / page.mediabox_size[1],
                                               y_to=y_bottom / page.mediabox_size[1], zoom=zoom_factor)
    gray = cv.cvtColor(im_np, cv.COLOR_BGR2GRAY)
    edges = gray < pixThr
    # plt.figure()
    # plt.imshow(edges)
    rectangles, slines = straightLines.getRectangles(edges, minlen=minlen,
                                                     tol=tol)  # bottom_left, top_right corners in image coordinates
    print(f"rectangles from straightlines \n: {rectangles}")
    if rectangles.__len__() == 0:
        logging.info("no rectangle found")
        return None, {'gray': gray, 'binedges': edges, 'straightLines': slines}
    ## convert back to original scale:
    rectScale = rectangles / zoom_factor
    ## convert y coordinates back to original page coordinates
    y_convert = lambda yim: y_top + yim
    y_bots = y_convert(rectScale[:, 1])
    y_tops = y_convert(rectScale[:, 3])
    rectScale[:, 1] = y_tops
    rectScale[:, 3] = y_bots
    print(f" {rectScale.shape[0]} rectangles scaled and transformed \n: {rectScale}")
    return rectScale, {'gray': gray, 'binedges': edges, 'straightLines': slines}


def findMatchingLabel(textBlocks, xval, seplines=None):
    """ find textblock (in Bezeichnung section) that matches an x value"""
    textBlocks.sort(key=lambda tb: tb[0])  # sort by the starting x value
    text_left = [tb for tb in textBlocks if tb[0] < xval]
    ## TODO find the section string also (based on separation lines, dashed or solid!!)
    return text_left[-1]


def findConnectedLines(connectDict, ix, listMatches=[]):
    """ find elements that are connected with the one with index ix. using a recursion.

    :param connectDict: a dictionary of line connections
    :param ix: array of indices. find the connections to the elements with these indices.
    :return: returns nothing, but fills the listMatches argument with the lines connected to line ix
    """
    ixkey = f'l_{ix}'
    if not ixkey in connectDict:
        return
    neigbors = connectDict[f'l_{ix}']
    if not neigbors:
        print("no more neighbors")
        return
    for nix in neigbors:  # run over neighbor indices:
        if not nix in listMatches:
            listMatches.append(nix)
            findConnectedLines(connectDict, nix, listMatches)


def getTextBlocks(lineList, section_label="ezeichnung"):
    """ get textblocks for section. Recognize solid and dashed lines, and build up hierarchy based on that
    :param section_label: the text label to find the section on the WSCAD page
    for example
    """
    Y_before_bez, Y_after_bez, HSY = exportRegelStruktur.getSectionStrYLims(page, "ezeichnung", xmax=150)
    textBlocks = page.get_text("blocks")
    textBlocks_filt = [tb for tb in textBlocks if (tb[1] > Y_before_bez) & (tb[1] < Y_after_bez) & (
        any(i.isalnum() for i in tb[4].replace("\n", " ")))]
    textBlocks_filt.sort(key=lambda tb: tb[0])
    ## get solid and dashed lines:
    ### problem big separator vertical lines are not defined in pdf as lines. Maybe rectangles?
    linesSep = [li for li in lineList if (li.startPoint[1] < Y_before_bez + 10) &
                (li.endPoint[1] > Y_after_bez - 10) & (li.lineLength() > 5)]
    linesSep2 = [li for li in lineList if (li.startPoint[1] < (Y_before_bez + 10)) &
                 (li.endPoint[1] > (Y_after_bez - 10))]


def processControlDiagram(page, pixThreshold=200, zoom_factor=3, minRctglLen=30):
    """ The main function to do the Control diagram (= BACS function structure diagram see
    VDI 3814 Blatt 4.3 / Figure 1 / section 6.) processing at once

    :param page: fitz page
    :param pixThreshold: used as threshold for the pixelgraphical processing to extract rectangles
    values between (white) 0 -255 (black)
    :param zoom_factor: used by converting the document from pdf to pixel image.
    It controls the resolution of the pixel-image.
    :param minRctglLen: minimum rectangle side length to be recognized as rectangle.
    """
    t0 = time()
    Xm, Ym = page.mediabox_size
    paths = page.get_drawings()
    lineList = lineReader.findLines(paths)  # lines from pdf
    # fLines, wLines = readpdf.getlines(doc, pnr)
    ## select lines of regelstruktur part:
    y_top, y_bottom = regelstrukturY(page)
    # startPoints = np.array([li.startPoint for li in lineList])
    ## lines of the Control block:
    linesControl = [li for li in lineList if
                    (li.startPoint[1] > y_top - 10) & (li.startPoint[1] < y_bottom) & (li.endPoint[1] < y_bottom + 10)]
    # lines45degree = [li for li in linesControl if abs(abs(
    #     (li.startPoint[0] - li.endPoint[0]) / (li.startPoint[1] - li.endPoint[1] + 1e-6)) - 1) < 0.1]
    logging.info(f"lines loaded from pdf {round(time() - t0, 2)}s")
    connectDict, connArr = getConnectionsFast(linesControl, tol=0.3)
    logging.info(f"connections calculated {round(time() - t0, 2)}s")
    ifaceTerminals = interfaceTerminals(linesControl, topy=y_top)
    ## pixel image based straight line and rectangle detection
    rectangles, info = extractRectangles(page, pixThr=pixThreshold, minlen=minRctglLen, tol=5, zoom_factor=zoom_factor)
    if rectangles is None:
        ## try again with higher pixel grayscale threshold:
        logging.error(f"no rectangles have been found wth threshold= {pixThreshold}, "
                      f"let's try with a higher threshold of {245}!")
        rectangles, info = extractRectangles(page, pixThr=245, tol=5, zoom_factor=zoom_factor)
    if rectangles is not None:
        ctrlTerminals, rectangles = controlTerminals(page, linesControl, rectangles=rectangles, pixThr=pixThreshold)
        # termPoints = np.array([ctp[0] for sublist in ctrlTerminals for ctp in sublist])
        # ax[0].scatter(termPoints[:, 0], Ym - termPoints[:, 1], s=8 ** 2, linewidths=3, marker="o", color="#111111",
        #               alpha=0.8)
        # ifTermPoints = np.array([ctp['terminalPoint'] for ctp in ifaceTerminals])
        # ax[0].scatter(ifTermPoints[:, 0], Ym - ifTermPoints[:, 1], s=7 ** 2, linewidths=3, marker="o",
        #               facecolors='none', edgecolor="#111199",
        #               alpha=0.8)
        txt2rect = text2Rectangles(page, rectangles, maxdist=10)
        txt2rect_filtered = []
        for tr in txt2rect:
            filteredTxtBlocks = [ti for ti in tr[1] if (ti[1] > y_top) & (ti[3] > y_top)]
            txt2rect_filtered.append((tr[0], filteredTxtBlocks, tr[2])) # rectangles, labels around, and labels inside
        textlabels = [ [ins[4] for ins in tf[2] ] + [tt[4].replace("\n", "") for tt in tf[1]] for tf in txt2rect_filtered]
        logging.info(f"recognized text labels \n {textlabels}")
        iface2ctrl = terminalConnections( ifaceTerminals, ctrlTerminals, connectDict)
        ctrl2ctrl =  ctrl2ctrlConnections(ctrlTerminals, connectDict) ## connections between control blocks
        ctrlTerminals = label2ControlTerminals(ctrlTerminals, page)
        ## after labelled the terminals, get the connections and labels for directions:
        ctrl2ctrlLabelled = ctrl2ctrlConnectionsLabelled(ctrlTerminals,
                                                         connectDict)  ## connections between control blocks
        iface2ctrlLabelled = terminalConnectionsLabelled(ifaceTerminals,
                                                               ctrlTerminals,
                                                               connectDict )
        ctrl2ctrlCons = c2cConnections(ctrl2ctrlLabelled)
        logging.info(f"interface-control block connections: \n{iface2ctrl}")
        return {"rectangles": rectangles, "text2rectangles": textlabels, "ctrlTerminals": ctrlTerminals,
                "interfaceTerminals": ifaceTerminals, "linesOfControl" : linesControl,
                "iface2ctrl_mapping": iface2ctrl, "iface2ctrl_labelled": iface2ctrlLabelled,
                "connectDict": connectDict, "ctrl2ctrl": ctrl2ctrl, "ctrl2ctrlConnections" : ctrl2ctrlCons }
    else:
        logging.error("no rectangle found in the control diagram")
        return None

def c2cConnections(ctrl2ctrlLabelled):
    """ from list of outgoing connections it creates a list of inter-block connections
    :param ctrl2ctrlLabelled: a list of lists obtained from terminalConnectionsLabelled.
    :return: a list of 4 tuples (block-index1, terminal-label1, block-index2, terminal-label2)
    """
    connections = []
    for i, ctrlcons_i in enumerate(ctrl2ctrlLabelled):
        if len(ctrlcons_i) > 0:
            print(f"connections from block {i}: {ctrlcons_i}")
            for ik in ctrlcons_i: # ik[0] : other block indices, ik[1]: this label
                for otherBlock in ik[0]: # otherBlock is the index of the other control block
                    other_label = [ob[1] for ob in ctrl2ctrlLabelled[otherBlock] if ob[0].__contains__(i)][0]
                    connections.append((i,ik[1],otherBlock,other_label))
    return connections


if __name__ == "__main__":

    inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/WSCAD_Examples/220621_Beispielschemen digiaktiv.pdf"
    doc = fitz.open(inpfile)  # Opens the document from a given path
    # pnr = 3        #Page number (page 1 has index 0)
    #for pnr in range(10, 18):
    for pnr in [0]:
        t0 = time()
        page = doc[pnr]
        Xm, Ym = page.mediabox_size
        paths = page.get_drawings()
        lineList = lineReader.findLines(paths)  # lines from pdf


        fLines, wLines = readpdf.getlines(doc, pnr)
        ## select lines of regelstruktur part:
        y_top, y_bottom = regelstrukturY(page)
        startPoints = np.array([li.startPoint for li in lineList])
        ## lines of the Control block:
        linesControl = [li for li in lineList if (li.startPoint[1] > y_top - 10) & (li.startPoint[1] < y_bottom) & (
                    li.endPoint[1] < y_bottom + 10)]
        lines45degree = [li for li in linesControl if abs(abs(
            (li.startPoint[0] - li.endPoint[0]) / (li.startPoint[1] - li.endPoint[1] + 1e-6)) - 1) < 0.1]
        [abs(abs((li.startPoint[0] - li.endPoint[0]) / (li.startPoint[1] - li.endPoint[1] + 1e-6)) - 1) for li in
         lines45degree]
        print(f"lines loaded from pdf {round(time() - t0, 2)}s")
        ### Here we create the plot
        fig, ax = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})
        longerlines = [li for li in lineList if
                       abs(li.startPoint[1] - li.endPoint[1]) + abs(li.startPoint[0] - li.endPoint[0]) > 5]
        # plotLines(ax, lineList, Ymax = Ym, col = "#DDDDDD")
        plotLines(ax[0], longerlines, Ymax=Ym, col="#DDDDDD")
        annot = False  ## use annotation for debugging, otherwise will be slow
        plotLines(ax[0], linesControl, Ymax=Ym, col="#BB1111", alpha=0.3, annotate=annot)
        plotLines(ax[0], lines45degree, Ymax=Ym, col="#22EE22")
        print(f"chart plotted {round(time() - t0, 2)}s")
        longLines = [li for li in linesControl if
                     abs(li.startPoint[1] - li.endPoint[1]) + abs(li.startPoint[0] - li.endPoint[0]) > 200]
        # connectDict_old, connArr_old = getConnections(linesControl)
        connectDict, connArr = getConnectionsFast(linesControl, tol=0.3)
        print(f"connections calculated {round(time() - t0, 2)}s")
        ## use the connectDict to find the connections between terminals!
        ## TODO: remove lines from connectDict, that are inside the rectangles!!

        ifaceTerminals = interfaceTerminals(linesControl, topy=y_top)
        ## get the Bezeichung to the terminals:
        Y_before_bez, Y_after_bez, HSY = exportRegelStruktur.getSectionStrYLims(page, "ezeichnung", xmax=150)
        textBlocks = page.get_text("blocks")
        textBlocks_filt = [tb for tb in textBlocks if (tb[1] > Y_before_bez) & (tb[1] < Y_after_bez) & (
            any(i.isalnum() for i in tb[4].replace("\n", " ")))]
        textBlocks_filt.sort(key=lambda tb: tb[0])
        iTermStrings = [findMatchingLabel(textBlocks_filt, it['terminalPoint'][0]) for it in ifaceTerminals]
        [tb[4] for tb in textBlocks_filt]
        ###
        ifaceConnections = []
        for ifT in ifaceTerminals:
            print(f"terminal {ifT['terminalPoint']} connections are searched")
            lMatch = []
            ccls = findConnectedLines(connectDict, ix=ifT["index"], listMatches=lMatch)
            ifaceConnections.append((ifT['terminalPoint'], lMatch))
        print(f"the following interface connections found \n{ifaceConnections}")
        print(f"interface terminals extracted {round(time() - t0, 2)}s")
        pixThreshold = 200
        ## pixel image based straight line and rectangle detection
        rectangles, info = extractRectangles(page, pixThr=pixThreshold)
        zoom_factor = 3

        origsize = tuple(np.flip([int(gi / zoom_factor) for gi in info["gray"].shape]))
        gray_origsize = cv.resize(info["gray"] * 1.0, dsize=origsize, interpolation=cv.INTER_CUBIC)
        ax[1].imshow(info["gray"])
        # plt.figure()
        # plt.imshow(graybin)
        ## TODO: how to smartly select the right gray pixel threshold? Sometimes rectangles have different color level!
        if rectangles is None:
            ## try again with higher pixel grayscale threshold:
            logging.error(f"no rectangles have been found wth threshold= {pixThreshold}, "
                          f"let's try with a higher threshold of {245}!")
            rectangles, info = extractRectangles(page, pixThr=245, tol=5)
            f2, ax2 = plt.subplots(2, 1)
            ax2[0].imshow(info["binedges"])
            slines = info["straightLines"]
            xvals = slines[:, [0, 2]].transpose()
            yvals = slines[:, [1, 3]].transpose()
            ax2[1].plot(xvals, yvals, c='#AA1111', alpha=0.7)
            ax2[1].set_title(f"page {pnr + 1} grayscale image for edge detection. Threshold increased to 245")
        print(f"rectangles extracted {round(time() - t0, 2)}s")
        if rectangles is not None:
            ## 776: [760, 763, 764],
            # plotLines(ax,     [linesControl[ix] for ix in [776, 760, 763, 764]], Ymax=Ym, col="#1111FF")
            print(rectangles)
            plotRectangles(ax[0], rectangles, Ymax=Ym, alpha=0.97)
            ctrlTerminals, rectangles = controlTerminals(page, linesControl, rectangles=rectangles, pixThr=pixThreshold)
            # termPoints = np.array([ np.array([ctr[0] for ctr in  ctrT]) for ctrT in  ctrlTerminals ]).flatten()
            # cps = [ [ctr[0] for ctr in  ctrT] for ctrT in  ctrlTerminals ]
            termPoints = np.array([ctp[0] for sublist in ctrlTerminals for ctp in sublist])
            ax[0].scatter(termPoints[:, 0], Ym - termPoints[:, 1], s=8 ** 2, linewidths=3, marker="o", color="#111111",
                          alpha=0.8)
            ifTermPoints = np.array([ctp['terminalPoint'] for ctp in ifaceTerminals])
            ax[0].scatter(ifTermPoints[:, 0], Ym - ifTermPoints[:, 1], s=7 ** 2, linewidths=3, marker="o",
                          facecolors='none', edgecolor="#111199",
                          alpha=0.8)
            ax[0].set_title(f"page : {pnr + 1} detected {rectangles.__len__()} Control- rectangles")
            txt2rect = text2Rectangles(page, rectangles, maxdist=10)
            txt2rect_filtered = []
            for tr in txt2rect:
                filteredTxtBlocks = [ti for ti in tr[1] if (ti[1] > y_top) & (ti[3] > y_top)]
                txt2rect_filtered.append((tr[0], filteredTxtBlocks))
            textlabels = [[tt[4].replace("\n", "") for tt in tf[1]] for tf in txt2rect_filtered]
            print(f"recognized text labels \n {textlabels}")
            iface2ctrl = terminalConnections(ifaceTerminals, ctrlTerminals, connectDict)
            iface2ctrlB, ifaceTerminals, ctrlTerminals = getTerminals(page, linesControl, connectDict, rectangles,
                                                                     topy=y_top)
            print(f"interface-control block connections: \n{iface2ctrl}")
        else:
            print("no rectangle found in the control diagram")

    if False:
        ### plot the original rectangles that are defined in the pdf
        qus = [pi for pi in paths if pi['items'][0][0] == "qu"]
        pdfrects = np.array([[qu["rect"].x0, qu["rect"].y0, qu["rect"].x1, qu["rect"].y1] for qu in qus])
        plotRectangles(ax[0], pdfrects, Ymax=Ym, alpha=0.97, col="#995511")

        ####
        import importlib

        importlib.reload(straightLines)
        pixThr = 200
        y_top, y_bottom = regelstrukturY(page)
        im_pil, im_np = readpdf.extractPage2Pixels(pdfdoc=None, pagenum=None, page=page,
                                                   y_from=y_top / page.mediabox_size[1],
                                                   y_to=y_bottom / page.mediabox_size[1], zoom=zoom_factor)
        gray = cv.cvtColor(im_np, cv.COLOR_BGR2GRAY)
        edges = gray < pixThr
        # plt.figure()
        # plt.imshow(edges)
        rectangles, lines = straightLines.getRectangles(info["binedges"], minlen=30,
                                                        tol=3)  # bottom_left, top_right corners in image coordinates
        print(f"rectangles from straightlines \n: {rectangles}")
        print(f" {rectangles.shape[0]} rectangles scaled and transformed \n: {rectangles}")
        rectangles, info = extractRectangles(page, minlen=30, pixThr=245, tol=1)
        slines = info["straightLines"]
        rectans = straightLines.detecRectangles(slines, tol=1)

    ## for testing:
    if False:
        pixThr = 250
        pnr = 11
        page = doc[pnr]
        y_top, y_bottom = regelstrukturY(page)
        zoom_factor = 3
        im_pil, im_np = readpdf.extractPage2Pixels(pdfdoc=None, pagenum=None, page=page,
                                                   y_from=y_top / page.mediabox_size[1],
                                                   y_to=y_bottom / page.mediabox_size[1], zoom=zoom_factor)
        gray = cv.cvtColor(im_np, cv.COLOR_BGR2GRAY)
        edges = gray < pixThr
        plt.figure()
        plt.imshow(gray)

        a = np.array([[1., 2.3], [1.5, 4.2], [1.3, 3.4]])
        bx = np.array([[1., 2.3, 3.2], [1.5, 4.2, 2.4]])
        by = np.array([[-0.3, 1.9, 4.4], [3.5, 3.2, 4.9]])
        plt.figure()
        plt.plot(bx, by)

        li = 1561
        for ki in range(len(lines)):
            if lines[li].shareOnePoint(lines[ki]):
                print(f"line {ki} touches {li}")
        print(linesControl[li])
        print(linesControl[526])
