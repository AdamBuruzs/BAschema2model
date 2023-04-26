# original written by Elias Widauer, modified by Adam Buruzs
import fitz
import math
import numpy as np

class line:
    """A class line object has two points and expresses a line on a x-y plane"""

    def __init__(self, start: list, end: list, color: list, width: float, style = "full") -> None:   #Line parameters
        """Builds a line object
        
        :param start: List containing coordinates [x, y]
        :param end: List containing coordinates [x, y]
        :param color: List with color information [R, G, B] with values 0-1
        :param width: Float number representing the width of a line
        :param style: Style of a line (full, dashed, ...)"""
        
        self.startPoint = start
        self.endPoint = end
        self.color = color
        self.width = width
        self.style = style

    def startx(self) -> float:
        """:return: Starting point x-coordinate"""
        return self.startPoint[0]
    
    def starty(self) -> float:
        """:return: Staring point y-coordinate"""
        return self.startPoint[1]

    def endx(self) -> float:
        """:return: Ending point x-coordinate"""
        return self.endPoint[0]
    
    def endy(self) -> float:
        """:return: Ending point y-coordinate"""
        return self.endPoint[1]

    def lineLength(self) -> float:
        """:return: Float length of a line"""
        return math.sqrt((self.endx()-self.startx())*(self.endx()-self.startx())+(self.endy()-self.starty())*(self.endy()-self.starty()))

    def hasPoint(self, point) -> bool:
        """Checks if a point is either start or end point
            
        :param point: Point [x, y]
        :return: Boolean"""
        
        return (self.startPoint == point or self.endPoint == point)

    def returnOtherPoint(self, point) -> list:
        """Returns the other point of a line if line.hasPoint
        
        :param point: Point [x, y]
        :return: Point [x, y]"""

        if self.hasPoint(point):
            if self.startPoint == point:
                return self.endPoint
            else:
                return self.startPoint
        else:
            return point

    def shareOnePoint(self, other, tolerance= 0.0) -> bool:
        """Checks if two different line objects share one but not both points
        Adam added tolerance parameter. Some lines are not exactly matching!
        :param other: Line object
        :param tolerance: tolerance value for checking distance between endpoints. the distance < tolerance is the criteria to match points.
        :return: Boolean"""
        if tolerance == 0.0: # function of Elias
            return (self.startPoint == other.startPoint or self.startPoint == other.endPoint or self.endPoint == other.startPoint or self.endPoint == other.endPoint) and not ((self.startPoint == other.startPoint and self.endPoint == other.endPoint) or (self.endPoint == other.startPoint and self.startPoint == other.endPoint))
        else: ## function of Adam
            ## this is a bit slow if you calculate NxN times
            samepoints =  lambda p1,p2 : np.linalg.norm(np.array(p1) - p2) < tolerance
            for thisp in [self.startPoint, self.endPoint]:
                for otherp in [other.startPoint, other.endPoint]:
                    if samepoints(thisp, otherp):
                        return True
            return False


    def isHorizontal(self) -> bool:
        """Checks if a line is horizontal
        :return: Boolean"""

        return (self.starty() == self.endy())

    def isVertical(self) -> bool:
        """Checks if a line is vertical
        :return: Boolean"""

        return (self.startx() == self.endx())

    def pointOnLine(self, point: list) -> bool:
        """Checks if a given point is on a line
        Note: Only vertical or horizontal lines!
        
        :param point: Point [x, y]
        :return: Boolean"""

        if self.isHorizontal():
            return (point[1] == self.starty() and ((point[0] >= self.startx() and point[0] <= self.endx()) or (point[0] >= self.endx() and point[0] <= self.startx())))
        elif self.isVertical():
            return (point[0] == self.startx() and ((point[1] >= self.starty() and point[1] <= self.endy()) or (point[1] >= self.endy() and point[1] <= self.starty())))
        else:
            print("No vertical/horizontal line given. Return is therefor FALSE")
            return False
            
    def __str__(self) -> str: 
        """:return: String information about line object"""   
        return (f"(Start: {self.startPoint}, End: {self.endPoint}, Length: {self.lineLength()} color: {self.color}, width: {self.width}, style: {self.style})")
    
    def __eq__ (self, other) -> bool:
        """Checks if two lines have the same starting and ending points
        
        :param other: Line object
        :return: Boolean"""

        return ((self.startPoint == other.startPoint and self.endPoint == other.endPoint) or (self.endPoint == other.startPoint and self.startPoint == other.endPoint))

    def __add__(self, other):
        """Adds two lines that share one point
        Note: In case that they don't have a matching point it returns self object
        
        :param other: Line object
        :return: Line object"""

        if(self.startPoint == other.startPoint and self.endPoint is not other.endPoint) or (self.endPoint == other.endPoint and self.startPoint is not other.startPoint) or (self.startPoint == other.endPoint and self.endPoint is not other.startPoint) or (self.endPoint == other.startPoint and self.startPoint is not other.endPoint):
            if(self.startPoint == other.startPoint):
                return line(self.endPoint, other.endPoint, self.color, self.width, self.style)
            elif(self.startPoint == other.endPoint):
                return line(self.endPoint, other.startPoint, self.color, self.width, self.style)
            elif(self.endPoint == other.endPoint):
                return line(self.startPoint, other.startPoint, self.color, self.width, self.style)
            elif(self.endPoint == other.startPoint):
                return line(self.startPoint, other.endPoint, self.color, self.width, self.style)
        else:
            return self


