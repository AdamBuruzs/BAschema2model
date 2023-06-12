#  Copyright (c) 2023.   Adam Buruzs
## The main file to process the whole WSCAD image.
## calling the other scripts:

import logging, sys

logging.basicConfig(stream = sys.stdout, level = logging.DEBUG)
import fitz

# from src import ALineReader as lineReader
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Qt5Agg")
from src import lineReader
from src import hydraulicProcess
from src import textlabels
from src import lineConnects
from src.readpdf import getSchemaNumber
import json
import jinja2
import os


class DataEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, lineReader.line):
            return f"line: {np.round(np.array(obj.startPoint),4)} - {np.round(np.array(obj.endPoint),4)} s:{obj.style}"
        if isinstance(obj, np.int64):
            return int(obj)
        return json.JSONEncoder.default(self, obj)

def processPage(doc, pagenum = 16, doplot= True):
    """ merge all functions for page processing
    :param pagenum: page number starting from 1

    :returns:  ## interfaces : terminal points on top of the Regelstruktur part.
     all information extracted from the "Bezeichnung" and "Anlage" sections
      ## controls: the information extracted from the Regelstruktur part (block diagrams and connections)
    """
    page = doc[pagenum-1]
    controls = lineConnects.processControlDiagram(page, pixThreshold=200, zoom_factor=3, minRctglLen=30)
    # controls["ctrlTerminals"] = lineConnects.label2ControlTerminals(controls["ctrlTerminals"], page)
    hydrau = hydraulicProcess.hydraulicConnections(page, doplot= doplot, title =f"page {pagenum}",
                                                   precision= 0, minLegth=20)
    textLabels =  textlabels.getTextBlocks( page, section_label = "ezeichnung")
    types = textlabels.getTextBlocksInSection(page, section_label= "Typ")
    ifaces = controls["interfaceTerminals"]
    ## The x positions of the vertical hydraulic Connectors
    hydraX = np.array([hi["lines"].startPoint[0] for hi in hydrau])
    # for hi in hydrau:
    #     hi['labels'] = [hif for hif in hi['labels'] if hif.startswith("-") ]
    for ii,ifa in enumerate(ifaces):
        textLabs = [tl for tl in textLabels if (tl["x_range"][0] < ifa['terminalPoint'][0]) &  (tl["x_range"][1] > ifa['terminalPoint'][0])]
        textLab = textLabs[0]
        ifa["textLabel"] = textLab
        ifa["matchingLabels"] = [tli[4] for tli in textLab['labels'] if (tli[0] < ifa['terminalPoint'][0]) &  (tli[2] > ifa['terminalPoint'][0]) ]
        min_lab_x = min([lab[0] for lab in textLab['labels']])
        ifa["labelHeader"] = [tli[4] for tli in textLab['labels'] if tli[0] == min_lab_x ]
        ifa["type"] =  [tli[4] for tli in types if (tli[0] < ifa['terminalPoint'][0]) &  (tli[2] > ifa['terminalPoint'][0]) ]
        ## find the hydraulic connection with the smallest distance .
        ## That is wrong!! you should use the Bezeichnung block to find the corect matching
        matchingHIX_closest = np.argmin(abs(hydraX - ifa["terminalPoint"][0]))
        ## the index of the matching vertical line on the hydraulic diagram
        matchingHIX = np.where( [ (textLab["x_range"][0] < hx) & ( hx < textLab["x_range"][1] ) for hx in hydraX ] )[0]
        logging.info(f"matchingHIX: {matchingHIX}")
        if matchingHIX.__len__() > 1 :
            logging.error("multiple hydraulic lines match the interface terminal")
        if matchingHIX.__len__() == 0:
            logging.error(f"no hydraulic connection to that text-block found {textLab} \n {ifa}")
        hydraulicIndex = matchingHIX[0]
        ifa["hydraulic"] = hydrau[hydraulicIndex]
        ifa["ctrlBlockIndices"] = controls["iface2ctrl_mapping"][ii]
    return ifaces, controls

