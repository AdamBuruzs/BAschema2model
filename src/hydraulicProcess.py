#  Copyright (c) 2023.   Adam Buruzs
## process the Hydraulic schema (BACS system representation). Find the labels of the measurement sensors

import logging, sys

from src import exportRegelStruktur

logging.basicConfig(stream = sys.stdout, level = logging.DEBUG)
import fitz
import src.lineReader as lineReader
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Qt5Agg")
from time import time
from src import lineConnects


def text2Points(page, pointsXY: np.array, ymin = None, ymax = None, Nret = 3  ):
    """ Get closest text-boxes to points
    :param pointsXY: a numpy array with points X and Y coordinates.
    :param ymin- max: filter the text-boxes to this range
    :param Nret: the number of closest points to return
    :return: for each point return the closest text-boxes
    """
    paths = page.get_drawings()
    textBlocks0 = page.get_text("blocks")
    textBlocks = [tb for tb in textBlocks0 if (tb[1] >= ymin) & (tb[1] < ymax) & (
        any(i.isalnum() for i in tb[4].replace("\n", " ")))]
    # center points of the text-boxes
    textCorners = np.array([tb[0:4] for tb in  textBlocks])
    textCenters = np.stack( (textCorners[:,[0,2]].mean(axis = 1), textCorners[:,[1,3]].mean(axis = 1)), axis = 1 )
    closestLabels = []
    for xy in pointsXY:
        distance = np.linalg.norm( np.abs(textCenters - xy), axis = 1)
        closest_ix = np.where( distance == min(distance))[0]
        closestN = np.argsort(distance) [0:Nret]
        closestLabels.append( [ ( textBlocks[ix][4], distance[ix] ) for ix in  closestN ])
    return closestLabels