def findLines(paths) -> list:
    """This function finds all lines on a PDF.
    
    :param paths: Fitz object that stores all information about all objects on a PDF page
    :return: List containing all lines each stored as object line """

    returnList = list()
    for path in paths:
        for item in path["items"]:
            if item[0] == "l":
                returnList.append(line([item[1].x, item[1].y], [item[2].x, item[2].y], path["color"], path["width"]))
    return returnList


def lineFilter(lineList: list, leftTopCorner: list, rightBotCorner: list, endInclude = False, cleanPoints = False) -> list:    	
    """This function filters for lines that are in a given area.
    
    :param lineList: List of line objects
    :param leftTopCorner: Point top left [x, y]
    :param rightBotCorner: Point bottom right [x, y]
    :param endInclude: Boolean (True -> both line points have to be in the bountaries)
    :param cleanPoints: Boolean (True -> only lines with length > 0 will be returned)
    :return: List of line objects"""

    returnList = list()
    for elem in lineList:
        if (elem.startx() >= leftTopCorner[0] and elem.starty() >= leftTopCorner[1]) and (elem.startx() <= rightBotCorner[0] and elem.starty() <= rightBotCorner[1]):
            if not endInclude or ((elem.endx() >= leftTopCorner[0] and elem.endy() >= leftTopCorner[1]) and (elem.endx() <= rightBotCorner[0] and elem.endy() <= rightBotCorner[1])):
                if not cleanPoints or elem.lineLength() > 0:
                    returnList.append(elem)
        elif (elem.endx() >= leftTopCorner[0] and elem.endy() >= leftTopCorner[1]) and (elem.endx() <= rightBotCorner[0] and elem.endy() <= rightBotCorner[1]):
            if not endInclude or ((elem.startx() >= leftTopCorner[0] and elem.starty() >= leftTopCorner[1]) and (elem.startx() <= rightBotCorner[0] and elem.starty() <= rightBotCorner[1])):
                if not cleanPoints or elem.lineLength() > 0:
                    returnList.append(elem)
    return returnList


def findNearestLine(lineList: list, point: list, direction: str) -> line:
    """This function finds the nearest line to a given point in a given direction. If not possible returns nothing!
    
    :param lineList: List of line objects
    :param point: Point [x, y]
    :direction: String direction to scan (left, right, up and down)
    :return: Line object """

    nearestLine = 0
    controlValue = 10000
    if direction == "left":
        for elem in lineList:
            if point[0] - elem.startx() > 0 and (point[0] - elem.startx()) < controlValue:
                controlValue = (point[0] - elem.startx())
                nearestLine = elem
    elif direction == "right":
        for elem in lineList:
            if elem.startx() - point[0] > 0 and (elem.startx() - point[0]) < controlValue:
                controlValue = (elem.startx() - point[0])
                nearestLine = elem
    elif direction == "up":
        for elem in lineList:
            if point[1] - elem.starty() > 0 and (point[1] - elem.starty()) < controlValue:
                controlValue = (point[1] - elem.starty())
                nearestLine = elem
    elif direction == "down":
        for elem in lineList:
            if elem.starty() - point[1] > 0 and (elem.starty() - point[1]) < controlValue:
                controlValue = (elem.starty() - point[1])
                nearestLine = elem          
    if isinstance(nearestLine, line):
        return nearestLine
    else:
        print("No line found")