def plotControls(ifaces, controls, page):
    """ make a plot about extracted control blocks"""
    Xm, Ym = page.mediabox_size
    fig, ax = plt.subplots(2, 1, gridspec_kw={'height_ratios': [3, 1]})
    lineConnects.plotRectangles(ax[0], controls["rectangles"], Ymax=Ym, alpha=0.97)
    termPoints = np.array([ctp[0] for sublist in controls["ctrlTerminals"] for ctp in sublist])
    ax[0].scatter(termPoints[:, 0], Ym - termPoints[:, 1], s=8 ** 2, linewidths=3, marker="o", color="#111111",
                  alpha=0.8)
    ifTermPoints = np.array([ctp['terminalPoint'] for ctp in ifaces])
    ax[0].scatter(ifTermPoints[:, 0], Ym - ifTermPoints[:, 1], s=7 ** 2, linewidths=3, marker="o",
                  facecolors='none', edgecolor="#111199",
                  alpha=0.8)
    ## transformed flipped coordinates
    rectsCoords = [1, -1, 1, -1] * controls["rectangles"] + [0, Ym, 0, Ym]
    for ii, texti in enumerate(controls["text2rectangles"]):
        filt_text = [ti for ti in texti if not (ti[0] in ["x", "y", "z"]) ]
        ax[0].text(rectsCoords[ii, 0] - 5,rectsCoords[ii, 1] + 15,
                   ":".join(filt_text), style='italic', alpha=0.5, color="#AA3388")
    for ctlB in controls["ctrlTerminals"]:
        for tei in ctlB:
            filt_text = [ti for ti in texti if not (ti[0] in ["x", "y", "z"]) ]
            ax[0].text(tei[0][0]+2, Ym - tei[0][1]+ 2,
                   tei[4], style='italic', alpha=0.5, color="#BB8888")
    lineConnects.plotLines(ax[0], controls["linesOfControl"], Ymax=Ym, col="#BB1111", alpha=0.3, annotate=False)

def toText(ifaces, controls):
    """ convert data to text"""
    outText = json.dumps({"interfaces": ifaces, "controlBlocks": controls},
                         cls=DataEncoder)
    return outText

def toJointDiagram(ifaces, controls, title = "", outfile = "../joint_dia/output/diagram.js"):
    """create jointjs diagram from the interfaces and control blocks"""
    environment = jinja2.Environment(loader=jinja2.FileSystemLoader("../joint_dia/templates/"))
    template = environment.get_template("HMSRDiagram.j2") ## jinja template
    hydroNames =  [ " ".join( ifa["hydraulic"]["mergedFirstLabels"]  ).replace("\n", ":") for ifa in ifaces]
    textLabels =  [ "<" + " ".join(ifa["labelHeader"]).replace("\n", " ") + ">\\n" +
                    " ".join(ifa["matchingLabels"]).replace("\n", "\\n") + "\\n" +
                    "|| " + ("" if len(ifa["type"]) == 0 else " ".join(ifa["type"]).replace("\n", " ")) + "||"
                    for ifa in ifaces]
    ctrlBlockCount = len(controls["rectangles"])
    icmap = controls['iface2ctrl_mapping']
    lcon = [[(k, vi) for vi in v] for k, v in icmap.items()]
    IBconnects = [item for sublist in lcon for item in sublist] # interface to control blocks conenctions
    iclmap = controls['iface2ctrl_labelled']
    lcon = [[(k,) + vi for vi in v] for k, v in iclmap.items()]
    IBLconnects = [item for sublist in lcon for item in sublist] # interface - control block, terminal label
    IBLCoded = [(ibl[0], ibl[1], "OUT" if ibl[2][0] == "y" else "IN" ) for ibl in  IBLconnects]
    minx, miny = controls["rectangles"].min(axis = 0)[:2]
    maxx, maxy = controls["rectangles"].max(axis = 0)[2:]
    labelsFiltered = [[ct for ct in tl if not ct[0] in ["x", "y", "w"]] for tl in controls["text2rectangles"] ]
    ctrlBlockLabels = [ lb[0] if len(lb) > 0 else "None" for lb in  labelsFiltered ]
    ctrlBlocks = [ ((controls["rectangles"][ci,0] - minx)/(maxx-minx) ,
                    (controls["rectangles"][ci,3] - miny)/(maxy-miny),
                    ctrlBlockLabels[ci])
                   for ci in range(len(controls["rectangles"]))]
    logging.info(f"js visualizing control blocks \n {ctrlBlocks}")
    conTmp = [ [(i,vv) for vv in v ] for i,v in  enumerate(controls['ctrl2ctrl']) if len(v) > 0 ]
    # CCconnects = [vl for sublist in conTmp for vl in sublist]
    CCconnects = [(coni[0], coni[2]) for coni in controls['ctrl2ctrlConnections'] if
                  (coni[1][0] == "y") or (coni[3][0] in ["x", "w"])]  # input label is only x.. or w..
    content = template.render(hydroNames = hydroNames, textLabels = textLabels,
                              ctrlBlocks = ctrlBlocks,
                              IBconnects = IBconnects,
                              IBLcon = IBLCoded,
                              CCconnects = CCconnects,
                              title = title)

    #outfile = f"./joint_dia/output/{outfile}"
    with open(outfile, mode="w", encoding="utf-8") as message:
        message.write(content)
        print(f"... wrote {outfile}")