def hydraulicConnections(page, doplot = True, title = "page xy", precision= 3,
                         vhconTol = 15, minLegth = 15):
    """ process the hydraulic diagrams. It deals with vertical dashed lines, and
    New: it also checks the connecting horizontel dashed lines that are connected to the vertical lines through a corner.

    :param vhconTol: tolerance of vertical-horizontal line connections
    :param minLegth: minimum length of the vertical dashed lines, otherwise the line is omitted
    :param precision: used for vertical/horizontal dashed line detection.´
    :param doplot: if true, a visualization of the detected components and keypoints are visualized. useful for debugging
    """

    ## TODO: process rectangular corners, and vertical dashed lines, and build up connections with the vertical dashed lines
    Xm, Ym = page.mediabox_size
    paths = page.get_drawings()
    lineList = lineReader.findLines(paths) #lines from pdf

    ## todo: filter the lines of the Hydraulic schema:
    Y_before, Y_after, HSY = exportRegelStruktur.getSectionStrYLims(page, "Anlage", xmax = 200)
    ## page.search_for(sectionString)
    print(f"Hydraulic schema in range y = [{Y_before} - {Y_after}]")
    linesOfSchema = [li for li in lineList if (li.startPoint[1] > Y_before) & (li.startPoint[1] < Y_after) ]

    ## get the vertical lines:
    verticalLDict = lineReader.convertLines(
                    lineReader.sortDict(
                        lineReader.findCorrespondingLines(
                            linesOfSchema, xOrY=False, precision= precision)), xOrY=False, spacing = 22)
    horizontalLDict = lineReader.convertLines(
                    lineReader.sortDict(
                        lineReader.findCorrespondingLines(
                            linesOfSchema, xOrY=True, precision= precision)), xOrY=True)
    ### selecting the dashed vertical lines
    #[vi.startPoint[0] == vi.endPoint[0] for ki, vi in verticalDictx.items()]
    dashedV_lines = list({ ki:vi for (ki, vi) in verticalLDict.items() if vi.style == "dashed"}.values() )
    ## TODO: detect horizontal lines, and check if endpoints are close to Top-Popints of the vertical lines. if yes they are candidates of connections
    dashedH_lines = list({ki: vi for (ki, vi) in horizontalLDict.items() if vi.style == "dashed"}.values())

    ## TODO: sometimes paths in the pdf are dashed lines itself!
    biglen = 70
    bigLongPaths = [pi for pi in paths if (abs(pi["rect"].bl.y - pi["rect"].tr.y) + abs(pi["rect"].bl.x - pi["rect"].tr.x) > biglen)
                   & (pi['items'][0][0] == 'l')]
    dashedpaths = [bi for bi in bigLongPaths if bi['dashes'].__len__() > 5]
    path2line = lambda path, style: lineReader.line([path['items'][0][1].x, path['items'][0][1].y],
                                                    [path['items'][0][2].x, path['items'][0][2].y], path["color"],
                                                    path["width"], style=style)
    dashedLongLines = [path2line(dp, "dashed") for dp in dashedpaths]

    logging.info(f" Hydraulic diagram detected {len(dashedV_lines)} dashed vertical lines and {len(dashedH_lines)} horizontal")
    logging.info(f" And additionally {len(dashedLongLines)} dashed lines from the pdf document")
    tol = 2.0
    dashedV_lines = dashedV_lines + [dh for dh in dashedLongLines if abs(dh.endPoint[0] - dh.startPoint[0]) < tol ]
    dashedH_lines = dashedH_lines + [dh for dh in dashedLongLines if abs(dh.endPoint[1] - dh.startPoint[1]) < tol]

    if doplot:
        fig, ax = plt.subplots(2,1, gridspec_kw={'height_ratios': [6, 1]})
        #fig, ax = plt.subplots(1, 1 )
        lineConnects.plotLines(ax[0], linesOfSchema, Ymax=Ym, col="#333333", alpha=0.4, annotate=False)
        lineConnects.plotLines(ax[0], dashedV_lines, Ymax=Ym, col="#BB1111", alpha=0.8, annotate=True)
        lineConnects.plotLines(ax[0], dashedLongLines, Ymax=Ym, col="#2211BB", alpha=0.8, annotate=True)
    y_vals = [ max(li.startPoint[1], li.endPoint[1]) for li in  dashedV_lines ]
    max_y = np.quantile(y_vals,0.95) ## around the bottom of the hydraulic part
    ## keep only vertical lines, which are touching the bottom of the hydraulic diagram:
    lines2Connect = [ li for li in dashedV_lines if
                      ((max(li.startPoint[1], li.endPoint[1]) ) >= max_y) & (li.lineLength() > minLegth) ]
    topPoints = np.array(
        [li.startPoint if (li.startPoint[1] < li.endPoint[1]) else li.endPoint for li in lines2Connect])
    HlinesCoords = np.array([li.startPoint + li.endPoint for li in dashedH_lines])

    ## TODO: make it nicer, a separate object with set of lines, following path (connections) and returning points
    matchVerticalLines = []
    verticalMatchPoints = []
    for tp in topPoints:
        distMat = HlinesCoords - np.tile(tp, 2)
        mindist = np.min([np.linalg.norm(distMat[:, 0:2], axis=1), np.linalg.norm(distMat[:, 2:], axis=1)], axis=0)
        vLineWithinTolerance = np.where(mindist < vhconTol)[0]
        if vLineWithinTolerance.__len__() > 0:
            ixclosest = vLineWithinTolerance[0]
            matchVerticalLines.append(dashedH_lines[ixclosest])
            distances = distMat[ixclosest, :]
            if np.linalg.norm(distances[0:2]) < np.linalg.norm(distances[2:]):
                verticalMatchPoints.append(HlinesCoords[ixclosest,  2:])
            else:
                verticalMatchPoints.append(HlinesCoords[ixclosest, 0:2])
        else:
            matchVerticalLines.append(None)
            verticalMatchPoints.append(None)
    if doplot:
        lineConnects.plotLines(ax[0], lines2Connect, Ymax=Ym, col="#11BB11", alpha=0.8, annotate=True)
        ax[0].set_title(f"page : {title} Hydraulic schema {lines2Connect.__len__()} detected connectors")
        ax[0].scatter(topPoints[:, 0], Ym - topPoints[:, 1], s=7 ** 2, linewidths=3, marker="o", facecolors='none',
                  edgecolor="#111199", alpha=0.6)
        lineConnects.plotLines(ax[0], [mvl for mvl in matchVerticalLines if mvl is not None], Ymax=Ym, col="#11BBBB",
                               alpha=0.8, annotate=True)
        Vmatches = np.array([ vmp for vmp in verticalMatchPoints if vmp is not None ])
        ax[0].scatter(Vmatches[:, 0], Ym - Vmatches[:, 1], s=7** 2, linewidths=3, marker="o", facecolors='none',
                      edgecolor="#11CC99", alpha=0.6)
        for tp in range(len(topPoints)):
            xmid, ymid = topPoints[tp]
            ax[0].text(xmid, Ym - ymid, f"TopPoint_{tp}", style='italic', alpha=0.7, color="#333399")
    labels2TopPoints = text2Points(page, topPoints, ymin = Y_before, ymax = Y_after )
    labels2VertPoints = [ None if vmp is None else text2Points(page, [vmp], ymin = Y_before, ymax = Y_after )[0] for vmp in verticalMatchPoints]
    ## look for closest label with "-" character starting
    mergedFirstLabels = []
    for i in range(len(labels2VertPoints)):
        labelarr = labels2TopPoints[i] if labels2VertPoints[i] is None else labels2TopPoints[i] + labels2VertPoints[i]
        filteredLabels = [lab[0] for lab in  labelarr  if lab[0].startswith("-")]
        if filteredLabels.__len__() > 0:
            mergedFirstLabels .append( filteredLabels[0])
        else:
            mergedFirstLabels.append("--")
    res_dict= {"lines": lines2Connect, "topPoints" : topPoints, "labels" : labels2TopPoints,
               "matchingVerticalLines": matchVerticalLines,
               "verticalMatchPoints":verticalMatchPoints, "labels2VertPoints" : labels2VertPoints,
               "mergedFirstLabels" : mergedFirstLabels}
    out = [dict(zip(res_dict.keys(),t)) for t in  zip(* res_dict.values())]
    #outfilt = [hc for hc in out if hc['lines'].lineLength() > minLegth]
    return out

