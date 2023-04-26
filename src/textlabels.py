## finding the text elements, and text headers from the "Bezeichnung" part

import logging, sys

from src import exportRegelStruktur, lineConnects, readpdf

logging.basicConfig(stream = sys.stdout, level = logging.DEBUG)
import fitz
import src.lineReader as lineReader
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Qt5Agg")
from time import time


def getTextBlocks( page, section_label = "ezeichnung"):
    """ get textblocks for section Bezeichnung. Extract rectangles from pdf, and find the main header labels based on that
    :param section_label: the text label to find the section on the WSCAD page
    for example "ezeichnung" - this finds "Bezeichnung" and "bezeichnung" also
    """
    paths = page.get_drawings()
    Y_before_bez, Y_after_bez, HSY = exportRegelStruktur.getSectionStrYLims(page, section_label, xmax=150)
    textBlocks = page.get_text("blocks")
    textBlocks_filt = [tb for tb in textBlocks if (tb[1] > Y_before_bez) & (tb[1] < Y_after_bez) & (
        any(i.isalnum() for i in tb[4].replace("\n", " ")))]
    ### TODO : this will miss some text-boxes!
    textBlocks_filt.sort(key=lambda tb: tb[0])
    ## get solid and dashed lines:
    ### problem big separator vertical lines are not defined in pdf as lines. Maybe rectangles?
    # linesSep = [li for li in lineList if (li.startPoint[1] < Y_before_bez+10) &
    #             (li.endPoint[1] > Y_after_bez-10) &   (li.lineLength() > 5) ]
    # linesSep2 = [li for li in lineList if (li.startPoint[1] < (Y_before_bez + 10)) &
    #             (li.endPoint[1] > (Y_after_bez - 10) ) ]
    allRectangles = [pi for pi in paths if pi['items'][0][0] == "qu"]
    rects = [ri for ri in  allRectangles if (ri['rect'][0] > 10) & (ri['rect'][1] < Y_before_bez +5) & (ri['rect'][3] > Y_after_bez - 5) ]
    rects.sort(key = lambda r: r['rect'][0])
    headers = []
    ### Anlagenkenzeichnen have "-" sign as first character!
    for ri in rects: # iterate over the found rectangles, these are containing the labels
        left_x = ri["rect"][0]
        right_x = ri["rect"][2]
        ## labels that are right side of the left vertical of the rectangle:
        labelsInBox = [ tf for tf in textBlocks_filt if (tf[0] > left_x) & (tf[0] < right_x) ]
        ## TODO: some  textbox is missed! those where Typ is filled??
        headers.append({"x_range": [left_x, right_x], "labels": labelsInBox})
    return headers

def getTextBlocksInSection( page, section_label = "Typ"):
    """ get text-blocks for any section.
    :param section_label: the text label to find the section on the WSCAD page
    for example "ezeichnung" - this finds "Bezeichnung" and "bezeichnung" also
    """
    paths = page.get_drawings()
    Y_before_bez, Y_after_bez, HSY = exportRegelStruktur.getSectionStrYLims(page, sectionString =section_label, xmax=150, usemid = True)
    textBlocks = page.get_text("blocks")
    textBlocks_filt = [tb for tb in textBlocks if (0.5*(tb[1]+ tb[3]) > Y_before_bez) & (0.5*(tb[1]+ tb[3]) < Y_after_bez) & (
        any(i.isalnum() for i in tb[4].replace("\n", " ")))]
    ### TODO : this will miss some text-boxes!
    textBlocks_filt.sort(key=lambda tb: tb[0])
    return textBlocks_filt


if __name__ == "__main__":

    inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/220621_Beispielschemen digiaktiv.pdf"
    doc = fitz.open(inpfile) #Opens the document from a given path
    # pnr = 3        #Page number (page 1 has index 0)
    #for pnr in range(10,17):
    for pnr in [16]:
        t0 = time()
        page = doc[pnr]
        Xm, Ym = page.mediabox_size
        paths = page.get_drawings()
        lineList = lineReader.findLines(paths) #lines from pdf
        fLines, wLines = readpdf.getlines(doc, pnr)
        ## select lines of regelstruktur part:
        y_top, y_bottom = lineConnects.regelstrukturY(page)
        startPoints = np.array([li.startPoint for li in lineList])
        ## lines of the Control block:
        linesControl = [li for li in lineList if (li.startPoint[1] > y_top-10) & (li.startPoint[1] < y_bottom) &  (li.endPoint[1] < y_bottom +10 ) ]
        lines45degree = [li for li in linesControl if abs(abs((li.startPoint[0] - li.endPoint[0])/(li.startPoint[1] - li.endPoint[1]+ 1e-6)) -1) < 0.1 ]
        [abs(abs((li.startPoint[0] - li.endPoint[0]) / (li.startPoint[1] - li.endPoint[1] + 1e-6)) -1 ) for li in lines45degree]
        print(f"lines loaded from pdf {round(time() -t0,2)}s")
        ### Here we create the plot
        fig, ax = plt.subplots(2,1, gridspec_kw={'height_ratios': [3, 1]})
        longerlines = [li for li in lineList if
                       abs(li.startPoint[1] - li.endPoint[1]) + abs(li.startPoint[0] - li.endPoint[0]) > 5]
        #plotLines(ax, lineList, Ymax = Ym, col = "#DDDDDD")
        lineConnects.plotLines(ax[0], longerlines, Ymax=Ym, col="#DDDDDD")
        annot = False ## use annotation for debugging, otherwise will be slow
        lineConnects.plotLines(ax[0], linesControl, Ymax = Ym, col ="#BB1111", alpha = 0.3, annotate=annot)

        ifaceTerminals = lineConnects.interfaceTerminals(linesControl, topy=y_top)
        qus = [pi for pi in paths if pi['items'][0][0] == "qu"]
        pdfrects = np.array([[qu["rect"].x0, qu["rect"].y0, qu["rect"].x1, qu["rect"].y1] for qu in qus])
        lineConnects.plotRectangles(ax[0], pdfrects, Ymax=Ym, alpha=0.97, col="#995511")
        ax[0].set_title(f"page : {pnr + 1} & rectangles")
        textLabels = getTextBlocks(page,  section_label = "ezeichnung")
        [print(f"{ti['x_range']} : { [tt[4] for tt in ti['labels']]}" ) for ti in textLabels]
        ifTermPoints = np.array([ctp['terminalPoints'] for ctp in ifaceTerminals])
        ax[0].scatter(ifTermPoints[:, 0], Ym - ifTermPoints[:, 1], s=7 ** 2, linewidths=3, marker="o", facecolors='none',
                      edgecolor="#111199",
                      alpha=0.8)
        for ift in ifaceTerminals:
            x_ift = ift['terminalPoints'][0]
            tlabels = [tl for tl in textLabels if (tl["x_range"][0] < x_ift) & (tl["x_range"][1] > x_ift) ]
            if tlabels.__len__() > 0:
                labels = tlabels[0]
                ift["labels"] = [li[4] for li in labels["labels"]]
            else:
                ax[0].scatter(ift["terminalPoints"][0], Ym - ift["terminalPoints"][1], s=8 ** 2, linewidths=3, marker="o",
                              facecolors='none',
                              edgecolor="#BB1111",
                              alpha=0.8)
                ift["labels"] = None
        for ift in (ifaceTerminals):
            print(ift)

