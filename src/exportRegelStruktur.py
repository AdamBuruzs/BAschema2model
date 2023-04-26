#  Copyright (c) 2023.   Adam Buruzs
# from src import ALineReader
from src import lineReader
from src import readpdf
import fitz
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Qt5Agg")
import math


## TODO: find y coordinates of "RegelStruktur" section
## using labels: "Typ", "Index"

def findWords(page, word):      #Returns a list of all rectangles that contain the word
    return page.search_for(word)

def getSectionStrYLims(page, sectionString ="Regelstruktur", xmax = 1000, usemid = True):
    """ get the y coordinates for the Reglerstruktur part
    :param sectionString: the name of the section to search for, for example "Regelstruktur"
    finds the y coordinates of the closest horizontal lines
    """
    allfinds = page.search_for(sectionString)
    if allfinds.__len__() == 1:
        label_Regel_coords = allfinds[0]
    else :
        print(f"multiple match found for {sectionString}:\n {allfinds}")
        allfinds.sort(key=lambda r: r[0])
        label_Regel_coords = [af for af in allfinds if af[0] < xmax][0]

    print(f"coordinates of label {sectionString} : {label_Regel_coords}")
    paths = page.get_drawings()
    lines = lineReader.findLines(paths)
    print
    ## horizontal section divider lines
    HSlines = [li for li in lines if (abs(li.endPoint[0] - li.startPoint[0]) > 25) & (min(li.startPoint[0] ,li.endPoint[0]) < 30)  ]
    HSY = [li.startPoint[1] for li in HSlines]
    if usemid : ## the pivot Y point: extracted from the label
        Ylabel =  (label_Regel_coords[1] + label_Regel_coords[3])/2.0
    else: # use the bottom-right point
        Ylabel = label_Regel_coords[-1]
    Y_after_Regel = min([yi for yi in HSY if yi > Ylabel])
    Y_before_Regel = max([yi for yi in HSY if yi < Ylabel])
    return Y_before_Regel, Y_after_Regel, HSY


if __name__ == "__main__":
    file = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/220621_Beispielschemen digiaktiv.pdf"
    pdf_file = fitz.open(file)
    print(f"opened a file with {pdf_file.page_count} pages")
    for pix in range(pdf_file.__len__()):
    #for pix in range(14,17):
        page = pdf_file[pix]
        imsonpage = pdf_file.get_page_images(pno = pix, full=False)
        print(f"ims on page {pix}: {imsonpage.__len__()}")
        pagetext = page.get_text()
        textElems = pagetext.split("\n")
        # part for the Anlage
        #im_pil, im_np = extractPage2Pixels(pdf_file, pagenum=pix, y_from=0.12, y_to=0.63, zoom=3)
        label_Typ_coords = page.search_for("Typ")
        label_Index_coords = page.search_for("Index")
        if label_Index_coords.__len__() ==0:
            print(f"string 'Index' not found search for lines around Regelstruktur")
            Y_before_Regel, Y_after_Regel, HYvals = getSectionStrYLims(page, sectionString ="Regelstruktur")
            y_bott = Y_after_Regel
        else:
            y_bott =label_Index_coords[0].top_left.y
        print(f"page  {pix} : Typ position {label_Typ_coords[0].bottom_right.y}")
        y_top = math.ceil(label_Typ_coords[0].bottom_right.y) +1
        try:
            print(f"Index position {y_bott}")
            y_bottom = math.floor(y_bott)
        except:
            print(f" anchor labels not found")
            y_bottom = page.mediabox_size[1] - 67
        print(f"medbox size {page.mediabox_size[1]}, Regel between {y_top}, {y_bottom}")

        # ## show the Regelstruktur part:
        im_pil, im_np = readpdf.extractPage2Pixels(pdf_file, pagenum=pix, y_from=y_top / page.mediabox_size[1],
                                                   y_to=y_bottom/page.mediabox_size[1], zoom=3)
        plt.figure()
        plt.imshow(im_np)
        plt.title(f"regler {pix+1}")
        im_pil.save(f"./ControlDiagrams/page{pix}Regler.jpg")