if __name__ == "__main__":

    inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/WSCAD_Examples/220621_Beispielschemen digiaktiv.pdf"
    doc = fitz.open(inpfile) #Opens the document from a given path
    # pnr = 3        #Page number (page 1 has index 0)
    #for pnr in range(10,17):
    for pnr in [11]:
        t0 = time()
        page = doc[pnr]
        Xm, Ym = page.mediabox_size
        paths = page.get_drawings()

        loadCode = False
        if loadCode :

            lineList = lineReader.findLines(paths) #lines from pdf

            ## todo: filter the lines of the Hydraulic schema:
            Y_before, Y_after, HSY = exportRegelStruktur.getSectionStrYLims(page, "Anlage", xmax = 200)
            ## page.search_for(sectionString)
            print(f"Hydraulic schema in range y = [{Y_before} - {Y_after}]")
            linesOfSchema = [li for li in lineList if (li.startPoint[1] > Y_before) & (li.startPoint[1] < Y_after) ]

            ## get the vertical lines:
            verticalDictx = lineReader.convertLines(
                            lineReader.sortDict(
                                lineReader.findCorrespondingLines(
                                    linesOfSchema, xOrY=False, precision=0)), xOrY=False)
            print(f"found {verticalDictx.__len__()} vertical lines")
            ### TODO: select the dashed vertical lines
            [vi.startPoint[0] == vi.endPoint[0] for ki, vi in verticalDictx.items()]
            dashedV_lines = list({ ki:vi for (ki, vi) in verticalDictx.items() if vi.style == "dashed"}.values() )
            horizontalLDict = lineReader.convertLines(
                lineReader.sortDict(
                    lineReader.findCorrespondingLines(
                        linesOfSchema, xOrY=True, precision=0)), xOrY=True)
            dashedH_lines = list({ki: vi for (ki, vi) in horizontalLDict.items() if vi.style == "dashed"}.values())
            HlinesCoords = np.array( [ li.startPoint + li.endPoint for li in  dashedH_lines])

            fig, ax = plt.subplots(2,1, gridspec_kw={'height_ratios': [6, 1]})
            #fig, ax = plt.subplots(1, 1 )
            lineConnects.plotLines(ax[0], linesOfSchema, Ymax=Ym, col="#333333", alpha=0.4, annotate=False)
            lineConnects.plotLines(ax[0], dashedV_lines, Ymax=Ym, col="#BB1111", alpha=0.8, annotate=True)
            y_vals = [ max(li.startPoint[1], li.endPoint[1]) for li in  dashedV_lines ]
            max_y = np.quantile(y_vals,0.95)
            lines2Connect = [ li for li in dashedV_lines if (max(li.startPoint[1], li.endPoint[1]) ) >= max_y]
            lineConnects.plotLines(ax[0], lines2Connect, Ymax=Ym, col="#11BB11", alpha=0.8, annotate=True)
            ax[0].set_title(f"page : {pnr + 1} Hydraulic schema {lines2Connect.__len__()} detected connectors")

            topPoints = np.array([ li.startPoint if (li.startPoint[1] < li.endPoint[1]) else li.endPoint for li in lines2Connect])

            vhconTol = 15
            matchVerticalLines = []
            verticalMatchPoints = []
            for tp in topPoints:
                distMat = HlinesCoords - np.tile(tp,2)
                mindist = np.min( [ np.linalg.norm(distMat[:, 0:2], axis=1) , np.linalg.norm(distMat[:, 2:], axis=1)], axis = 0)
                vLineWithinTolerance =  np.where(mindist < vhconTol)[0]
                if vLineWithinTolerance.__len__() > 0:
                    ixclosest = vLineWithinTolerance[0]
                    matchVerticalLines.append(dashedH_lines[ixclosest])
                    distances = distMat[ixclosest, :]
                    if np.linalg.norm(distances[0:2]) < np.linalg.norm(distances[2:]):
                        verticalMatchPoints.append(HlinesCoords[ixclosest, 2:])
                    else:
                        verticalMatchPoints.append(HlinesCoords[ixclosest, 0:2])
                else:
                    matchVerticalLines.append(None)
                    verticalMatchPoints.append(None)
            lineConnects.plotLines(ax[0], [mvl for mvl in matchVerticalLines if mvl is not None], Ymax=Ym, col="#11BBBB", alpha=0.8, annotate=True)
            ax[0].scatter(topPoints[:, 0], Ym - topPoints[:, 1], s=7 ** 2, linewidths=3, marker="o", facecolors='none',
                          edgecolor="#111199", alpha=0.6)
            Vmatches = np.array([ vmp for vmp in verticalMatchPoints if vmp is not None ])
            ax[0].scatter(Vmatches[:, 0], Ym - Vmatches[:, 1], s=7** 2, linewidths=4, marker="o", facecolors='none',
                          edgecolor="#11CC99", alpha=0.6)
            labels2TopPoints = text2Points(page, topPoints, ymin = Y_before, ymax = Y_after, Nret = 3 )
            # ax.annotate(i,(xmid, Ymax - ymid))
            for ki in range(len(topPoints)):
                tlabel = " ".join([ li[0] for li in  labels2TopPoints[ki]])
                ax[0].text(topPoints[ki,0], Ym - topPoints[ki,1], tlabel, style='italic', alpha=0.7, color="grey")

        hcs = hydraulicConnections(page, doplot = True,
                                   title = f"hydraulicConnections function page {pnr}", minLegth=15 )
        hcsfilt = [ hc for hc in  hcs if hc['lines'].lineLength() > 10 ]
        # ax[0].scatter([725], Ym - np.array([227]), s=7** 2, linewidths=6, marker="o", facecolors='none',
        #               edgecolor="#DD0011", alpha=0.6)