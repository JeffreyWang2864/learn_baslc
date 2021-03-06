import os
import numpy as np
from matplotlib import pyplot as plt
import re
import jieba
import json
from xml.etree import ElementTree as et
import json
import csv
import xlwt

class Util:

    def __init__(self):
        self.SeparateDataSet_Pattern = None

    def selectRandomItem(self, current, target):
        if isinstance(current, int):
            new = current
            while new == current:
                new = int(np.random.uniform(0, target))
            return new
        elif isinstance(current, list or tuple):
            new = int(np.random.uniform(0, target))
            while new in current:
                new = int(np.random.uniform(0, target))
            return new

    def clipStepSize(self, max, target, min):
        if target > max:
            return max
        if min > target:
            return min
        return target

    def SIM_EUCLID(self, d1, d2):
        return 1.0 / (1.0 + np.linalg.norm(d1 - d2))

    def SIM_PEARSON(self, d1, d2):
        if len(d1) < 3: return 1.0
        return 0.5 + 0.5 * np.corrcoef(d1, d2, rowvar=0)[0][1]

    def SIM_COSINE(self, d1, d2):
        num = float(d1.transpose() * d2)
        denom = np.linalg.norm(d1) * np.linalg.norm(d2)
        return 0.5 + 0.5 * (num / denom)

    def splitDataSet(self, DataLen, test_proportion = 0.2, mode ="DEFAULT"):
        """
        mode --- decides the way function operates with your input data
            DEFAULT --- just split the data randomly
            LOAD    --- use saved split pattern
            SAVE    --- save the split pattern after separating your input, than return the table
        """
        if mode == "LOAD":
            assert self.SeparateDataSet_Pattern != None
            return self.SeparateDataSet_Pattern
        else:
            assert isinstance(DataLen, int)
            length_test = int(DataLen*test_proportion)
            ExistedElements = list()
            Tabel = [0] * DataLen
            for i in range(length_test):
                index = self.selectRandomItem(ExistedElements, DataLen)
                Tabel[index] += 1
                ExistedElements.append(index)
            if mode == "SAVE":
                self.SeparateDataSet_Pattern = Tabel
            return Tabel

    def getDirectory(self):
        return (os.path.dirname(os.path.abspath(__file__)) + "/")

    def plotCurveROC(self, DataLabel, PredictLabel):
        if isinstance(DataLabel, list):
            DataLabel = np.array(DataLabel)
        if isinstance(PredictLabel, list):
            PredictLabel = np.array(PredictLabel)
        StepIndex = DataLabel.argsort()
        cursor = (1.0, 1.0)
        HorizontalSum = float()
        PositiveNum = sum(PredictLabel == 1)
        y_step = 1 / float(PositiveNum)
        x_step = 1 / float(len(PredictLabel) - PositiveNum)
        graph = plt.figure()
        graph.clf()
        figure = plt.subplot(111)
        for index in StepIndex.tolist():
            if PredictLabel[index] == 1.0 or PredictLabel[index] == 1:
                x_var, y_var = 0, y_step
            else:
                x_var, y_var = x_step, 0
                HorizontalSum += cursor[1]
            figure.plot([cursor[0], cursor[0] - x_var], [cursor[1], cursor[1] - y_var], c='#5C9EFF')
            cursor = (cursor[0] - x_var, cursor[1] - y_var)
        figure.plot([0, 1], [0, 1], c='#A9CCFF', ls="--")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC curve")
        plt.axis([0, 1, 0, 1])
        print("the area covers %.2f%% of area" % ((HorizontalSum * x_step) * 100))
        plt.show()


