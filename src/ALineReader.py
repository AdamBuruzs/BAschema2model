# written by Elias
import fitz
from operator import itemgetter
import math

class line:     
    def __init__(self, start, end, color, width, style = "full"):   #Line parameters
        self.startPoint = start
        self.endPoint = end
        self.color = color
        self.width = width
        self.style = style

    def startx(self):
        return self.startPoint[0]
    
    def starty(self):
        return self.startPoint[1]

    def endx(self):
        return self.endPoint[0]
    
    def endy(self):
        return self.endPoint[1]

    def lineLength(self):   #Returns the length of a line (could be usefull to determine the type of dashing, like dots or small/big lines)
        return math.sqrt((self.endx()-self.startx())*(self.endx()-self.startx())+(self.endy()-self.starty())*(self.endy()-self.starty()))

    def printLine(self):    #Returns info of a given line
        print(f"Start: {self.startPoint}, End: {self.endPoint}, color: {self.color}, width: {self.width}, style: {self.style}")



def findLines(paths):   #Finds all lines on a PDF-Page
    returnList = list()
    for path in paths:
        for item in path["items"]:
            if item[0] == "l":
                returnList.append(line([item[1].x,item[1].y], [item[2].x, item[2].y], path["color"], path["width"]))
    return returnList   #Returns a list of all lines (class line)


def findCorrespondingLines(lineList, xOrY):
    """ finds vertical lines or horizontal lines and groups them into a dict with y or x levels as keys"""
    returnDict = dict()
    if xOrY:
        for elem in lineList:
            if elem.starty() == elem.endy():    #Checks if line is vertical
                try:
                    returnDict[elem.starty()].append(elem)
                except:
                    returnDict[elem.starty()] = [elem]
    else:
        for elem in lineList:
            if elem.startx() == elem.endx():    #Checks if line is horizontal
                try:
                    returnDict[elem.startx()].append(elem)
                except:
                    returnDict[elem.startx()] = [elem]
    return returnDict                       #Returns a dict with x or y value as key and all corresponding lines in it


def sortDict(unsortedDict): #Sorts the lists of lines in a dict for their startingpoint 
    sortedDict = dict()
    for key in unsortedDict:
        if(len(unsortedDict[key]) > 1):
            sortedDict[key] = sorted(unsortedDict[key], key = lambda line: line.startPoint)
        else:
            sortedDict[key] = unsortedDict[key]
    return sortedDict


