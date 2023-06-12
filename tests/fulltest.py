# parsing the diagrams in /Digiaktiv_MSR-Schema.pdf file, and storing results in files
import src.fullProcess as fullProcess
import logging, sys

logging.basicConfig(stream = sys.stdout, level = logging.DEBUG)
import fitz
# import Elias_DigiAktive_V100822.Programm.lineReader as lineReader

# from src import ALineReader as lineReader
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Qt5Agg")
from src import lineReader
from src import hydraulicProcess
from src import textlabels
from src import lineConnects
import src.readpdf
import src.fullProcess as fullProcess
from src.fullProcess import processPage
from src.fullProcess import DataEncoder
import src.diagram2html as diagram2html
import json
import jinja2
import os



# inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/WSCAD_Examples/Digiaktiv_MSR-Schema.pdf"
inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/WSCAD_Examples/220621_Beispielschemen digiaktiv.pdf"
doc = fitz.open(inpfile)  # Opens the document from a given path

# inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/WSCAD_Examples/Digiaktiv_MSR-Schema.pdf"
fileTag = os.path.basename(inpfile).replace(".pdf", "")
# outdir = f"C:/Users/BuruzsA/PycharmProjects/diagram2model/results/digiaktiv_MSR_examples"
outdir = r"C:\Users\BuruzsA\Documents\projects\Digiaktiv\BASchema2mod\test"

try:
    os.makedirs(os.path.join(outdir, "diagrams" ), exist_ok = True)
    os.makedirs(os.path.join(outdir, "pages" ), exist_ok = True)
    os.makedirs(os.path.join(outdir, "icons" ), exist_ok = True)
    os.makedirs(os.path.join(outdir, "schemaText" ), exist_ok = True)
    os.makedirs(os.path.join(outdir, "diagramHTML" ), exist_ok = True)
except:
    logging.error(sys.exc_info())

#for pagenum in range(2, doc.page_count + 1):  # range(1, doc.page_count + 1):  # range(doc.page_count):
for pagenum in range(6,8):
    page = doc[pagenum - 1]
    try:
        ifaces, controls = fullProcess.processPage(doc, pagenum=pagenum)
        zeichungsNummer = src.readpdf.getSchemaNumber(page)
        outText = json.dumps({"diagramNumber": zeichungsNummer, "interfaces": ifaces, "controlBlocks": controls},
                             cls=fullProcess.DataEncoder)
        with open(f'{outdir}/schemaText/{fileTag}_p{pagenum}.txt', 'w') as f:
            f.write(outText)
        outjsfile = f"{outdir}/diagrams/{fileTag}_p{pagenum}.js"
        znum =  zeichungsNummer.replace('\n', '')
        fullProcess.toJointDiagram(ifaces, controls, title=f"page {pagenum}, ZNum:{znum}", outfile=outjsfile)
        diagram2html.makeHtml(jsfile = outjsfile,
             outdir = os.path.join(outdir, "diagramHTML") )
        fullProcess.plotControls(ifaces, controls, page)
        #outText = fullProcess.toText(ifaces, controls)

        pagedoc = fitz.open()
        pagedoc.insert_pdf(doc, from_page=pagenum - 1, to_page=pagenum - 1)
        pdffile = os.path.join(outdir,"pages", f"{fileTag}_p{pagenum}.pdf")
        pagedoc.save(pdffile)
        logging.info(f"page {pagenum} processed and saved")
        mat = fitz.Matrix(0.2, 0.2)
        pix = page.get_pixmap(matrix=mat)  # render page to an image
        pix.save(f"{outdir}/icons/{fileTag}-p{pagenum}.png")

    except:
        logging.error(f"Error on page {pagenum}")
        logging.error(sys.exc_info())


# if __name__ == "__debug_page9__":
if False:
    pi = 8
    pagenum = pi +1
    page = doc[pi]
    hydrau = hydraulicProcess.hydraulicConnections(page, doplot= True, title =f"page {pagenum}",
                                                   precision= 0, minLegth=20)
    controls9 = lineConnects.processControlDiagram(page, pixThreshold=200, zoom_factor=3, minRctglLen=30)
    print(controls9['ctrl2ctrl'])
    print(controls9['ctrl2ctrlConnections'])

    ## why it does not find "-D5" to rectangle on page 9?
    textBlocks = page.get_text("words")

    ctrl2ctrlLabelled = controls9["ctrl2ctrlConnections"]

    # connections = []
    # for i, ctrlcons_i in enumerate(ctrl2ctrlLabelled):
    #     if len(ctrlcons_i) > 0:
    #         print(f"connections {ctrlcons_i}")
    #         for ik in ctrlcons_i: # ik[0] : other block indices, ik[1]: this label
    #             for otherBlock in ik[0]: # otherBlock is the index of the other control block
    #                 other_label = [ob[1] for ob in ctrl2ctrlLabelled[otherBlock] if ob[0].__contains__(i)][0]
    #                 connections.append((i,ik[1],otherBlock,other_label))


    ## TODO! make directed arrows in jointjs charts from controls["ctrl2ctrlLabelled"]
    import src.readpdf
    for pagenum in range(2, doc.page_count + 1):  # range(1, doc.page_count + 1):  # range(doc.page_count):
        # for pagenum in [9]:
        page = doc[pagenum - 1]
        snum = src.readpdf.getSchemaNumber(page)
        print(f"{pagenum} : {snum}")