if __name__ == "__main__":

    loop = False
    #inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/WSCAD_Examples/220621_Beispielschemen digiaktiv.pdf"
    #inpfile = "C:/Users/BuruzsA/PycharmProjects/diagram2model/webapp/static/uploads/pages/2022-12-15-2123.pdf"
    #inpfile = "webapp/static/uploads/pages/HZK101.pdf"
    inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/WSCAD_Examples/WSCAD_MSR-Schema_28092022.pdf"
    doc = fitz.open(inpfile)  # Opens the document from a given path

    if not loop:
        pagenum = 1
        page = doc[pagenum-1]
        # ifaces2, controls2 = processPage(doc, pagenum=pagenum)
        ifaces, controls = processPage(doc, pagenum= pagenum)
        outText = json.dumps( {"interfaces": ifaces, "controlBlocks": controls},
                              cls = DataEncoder )
        toJointDiagram(ifaces, controls, title= f"page {pagenum}", outfile= "./joint_dia/output/diagram.js")
        plotControls(ifaces, controls, page)
        outText = toText(ifaces, controls)
    ## print the json to a file
    else:
        inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/220621_Beispielschemen digiaktiv.pdf"
        fileTag = "Beispielschemen_digiaktiv"
        for pagenum in range(1, doc.page_count + 1) : #range(1, doc.page_count + 1):  # range(doc.page_count):
            page = doc[pagenum-1]
            try:
                ifaces, controls = processPage(doc, pagenum=pagenum)
                outText = json.dumps({"interfaces": ifaces, "controlBlocks": controls},
                                     cls=DataEncoder)
                outfile = f"./webapp/static/uploads/diagrams/{fileTag}_p{pagenum}.js"
                toJointDiagram(ifaces, controls, title=f"page {pagenum}", outfile = outfile)
                plotControls(ifaces, controls, page)
                outText = toText(ifaces, controls)
                with open(f'./webapp/static/uploads/schemaText/{fileTag}_p{pagenum}.txt', 'w') as f:
                    f.write(outText)
                pagedoc = fitz.open()
                pagedoc.insert_pdf(doc, from_page = pagenum - 1, to_page = pagenum - 1)
                pdffile = os.path.join("../webapp", "static", "uploads", "pages", f"{fileTag}_p{pagenum}.pdf")
                pagedoc.save(pdffile)
                logging.info(f"page {pagenum} processed and saved")
                mat = fitz.Matrix(0.2,0.2)
                pix = page.get_pixmap(matrix=mat)  # render page to an image
                pix.save(f"./webapp/static/uploads/icons/{fileTag}-p{pagenum}.png")
            except:
                logging.error(f"Error on page {pagenum }")
                logging.error(sys.exc_info() )
