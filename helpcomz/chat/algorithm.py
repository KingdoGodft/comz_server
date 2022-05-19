# -*- coding: utf-8 -*- 
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pandas as pd
from .csvManager import CsvManager
from operator import itemgetter


class algorithm:

    
    

    def __init__(self):
        print(os.getcwd())
        self.cpu = CsvManager("../resource/cpu.csv")
        self.gpu = CsvManager("../resource/gpu.csv")
        self.case = CsvManager("../resource/case.csv")
        self.ram = CsvManager("../resource/ram.csv")
        self.power = CsvManager("../resource/power.csv")
        self.ssd = CsvManager("../resource/ssd.csv")
        self.mb = CsvManager("../resource/mb.csv")
        self.FPS_DATA = CsvManager("../resource/FPS_DATA.csv")
        self.gameMap = {

        }

        self.gameMap["사이버펑크2077"]=1
        self.gameMap["플레이어언노운스 배틀그라운드"]=2
        self.gameMap["리그오브레전드"]=3
    
        self.optionMap = {

        }

        self.optionMap[0]="any"
        self.optionMap[1]="MEDIUM"
        self.optionMap[2]="HIGH"
        self.optionMap[3]="ULTRA"

        self.initialize()

    def initialize(self):
        self.currBudget = 0
        self.returnData = []
        # self.generateForm().part_type = 3

    def generateForm(self):
        d = {}
        d["part_type"] = ""
        d["part_name"] = ""
        d["price"] = ""
        d["shop_link"] = ""
        d["thumbnail"] = ""
        
        return d
        #  return {
        #     "part_type" : "",
        #     "part_name" : "",
        #     "price" : "",
        #     "shop_link" : "",
        #     "thumbnail" : "",
        #     }


    def chooseSSD(self):
        ssdData = self.generateForm()
        ssdData["part_type"] = "disk"


        ssd = self.ssd.data.iloc[0:1]

        ssdData["price"] = int(ssd["price"])
        ssdData["thumbnail"] = ssd["thumbnail"]
        ssdData["part_name"] = ssd["model"]
        ssdData["shop_link"] = ssd["link"]

        return ssdData

    def chooseCase(self):
        caseData = self.generateForm()
        caseData["part_type"] = "case"

        case = self.case.data.iloc[0:1]

        caseData["price"] = int(case["price"])
        caseData["thumbnail"] = case["thumbnail"]
        caseData["part_name"] = case["model"]
        caseData["shop_link"] = case["link"]

        return case

    def chooseRam(self):
        ramData = self.generateForm()
        ramData["part_type"] = "ram"

        ram = self.ram.data[0]

        ramData["price"] = int(ram["price"])
        ramData["thumbnail"] = ram["thumbnail"]
        ramData["part_name"] = ram["model"]
        ramData["shop_link"] = ram["link"]

        return ram

    def getMBBySocket(self,socket):
        d = self.generateForm()
        d["part_type"] = "mainboard"


        mb = self.mb.consumeRow(colName="socket",key=str(socket)+"",consume=False)[0]

        d["price"] = int(mb["price"])
        d["thumbnail"] = mb["thumbnail"]
        d["part_name"] = mb["model"]
        d["shop_link"] = mb["link"]

        return d

    def getPowerByTDP(self,tdp):
        d = self.generateForm()
        d["part_type"] = "case"

        pw = self.power.data[self.power.data["capacity"] >= tdp]
        pw = pd.DataFrame(pw).sort_values(by="capacity",ascending=True).iloc[0:1] #파워 용량 가장 작은 것 선택!

        d["price"] = int(pw["price"])
        d["thumbnail"] = pw["thumbnail"]
        d["part_name"] = pw["model"]
        d["shop_link"] = pw["link"]

        return d

    def run(self, budget, games, option):
        #None 리턴하면 계산하다가 에러 난 것!

        # budget = budget[0]

        try:
            budget = int(budget.split("만원")[0])
        except:
            return None



        case = self.chooseCase()
        self.currBudget += int(case["price"])

        ssd = self.chooseSSD()
        self.currBudget += int(ssd["price"])

        ram = self.chooseSSD()
        self.currBudget += int(ram["price"])



        # 옵션이랑 비용 정리 위에서 해준다 

        candidateList = []

        for game in games:
            cpugpuList = self.getProperCpuGpuList(game, option)

            if len(cpugpuList) <= 0:
                return None

            # for candidate in candidateList:
            #     #이미 이전 게임에서 선택된 후보를 다시 체크해야됌!
            #todo 게임 여러개일때 ... 어떡해야될지 모르겠네 ㅅㅂ 


            for idx, cpugpu in cpugpuList.iterrows():
                print("cpugpu ",cpugpu)
                cpu=cpugpu["CPU NAME"]
                gpu=cpugpu["GPU NAME"]
                frame=cpugpu["GAME AVG FRAME"]

                # model,price,link,thumbnail,score,core,thread,clock,turbo_clock,tdp,socket 가져온다 
                try:
                    currCpu = self.cpu.consumeRow(colName="model",key=cpu,consume=False)[0] #무조건 하나임 중복 cpu 가 없어서 
                    currGpu = self.gpu.consumeRow(colName="model",key=gpu,consume=False)[0] #무조건 하나임 중복 gpu 가 없어서 
                except:
                    continue

                currMb = self.getMBBySocket(currCpu["socket"])

                needCapacity = int(currCpu["tdp"])+int(currGpu["tgp"])+150 #필요한 파워 용량 

                currPw = self.getPowerByTDP(needCapacity)

                tempBudget = currCpu["price"]+currGpu["price"]+currMb["price"]+currPw["price"]

                print("budget test ",self.currBudget,tempBudget, budget)
                if (self.currBudget+tempBudget)/10000 > budget :
                    print("BUDGET EXCEED")
                    continue

                #continue 안 할 경우 넣어도 되는 부품 조합임 .

                candidate={}
                # candidate.c = cpu
                # candidate.g = gpu
                candidate["cpu"] = currCpu
                candidate["gpu"] = currGpu
                candidate["mb"] = currMb
                candidate["pw"] = currPw
                candidate["frame"] = frame
                candidate["budget"] = tempBudget

                candidateList.append(candidate)

        if len(candidateList) <= 0:
            return None

        # selected = sorted(candidateList, key=itemgetter("budget"))[0] # 가격 낮은거부터 정렬 
        selected = sorted(candidateList, key=itemgetter("frame"),reverse=True)[0] # 프레임 높은거부터 정렬 

        temp_cpu = self.generateForm()
        temp_cpu["part_type"] = "cpu"
        temp_cpu["price"] = selected["cpu"]["price"]
        temp_cpu["thumbnail"] = selected["cpu"]["thumbnail"]
        temp_cpu["part_name"] = selected["cpu"]["model"]
        temp_cpu["shop_link"] = selected["cpu"]["link"]

        temp_gpu = self.generateForm()
        temp_gpu["part_type"] = "gpu"
        temp_gpu["price"] = selected["gpu"]["price"]
        temp_gpu["thumbnail"] = selected["gpu"]["thumbnail"]
        temp_gpu["part_name"] = selected["gpu"]["model"]
        temp_gpu["shop_link"] = selected["gpu"]["link"]

        temp_mb = self.generateForm()
        temp_mb = selected["mb"]

        temp_pw = self.generateForm()
        temp_pw = selected["pw"]
    
        self.returnData.append(temp_cpu)
        self.returnData.append(temp_gpu)
        self.returnData.append(temp_mb)
        self.returnData.append(ram)
        self.returnData.append(temp_pw)
        self.returnData.append(ssd)
        self.returnData.append(case)

        self.currBudget += selected["budget"]

        return {
                   "data" : self.returnData,
                   "option" : option,
                   "frame" : selected["frame"],
                   "totalPrice" : self.currBudget
                }





    def getProperCpuGpuList(self, game, option):
        if option=="상관없음":
            option = 0
        if option=="하옵":
            option = 1
        if option=="중옵":
            option = 2
        if option=="상옵":
            option = 3

        #game = 1 =>사이버펑크
        #       2 => 배그
        #       3 => 롤
        targetGame= self.gameMap[game]

        minFPS = 55
        maxFPS = 150


        if option != 0:
            temp_data = self.FPS_DATA.data[self.FPS_DATA.data["GAME SETTING"] == self.optionMap[option]]
            # temp_data = self.FPS_DATA.consumeRow(colName="GAME SETTING",key=self.optionMap[option],consume=True,consumeAll=False)

        # temp_data = self.FPS_DATA.consumeRow(colName="GAME NAME",key=targetGame,consume=True,consumeAll=False)
        temp_data = temp_data[temp_data["GAME NAME"] == targetGame]

        temp_data = temp_data[temp_data["GAME AVG FRAME"] >= minFPS]
        temp_data = temp_data[temp_data["GAME AVG FRAME"] <= maxFPS]

        # returnList = (temp_data["CPU NAME"], temp_data["GPU NAME"])

        returnList = pd.DataFrame(temp_data)[["CPU NAME","GPU NAME","GAME AVG FRAME"]]
        return returnList