def convertLines(sortedLineDict, xOrY): #Converts dashed lines into one line with style "dashed" 
    convertedLines = dict()
    counter = 0
    spacing = 12    #The greater spacing allows to detect dashed lines with increased distance between the dashes 
    if xOrY:
        for key in sortedLineDict:
            if(len(sortedLineDict[key]) > 1):
                startPoint = sortedLineDict[key][0].startx()
                endPoint = sortedLineDict[key][0].endx()
                lineCounter = 0
                for num in range(1, len(sortedLineDict[key])):
                    if abs(endPoint-sortedLineDict[key][num].startx()) < spacing:
                        endPoint = sortedLineDict[key][num].endx()
                        lineCounter += 1
                    else:
                        if lineCounter >= 2:
                            convertedLines["Line%i" % counter] = line([startPoint, sortedLineDict[key][num].starty()], [endPoint, sortedLineDict[key][num].endy()], sortedLineDict[key][num].color, sortedLineDict[key][num].width, style = "dashed")
                        else:
                            convertedLines["Line%i" % counter] = line([startPoint, sortedLineDict[key][num].starty()], [endPoint, sortedLineDict[key][num].endy()], sortedLineDict[key][num].color, sortedLineDict[key][num].width, style = "full")
                        lineCounter = 0
                        counter += 1
                        startPoint = sortedLineDict[key][num].startx()
                        endPoint = sortedLineDict[key][num].endx()
                    if num == len(sortedLineDict[key]) - 1:
                        if lineCounter >= 2:
                            convertedLines["Line%i" % counter] = line([startPoint, sortedLineDict[key][num].starty()], [endPoint, sortedLineDict[key][num].endy()], sortedLineDict[key][num].color, sortedLineDict[key][num].width, style = "dashed")
                        else:
                            convertedLines["Line%i" % counter] = line([startPoint, sortedLineDict[key][num].starty()], [endPoint, sortedLineDict[key][num].endy()], sortedLineDict[key][num].color, sortedLineDict[key][num].width, style = "full")
                        lineCounter = 0
                        counter += 1 
            else:
                convertedLines["Line%i" % counter] = sortedLineDict[key][0]
                counter += 1
        return convertedLines
    else:
        for key in sortedLineDict:
            if(len(sortedLineDict[key]) > 1):
                startPoint = sortedLineDict[key][0].starty()
                endPoint = sortedLineDict[key][0].endy()
                lineCounter = 0
                for num in range(1, len(sortedLineDict[key])):
                    if abs(endPoint-sortedLineDict[key][num].starty()) < spacing:
                        endPoint = sortedLineDict[key][num].endy()
                        lineCounter += 1
                    else:
                        if lineCounter >= 2:
                            convertedLines["Line%i" % counter] = line([sortedLineDict[key][num].startx(), startPoint], [sortedLineDict[key][num].endx(), endPoint], sortedLineDict[key][num].color, sortedLineDict[key][num].width, style = "dashed")
                        else:
                            convertedLines["Line%i" % counter] = line([sortedLineDict[key][num].startx(), startPoint], [sortedLineDict[key][num].endx(), endPoint], sortedLineDict[key][num].color, sortedLineDict[key][num].width, style = "full")
                        lineCounter = 0
                        counter += 1
                        startPoint = sortedLineDict[key][num].starty()
                        endPoint = sortedLineDict[key][num].endy()
                    if num == len(sortedLineDict[key]) - 1:
                        if lineCounter >= 2:
                            convertedLines["Line%i" % counter] = line([sortedLineDict[key][num].startx(), startPoint], [sortedLineDict[key][num].endx(), endPoint], sortedLineDict[key][num].color, sortedLineDict[key][num].width, style = "dashed")
                        else:
                            convertedLines["Line%i" % counter] = line([sortedLineDict[key][num].startx(), startPoint], [sortedLineDict[key][num].endx(), endPoint], sortedLineDict[key][num].color, sortedLineDict[key][num].width, style = "full")
                        lineCounter = 0
                        counter += 1 
            else:
                convertedLines["Line%i" % counter] = sortedLineDict[key][0]
                counter += 1
        return convertedLines

    
def drawLines(listOfLineDict, page, pdfSaveName = "Output.pdf"):
    """Draws lines on PDF-Page the lines have to be provided in a list of dicts"""
    outpdf = fitz.open()
    outpage = outpdf.new_page(width=page.rect.width, height=page.rect.height)
    shape = outpage.new_shape()
    for lineDict in listOfLineDict:
        for elem in lineDict:
            try:
                point1 = fitz.Point(lineDict[elem].startx(), lineDict[elem].starty())
                point2 = fitz.Point(lineDict[elem].endx(), lineDict[elem].endy())
                shape.draw_line(point1, point2)
                if lineDict[elem].style == "dashed":
                    shape.finish(color = (1, 0.6 , 0.5))
                else:
                    shape.finish()
            except:
                for item in lineDict[elem]:
                    point1 = fitz.Point(item.startx(), item.starty())
                    point2 = fitz.Point(item.endx(), item.endy())
                    shape.draw_line(point1, point2)
                if item.style == "dashed":
                    shape.finish(color = (1, 0.6 , 0.5))
                else:
                    shape.finish()

    shape.commit()
    outpdf.save(pdfSaveName)
    
#Setup Main:

if __name__ == "__main__":

    inpfile = "C:/Users/BuruzsA/Documents/projects/Digiaktiv/220621_Beispielschemen digiaktiv.pdf"
    doc = fitz.open(inpfile) #Opens the document from a given path
    pnr = 5         #Page number (page 1 has index 0)
    page = doc[pnr]
    paths = page.get_drawings()


    finalDictx = convertLines(sortDict(findCorrespondingLines(findLines(paths), False)), False) #Dict including all vertical lines with the correct style
    finalDicty = convertLines(sortDict(findCorrespondingLines(findLines(paths), True)), True)   #Dict including all horizontal lines with the correct style


    drawLines([finalDictx, finalDicty], page, "./results/Test6.pdf")  #Draws both dicts on a PDF-Page