def findCorrespondingLines(lineList: list, xOrY: bool, precision : int = 8) -> dict:
    """This function findes all lines that are horizontal or vertical and creates a dictionary with corresponding lines
    
    :param lineList: List of line objects
    :param xOrY: Boolean (False -> vertical / True -> horizontal)
    :param precision: the x or y coordinates are rounded, no differentation below this precision
     for example 2 vertical lines with y1 = 11.12, and y2 = 11.13 will be treated as aligned(correspondent) if the precision = 1
     problem : 11.14 and 11.15 are treated as different!
    :return: Dictionary with x or y value as key and a list of all corresponding lines as entry"""

    returnDict = dict()
    if xOrY:
        for elem in lineList:
            if elem.starty() == elem.endy():    #Checks if line is vertical
                try:
                    returnDict[round(elem.starty(), precision)].append(elem)
                except:
                    returnDict[round(elem.starty(), precision)] = [elem]
    else:
        for elem in lineList:
            if elem.startx() == elem.endx():    #Checks if line is horizontal
                try:
                    returnDict[round(elem.startx(), precision)].append(elem)
                except:
                    returnDict[round(elem.startx(), precision)] = [elem]
    return returnDict


def sortDict(unsortedDict: dict):
    """This function sorts the entries of a dictionary. Each entry must be a list of line. Sorting for starting point (first x and then y)
    
    :param unsortedDict: Dictionary with lists of lines as entry
    :return: Dictionary with sorted entries"""

    sortedDict = dict()
    for key in unsortedDict:
        if(len(unsortedDict[key]) > 1):
            sortedDict[key] = sorted(unsortedDict[key], key = lambda line: line.startPoint)
        else:
            sortedDict[key] = unsortedDict[key]
    return sortedDict


def convertLines(sortedLineDict: dict, xOrY, spacing = 12): #Converts dashed lines into one line with style "dashed"
    """This function converts single short lines with small spacing into one line with style "dashed"

    :param sortedLineDict: Dictionary with lists of corresponding lines (sorted) as entries
    :param xOrY: Boolean (False -> vertical / True -> horizontal)
    :param spacing: Greater spacing allows to detect dashed lines with increased distance between the dashes
    :return: Dictionary with new lines"""
    convertedLines = dict()
    counter = 0

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

    
def drawLines(input, page, pdfSaveName = "Output.pdf"):    #Draws lines on PDF-Page the lines have to be provided in (line, list (also dicts in list), dict))
    """This function is only for depiction purposes and prints lines. The lines can be given as a line directly, in a list or in a dict

    :param input: Input with lines in it (line object, list of lines or dicts, dicts)
    :param page: Fitz object with all informations about a given PDF page
    :param pdfSaveName: String of the file path where the PDF is stored"""

    outpdf = fitz.open()
    outpage = outpdf.new_page(width=page.rect.width, height=page.rect.height)
    shape = outpage.new_shape()

    if isinstance(input, line): #Draws a simple line
        point1 = fitz.Point(input.startx(), input.starty())
        point2 = fitz.Point(input.endx(), input.endy())
        shape.draw_line(point1, point2)
        shape.finish()

    elif isinstance(input, list):   #Draws lines from list
        for elem in input: 
            if isinstance(elem, line):
                point1 = fitz.Point(elem.startx(), elem.starty())
                point2 = fitz.Point(elem.endx(), elem.endy())
                shape.draw_line(point1, point2)
                shape.finish()
            if isinstance(elem, dict):
                for key in elem:
                    if isinstance(elem[key], line):
                        point1 = fitz.Point(elem[key].startx(), elem[key].starty())
                        point2 = fitz.Point(elem[key].endx(), elem[key].endy())
                        shape.draw_line(point1, point2)
                        shape.finish()
                    elif isinstance(elem[key], list):
                        for elem2 in elem[key]:
                            point1 = fitz.Point(elem2.startx(), elem2.starty())
                            point2 = fitz.Point(elem2.endx(), elem2.endy())
                            shape.draw_line(point1, point2)
                            shape.finish()

    elif isinstance(input, dict):   #Draws lines from dict
        for key in input:
            if isinstance(input[key], line):
                point1 = fitz.Point(input[key].startx(), input[key].starty())
                point2 = fitz.Point(input[key].endx(), input[key].endy())
                shape.draw_line(point1, point2)
                shape.finish()
            elif isinstance(input[key], list):
                for elem in input[key]:
                    point1 = fitz.Point(elem.startx(), elem.starty())
                    point2 = fitz.Point(elem.endx(), elem.endy())
                    shape.draw_line(point1, point2)
                    shape.finish()

    shape.commit()
    outpdf.save(pdfSaveName)
    
