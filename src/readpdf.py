import fitz # PyMuPDF
import io
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Qt5Agg")

def extractPageImages(file = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/220621_Beispielschemen digiaktiv.pdf",
                      pageIndex = 3):
    """ trial to extract images from a page of a pdf document. """
    # open the file
    pdf_file = fitz.open(file)
    page = pdf_file[pageIndex]
    image_list = page.get_images()
    # printing number of images found in this page
    if image_list:
        print(f"[+] Found a total of {len(image_list)} images in page {pageIndex}")
    else:
        print("[!] No images found on page", pageIndex)
    for image_index, img in enumerate(page.get_images(), start=1):
        # get the XREF of the image
        xref = img[0]
        # extract the image bytes
        base_image = pdf_file.extract_image(xref)
        image_bytes = base_image["image"]
        # get the image extension
        image_ext = base_image["ext"]
        # load it to PIL
        image = Image.open(io.BytesIO(image_bytes))
        # save it to local disk
        image.save(open(f"images/image{pageIndex + 1}_{image_index}.{image_ext}", "wb"))
    return page

def extractPage2Pixels(pdfdoc: fitz.fitz.Document, pagenum = 0, page = None, format= "PNG",
                       y_from = 0.0, y_to = 1.0, zoom = 3 ):
    """ Extract a page from a multi-page pdf document
    :param pdfdoc: pdfdoc = fitz.open(file)
    :param pagenum: the page number that you want to extract
    """
    if page is None:
        page = pdfdoc[pagenum]
    width,height = page.mediabox.width, page.mediabox.height
    clipRect = fitz.IRect(0, y_from *height , width, y_to * height )
    zoom_mat = fitz.Matrix(zoom,zoom)
    impx = page.get_pixmap(clip = clipRect, matrix = zoom_mat)
    pixpil = impx.pil_tobytes(format=format, optimize=False)
    pil_image = Image.open(io.BytesIO(pixpil))
    np_image = np.array(pil_image)
    #image.show()
    ## TODO: how to control the resolution/pixels of the output?
    ## TODO: can we snip out some rectangle and convert just part of the pdf?
    return pil_image, np_image


def getlines(pdfdoc: fitz.fitz.Document, pagenum = 0):
    """ extract lines from pdf document"""
    page = pdfdoc[pagenum]
    draws = page.get_drawings()
    allines = [ dr for dr in draws if dr["items"][0][0] == "l" ]
    wlines = [li for li in allines if li["width"] > 0]
    #someval = 743.9225463867188
    #sel = [wl for wl in wlines if wl['rect'].bottom_left[0] == 743.9225463867188]
    ## TODO: get only lines within an yrange
    ## TODO: filter out 0 length lines?
    return allines, wlines

def plotLines(lines, plotlabels = True):
    """ create matplotlib plot from lines"""
    fig = plt.figure()
    for li in lines:
        xv = [li["items"][0][1].x, li["items"][0][2].x]
        yv = [li["items"][0][1].y, li["items"][0][2].y]
        plt.plot(xv,yv)
        if plotlabels:
            plt.text(np.array(xv).mean(),np.array(yv).mean(), li['seqno'],style='italic', alpha= 0.5, color = "grey" )
    plt.gca().invert_yaxis()
    plt.tight_layout()

def plotLinesOfPage(pdf_file, pagenum):
    """ extract lines from page pagenum, and plot them on matplotlib.
    Use it to test which lines are recognized by  fitz / PyMuPDF
    :param pdf_file: fitz file object = fitz.open(file)
    :return:
    """
    allines, wlines = getlines(pdf_file, pagenum= pagenum)
    line_lengths = np.array([np.linalg.norm(np.array(li["items"][0][1])-np.array(li["items"][0][2])) for li in allines ])
    posLen = line_lengths > 0.0
    linesWithLength = np.array(allines)[posLen]
    plotLines(linesWithLength, plotlabels=True)
    plt.title(f"page of pdf {pagenum+1}")

if __name__ == "__main__":
    file = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/220621_Beispielschemen digiaktiv.pdf"
    pdf_file = fitz.open(file)
    print(f"opened a file with {pdf_file.page_count} pages")
    for pix in range(0,10):
        page = pdf_file[pix]
        imsonpage = pdf_file.get_page_images(pno = pix, full=False)
        print(f"ims on page {pix}: {imsonpage.__len__()}")
        pagetext = page.get_text()
        textElems = pagetext.split("\n")
        # part for the Anlage
        #im_pil, im_np = extractPage2Pixels(pdf_file, pagenum=pix, y_from=0.12, y_to=0.63, zoom=3)
        ## show the Regelstruktur part:
        im_pil, im_np = extractPage2Pixels(pdf_file, pagenum=pix, y_from=836/page.mediabox_size[1],
                                       y_to=945/page.mediabox_size[1], zoom=3)
        plt.figure()
        plt.imshow(im_np)
        plt.title(f"regler {pix+1}")
        im_pil.save(f"./img_templates/page{pix}Regler.jpg")
    if False:
        page = extractPageImages(file = file,
                          pageIndex=3, format = "PNG")
    ims = pdf_file.get_page_images(pno=3)
    # impx = page.getp_pixmap()
    # pixpil = impx.pil_tobytes(format="JPEG", optimize=False)
    #
    # #image = Image.frombytes('RGBA', (128, 128), pixpil)
    # image = Image.open(io.BytesIO(pixpil))
    # image.show()
    zoomfact = 2
    im_pil, im_np = extractPage2Pixels(pdf_file, pagenum = 5,y_from = 0.0, y_to = 1.0, zoom = zoomfact)
    plt.figure()
    plt.title("entire page")
    plt.imshow(im_np)
    clip_Anlage = fitz.IRect(33, 127 , 1410, 613 )
    allines, wlines = getlines(pdf_file, pagenum= 9)
    val,counts = np.unique(np.array([wl['rect'].bottom_left[0] for wl in allines]), return_counts = True)
    bigcounts = np.where(counts > 10)
    val[bigcounts] * zoomfact ## these are the x coordinate of dashed vertical lines!
    [dline for dline in allines if abs(dline['rect'].bottom_left[0] - 620.5932006) < 0.001 ]
    line_lengths = np.array([np.linalg.norm(np.array(li["items"][0][1])-np.array(li["items"][0][2])) for li in allines ])
    posLen = line_lengths > 0.0
    linesWithLength = np.array(allines)[posLen]
    plotLines(linesWithLength)
    plt.gca().invert_yaxis()
    def zeroLenButSize(line):
        len = np.linalg.norm(np.array(line["items"][0][1])-np.array(line["items"][0][2]))
        size = line["rect"].width + line["rect"].height
        zeroLenButSize = (len == 0) & (size > 0.0)
        return zeroLenButSize
    zlBS = [zeroLenButSize(li) for li in allines]
    l1 = [li for li in allines if (222.0 < li["rect"].tr[0]) & (li["rect"].tr[0] < 223.0) ]

    plotLinesOfPage(pdf_file, pagenum = 5)
    im_pil, im_np = extractPage2Pixels(pdf_file, pagenum=pix, y_from=836/page.mediabox_size[1],
                                       y_to=945/page.mediabox_size[1], zoom=3)
    plt.figure