class DataPreprocessing:

    def __init__(self):
        self.SETTYPE_LIST = list
        self.SETTYPE_NDARRAY = np.array
        self.SETTYPE_NDMAT = np.mat
        self.__SET_FORMAT = (self.SETTYPE_LIST, self.SETTYPE_NDARRAY, self.SETTYPE_NDMAT)
        self.DATATYPE_INT = int
        self.DATATYPE_FLOAT = float
        self.DATATYPE_STRING = str
        self.__DATA_FORMAT = (self.DATATYPE_INT, self.DATATYPE_FLOAT, self.DATATYPE_STRING)
        self.FILE_CSV = 0
        self.FILE_XML = 1
        self.FILE_JSON = 2
        self.FILE_XLSX = 3
        self.FILE_TXT = 4
        self.FILE_HTML = 5
        self.__FILE_FORMAT = (self.FILE_CSV, self.FILE_XML, self.FILE_HTML, self.FILE_JSON, self.FILE_TXT, self.FILE_XLSX)
        self.LANG_CHINESE = re.compile(r'([\u4E00-\u9FA5]+|\w+)')
        self.LANG_ENGLISH = re.compile(r'[a-z|A-Z]+')
        self.__LANGUAGE = (self.LANG_CHINESE, self.LANG_ENGLISH)
        self.DataSet = None
        self.Label = None
        self.graph = None

    def __initGraph(self):
        self.graph = plt.figure()

    def __validPath(self, path):
        assert isinstance(path, str)
        if path[-4::] != ".txt":
            raise TypeError("Read file only support .txt format!")
        if not os.path.exists(Util().getDirectory() + "DATA/" + path):
            print("File does not exist: %s" % path)
            return False
        return True

    def readSimpleDataSet(self, path, set_form, data_form, sep ="\t", add_label = False):
        assert set_form in self.__SET_FORMAT
        assert data_form in self.__DATA_FORMAT
        assert isinstance(add_label, bool)
        assert self.__validPath(path)
        file = open(Util().getDirectory() + "DATA/" + path, "r")
        data = list()
        lines = file.readlines()
        if add_label:
            self.Label = list()
        for line in lines:
            tempData = list()
            splitData = line.strip().split(sep)
            tempData = [data_form(item) for item in splitData]
            #tempData = [data_form(item) for item in splitData[:-1]]       # FIXME: get rid of [:-1]
            if add_label:
                self.Label.append(splitData.pop())          # FIXME: change splitData to tempData
            data.append(tempData.copy())
        print("read file successful")
        self.DataSet = set_form(data)
        if add_label:
            self.Label = set_form(self.Label)

    def readXML(self, path, set_form, data_form, add_label = False):
        assert isinstance(path, str)
        fileAbsolutePath = Util().getDirectory() + "DATA/" + path + ".xml"
        assert os.path.exists(fileAbsolutePath)
        parseTree = et.parse(fileAbsolutePath)
        root = parseTree.getroot()
        rows = root.findall("Row")
        data = list()
        label = list()
        for row in rows:
            new_line = list()
            for element in row.findall("Value"):
                new_line.append(data_form(element.text))
            if add_label:
                label.append(data_form(row.find("Label").text))
            data.append(new_line.copy())
        self.DataSet = set_form(data)
        self.Label = label

    def readParagraph(self, path, add_label = False, sep ="\t"):
        if add_label:
            self.Label = list()
        assert self.__validPath(path)
        file = open(Util().getDirectory() + "DATA/" + path, "r")
        self.DataSet = list()
        lines = file.readlines()
        for line in lines:
            if len(line.strip()) > 1:
                if add_label:
                    tempData = line.strip().split(sep)
                    self.Label.append(int(tempData.pop()))
                self.DataSet.append(tempData[0])

    def writeDataSet(self, name, form, use_label = False):

        def writeTXT():
            file = open(Util().getDirectory() + "DATA/" + name + ".txt", 'w')
            for i in range(len(self.DataSet)):
                for item in self.DataSet[i]:
                    file.write(str(item))
                    file.write("\t")
                if use_label:
                    file.write(self.Label[i])
                file.write("\n")
            file.close()
            return 1

        def writeCSV():
            writer = csv.writer(open(Util().getDirectory() + "DATA/" + name + '.csv', 'wb'))
            if not isinstance(self.DataSet, list):
                if use_label:
                    temp = np.vstack((self.DataSet.T, self.Label.T))
                    temp.resize((self.DataSet.shape[1] + 1, self.DataSet.shape[0]))
                    writer.writerows(temp.transpose())
                else: writer.writerows(self.DataSet)
            else:
                if use_label:
                    temp = self.DataSet
                    for i in range(len(temp)):
                        temp[i] = temp[i].append(self.Label[i])
                    writer.writerows(temp)
                else: writer.writerows(self.DataSet)
            writer.dialect()
            return 1

        def writeJSON():
            writer = open(Util().getDirectory() + "DATA/" + name + ".json", 'wb')
            if isinstance(self.DataSet, (np.ndarray, np.generic)):
                data = self.DataSet.tolist()
            else: data = self.DataSet
            if use_label:
                contents = json.dumps((data, self.Label))
            else: contents = json.dumps(data)
            json.dump(contents, writer)
            return 1

        def writeXML():

            def formattedXML(e, level = 0):
                if len(e) > 0:
                    e.text = "\n" + "\t" * (level + 1)
                    for child in e:
                        formattedXML(child, level+1)
                    child.tail = child.tail[:-1]
                e.tail = "\n" + "\t" * level

            root_node = et.Element("Table")
            for i in range(len(self.DataSet)):
                current = et.Element("Row")
                for j in range(len(self.DataSet[i])):
                    data_node = et.Element("Value")
                    data_node.text = str(self.DataSet[i][j])
                    current.append(data_node)
                if use_label:
                    label_node = et.Element("Label")
                    label_node.text = str(self.Label[i])
                    current.append(label_node)
                root_node.append(current)
            formattedXML(root_node)
            tree = et.ElementTree(root_node)
            tree.write(Util().getDirectory() + "DATA/" + name + ".xml")
            return 1

        def writeXLSX():
            wbook = xlwt.Workbook()
            wsheet = wbook.add_sheet("sheet 1")
            for i in range(len(self.DataSet)):
                for j in range(len(self.DataSet[i])):
                    wsheet.write(i, j, self.DataSet[i][j], xlwt.easyxf('align: vertical center, horizontal center'))
                if use_label:
                    wsheet.write(i, len(self.DataSet[i]), self.Label[i],
                                 xlwt.easyxf('align: vertical center, horizontal center'))
            wbook.save(Util().getDirectory() + "DATA/" + name + ".xls")
            return 1

        def writeHTML():
            file = open(Util().getDirectory() + "DATA/" + name + ".html", "w")
            file.write("<!DOCTYPE HTML>\n")
            file.write("<html>\n")
            file.write("\t<head>\n")
            file.write('\t\t<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n')
            file.write('\t\t<title> crawl result </title>\n')
            file.write("\t</head>\n")
            file.write("\t\t<table>\n")
            for i in range(len(self.DataSet)):
                file.write("\t\t\t<tr>\n")
                for j in range(len(self.DataSet[i])):
                    file.write("\t\t\t\t<td> ")
                    file.write(str(self.DataSet[i][j]))
                    file.write("\t\t\t\t</td>\n")
                if use_label:
                    file.write("\t\t\t\t<td> ")
                    file.write(str(self.Label[i]))
                    file.write("\t\t\t\t</td>\n")
                file.write("\t\t\t</tr>\n")
            file.write("\t\t</table>\n")
            file.write("\t</body>\n")
            file.write("</html>")
            file.close()
            return 1

        def writeFileError():
            raise TypeError("unable to write the file")

        assert form in self.__FILE_FORMAT
        return {
            self.FILE_TXT : writeTXT,
            self.FILE_CSV : writeCSV,
            self.FILE_JSON : writeJSON,
            self.FILE_XML : writeXML,
            self.FILE_XLSX : writeXLSX,
            self.FILE_HTML : writeHTML
        }.get(form, writeFileError)()

    def separateDataSet(self, set_form, portion = 0.2, mode = "DEFAULT"):
        assert set_form in self.__SET_FORMAT
        assert self.DataSet is not None
        assert isinstance(portion, float) or isinstance(portion, float)
        assert 0.0 < portion < 1.0
        assert mode in ("DEFAULT", "SAVE", "LOAD")
        if self.Label is not None:
            trainLabel, testLbel = list(), list()
        trainData, testData = list(), list()
        Lookup_Table = Util().splitDataSet(len(self.DataSet), portion, mode)
        for i in range(len(Lookup_Table)):
            if Lookup_Table[i] == 0:
                trainData.append(self.DataSet[i])
                if self.Label is not None:
                    trainLabel.append(self.Label[i])
            elif Lookup_Table[i] == 1:
                testData.append(self.DataSet[i])
                if self.Label is not None:
                    testLabel.append(self.Label[i])
        self.DataSet = set_form(trainData)
        if self.Label is not None:
            self.Label = set_form(trainLabel)
            return set_form(testData), set_form(testLabel)
        return testData

    def removeRedundantData(self):
        if isinstance(self.DataSet, self.SETTYPE_LIST):
            raise TypeError("'list' object cannot do redundant")
        else:
            non_redundant = list()
            for i in range(self.DataSet.shape[1]):
                curVal = self.DataSet[1, i]
                for item in self.DataSet[:, i]:
                    if item != curVal:
                        non_redundant.append(i)
                        break
        self.DataSet = self.DataSet[:, non_redundant]
        if self.Label is not None:
            assert not isinstance(self.Label, list)
            self.Label = self.Label[non_redundant]

    def balanceDataSet(self, ratio = (0.5, 0.5)):
        assert self.DataSet is not None
        assert self.Label is not None
        assert not isinstance(self.Label, list)
        assert isinstance(ratio, tuple)
        assert len(ratio) == 2
        assert sum(ratio) == 1.0
        assert len(set(self.Label)) == 2
        sign1, sign2 = int(), int()
        firstSign = self.Label[0]
        for item in self.Label:
            if item == firstSign:
                sign1 += 1
            else: sign2 += 1
        modification = (ratio[0]*len(self.Label) - sign1, ratio[1]*len(self.Label) - sign2)
        range0 = np.nonzero(self.Label == firstSign)[0]
        range1 = np.nonzero(self.Label != firstSign)[0]
        if modification[0] > 0:
            additional0 = np.array(
                [np.random.randint(np.min(range0), np.max(range0)) for _ in range(int(modification[0]))])
            range0 = np.hstack((range0, additional0))
        elif modification[0] < 0:
            range0 = range0[np.array([np.random.randint(0, range0.size)
                                      for _ in range(int(range0.size + modification[0]))])]
        if modification[1] > 0:
            additional1 = np.array(
                [np.random.randint(np.min(range1), np.max(range1)) for _ in range(int(modification[0]))])
            range1 = np.hstack((range1, additional1))
        elif modification[1] < 0:
            range1 = range1[np.array([np.random.randint(0, range1.size)
                                      for _ in range(int(range1.size + modification[1]))])]
        totalRange = np.hstack((range0, range1))
        if isinstance(self.DataSet, list):
            r = totalRange.tolist()
            new = list()
            for item in r:
                new.append(self.DataSet[item])
            self.DataSet = new
        else: self.DataSet = self.DataSet[totalRange]
        self.Label = self.Label[totalRange]

    def changeType(self, data, future_type):
        enum_of_data = set(data)
        conversionDict = dict()
        initial_correspond_value = future_type()
        for item in enum_of_data:
            conversionDict[item] = initial_correspond_value
            initial_correspond_value += future_type(1)
        for i in range(len(data)):
            data[i] = conversionDict[data[i]]

    def convertLevelToBinary(self):
        assert self.DataSet is not None
        assert self.Label is not None
        assert len(set(self.Label)) > 2
        if isinstance(self.Label, list):
            self.Label = np.array(self.Label)
        labelRange = sorted(list(set(self.Label)))
        boundary = (labelRange[0] + labelRange[-1])/2
        range0 = np.nonzero(self.Label < boundary)[0]
        range1 = np.nonzero(self.Label > boundary)[0]
        self.Label[range0] = 0
        self.Label[range1] = 1
        totalRange = np.hstack((range0, range1))
        self.Label = self.Label[totalRange]
        if isinstance(self.DataSet, list):
            r = totalRange.tolist()
            new = list()
            for item in r:
                new.append(self.DataSet[item])
            self.DataSet = new
        else: self.DataSet = self.DataSet[totalRange]

    def __curWords(self, sentence, language, Filter):
        if language is self.LANG_ENGLISH:
            words = [item.lower() for item in re.findall(language, sentence)]
        elif language is self.LANG_CHINESE:
            return [word for word in jieba.cut(" ".join(re.findall(language, sentence)))
                       if word != " "]
        words = [item for item in words if Filter(item)]
        return words

    def __generateDictionary(self, sentences):
        ret = set()
        for sentence in sentences:
            ret = ret | set(sentence)
        return list(ret)

    def __getWordExistence(self, line, dictionary):
        ret = [0] * len(dictionary)
        for word in line:
            if word in dictionary:
                ret[dictionary.index(word)] += 1
            else:
                print("The word %s does not contain in the dictionary" % (word))
        return ret

    def wordBagging(self, language, set_form, Filter = lambda x: True):
        assert set_form in self.__SET_FORMAT
        assert language in self.__LANGUAGE
        lineList = list()
        for line in self.DataSet:
            lineList.append(self.__curWords(line ,language, Filter))
        dictionary = self.__generateDictionary(lineList)
        dictMat = list()
        for line in lineList:
            dictMat.append(self.__getWordExistence(line, dictionary))
        return dictionary, set_form(dictMat)

    def head(self, value = 10):
        return self.DataSet[::value]

    def tail(self, value = 10):
        return self.DataSet[-value::]

    def pca(self, dimension):
        assert isinstance(dimension, int) and 0 < dimension <= self.DataSet.shape[1]
        meanValue = np.mean(self.DataSet, axis=0)
        data = self.DataSet - meanValue
        covariance = np.cov(data, rowvar=0)
        eigVals, eigVectors = np.linalg.eig(covariance)
        eigValsIndex = np.argsort(eigVals)[:-(dimension+1):-1]
        finalEigVectors = eigVectors[:, eigValsIndex]
        lowData = data * finalEigVectors
        reconData = (lowData * finalEigVectors.transpose()) + meanValue
        self.DataSet = reconData
        return lowData

    def graph2D(self, graphingIndexes = None, color ="#516EFF"):
        if graphingIndexes is None:
            x = np.array(self.DataSet[:, 0]).flatten()
            y = np.array(self.DataSet[:, 1]).flatten()
        elif isinstance(graphingIndexes, list) or isinstance(graphingIndexes, tuple):
            assert len(graphingIndexes) == 2
            for item in graphingIndexes:
                assert 0 <= item < self.DataSet.shape[1]
            x = np.array(self.DataSet[:, graphingIndexes[0]]).flatten()
            y = np.array(self.DataSet[:, graphingIndexes[1]]).flatten()
        if self.graph is None:
            self.__initGraph()
        graph = self.graph.add_subplot(111)
        graph.scatter(x, y, marker='o', c=color, s=20, alpha=0.2)

    def showGraph(self):
        plt.show()