# -*- coding: utf-8 -*- 
import sys
import os
from tkinter.messagebox import NO
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

import pandas as pd
from .csvManager import CsvManager
from operator import itemgetter
import logging
logger = logging.getLogger("sex")
class algorithm:

    
    

    def __init__(self):
        logger.debug(os.getcwd())
        self.cpu = CsvManager("./resource/cpu.csv")
        self.gpu = CsvManager("./resource/gpu.csv")
        self.case = CsvManager("./resource/case.csv")
        self.ram = CsvManager("./resource/ram.csv")
        self.power = CsvManager("./resource/power.csv")
        self.ssd = CsvManager("./resource/ssd.csv")
        self.mb = CsvManager("./resource/mb.csv")
        self.FPS_DATA = CsvManager("./resource/FPS_DATA.csv")
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


        ssd = self.ssd.consumeRow(consume=False, consumeAll=True)[0]

        ssdData["price"] = int(ssd["price"])
        ssdData["thumbnail"] = ssd["thumbnail"]
        ssdData["part_name"] = ssd["model"]
        ssdData["shop_link"] = ssd["link"]

        return ssdData

    def chooseCase(self):
        caseData = self.generateForm()
        caseData["part_type"] = "case"

        # case = self.case.data.iloc[0:1]
        case = self.case.consumeRow(consume=False, consumeAll=True)[0]


        caseData["price"] = int(case["price"])
        caseData["thumbnail"] = case["thumbnail"]
        caseData["part_name"] = case["model"]
        caseData["shop_link"] = case["link"]

        return caseData

    def chooseRam(self):
        ramData = self.generateForm()
        ramData["part_type"] = "ram"

        ram = self.ram.consumeRow(consume=False, consumeAll=True)[0]

        # ram = self.ram.data.iloc[0:1]

        ramData["price"] = int(ram["price"])
        ramData["thumbnail"] = ram["thumbnail"]
        ramData["part_name"] = ram["model"]
        ramData["shop_link"] = ram["link"]

        return ramData

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
        temp = {}
        d = self.generateForm()
        d["part_type"] = "powersupply"

        pw = self.power.consumeRow(consume=False, consumeAll=True)

        minRow = None
        mintdp = 9999
        for row in pw:
            if int(row["capacity"]) >= tdp:
                if mintdp > int(row["capacity"]):
                    mintdp = int(row["capacity"])
                    minRow = row

        if minRow is None:
            return None

        d["price"] = int(minRow["price"])
        d["thumbnail"] = minRow["thumbnail"]
        d["part_name"] = minRow["model"]
        d["shop_link"] = minRow["link"]

        return d

    def run(self, budget, games, option, resolution, refresh_rate, preference):
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

        ram = self.chooseRam()
        self.currBudget += int(ram["price"])



        # 옵션이랑 비용 정리 위에서 해준다 

        candidateList = []

        for game in games:
            cpugpuList = self.getProperCpuGpuList(game, option, resolution, refresh_rate)

            if len(cpugpuList) <= 0:
                return None

            # for candidate in candidateList:
            for idx, cpugpu in cpugpuList.iterrows():
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

                if currPw is None: #만족하는 파워 용량이 없어서 None 리턴 
                    return None

                tempBudget = currCpu["price"]+currGpu["price"]+currMb["price"]+currPw["price"]

                if (self.currBudget+tempBudget)/10000 > budget :
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
                candidate["game"] = game

                candidateList.append(candidate)

        if len(candidateList) <= 0:
            return None


        games_pc = []
        '''
        # 각 게임별 필터링한 후 각각의 게임에서 최대 FPS를 만드는 PC끼리 비교
        for game in games:
            # 각 게임별 분류
            pc_of_game = list(filter(lambda candidate: candidate["game"] == game, candidateList))
            # 만약 1개의 게임이라도 만족시킬 수 없다면 불가능한 견적이라고 판단
            print(pc_of_game)
            if not pc_of_game:
                return None
            # 각 게임별 최대 FPS를 만드는 PC 
            max_fps_pc = sorted(pc_of_game, key=itemgetter("frame"),reverse=True)[0]
            games_pc.append(max_fps_pc)
        # 각 게임별 필터링 후 FPS를 비교함=> 각 게임별 최대값끼리 비교하여 최소 FPS를 가져옴
        selected = sorted(games_pc, key=itemgetter("frame"),reverse=True)[-1]

        if preference == "가성비":
            selected = sorted(candidateList, key=itemgetter("budget"))[0] # 가격 낮은 순서로 정렬 
        else:
            selected = sorted(candidateList, key=itemgetter("frame"),reverse=True)[0] # 프레임 높은 순서로 정렬
        '''

        selected = None

        if preference == "가성비":  # 가격 우선
            # 각 게임별 필터링한 후 각각의 게임에서 최소 가격을 비교
            for game in games:
                # 각 게임별 분류
                pc_of_game = list(filter(lambda candidate: candidate["game"] == game, candidateList))
                # 만약 1개의 게임이라도 만족시킬 수 없다면 불가능한 견적이라고 판단
                if not pc_of_game:
                    return None
                # 각 게임별 최소 가격의 PC
                min_cost_pc = sorted(pc_of_game, key=itemgetter("budget"),reverse=False)[0]
                games_pc.append(min_cost_pc)
            # 각 게임별 필터링 후 FPS를 비교함=> 각 게임별 최대값끼리 비교하여 최소 FPS(높은 사양의 게임)를 가져옴
            selected = sorted(games_pc, key=itemgetter("frame"),reverse=False)[0]

        else:       # 성능 우선
            # 각 게임별 필터링한 후 각각의 게임에서 최대 FPS를 만드는 PC끼리 비교
            for game in games:
                # 각 게임별 분류
                pc_of_game = list(filter(lambda candidate: candidate["game"] == game, candidateList))
                # 만약 1개의 게임이라도 만족시킬 수 없다면 불가능한 견적이라고 판단
                if not pc_of_game:
                    return None
                # 각 게임별 최대 FPS를 만드는 PC 
                max_fps_pc = sorted(pc_of_game, key=itemgetter("frame"),reverse=False)[-1]
                games_pc.append(max_fps_pc)
            # 각 게임별 필터링 후 FPS를 비교함=> 각 게임별 최대값끼리 비교하여 최소 FPS(높은 사양의 게임)를 가져옴
            selected = sorted(games_pc, key=itemgetter("frame"),reverse=False)[0]

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





    def getProperCpuGpuList(self, game, option, resolution, refresh_rate):
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
        maxFPS = 600
        # 모니터 주사율에 따라 최소 FPS 선택
        # 144hz를 다 쓰지는 못해도 100프레임정도는 나와야 하지 않을까...?
        # refresh_rate는 dialogflow의 pc_monitor_refresh_rate entity 참고
        if refresh_rate == "144hz":
            minFPS = 100

        # 모니터 해상도 선택
        # FHD, QHD (대문자)
        # 상관없다로 선택된 경우 FHD로 고정
        if resolution == "상관없다":
            resolution = "FHD"


        if option != 0:
            temp_data = self.FPS_DATA.data[self.FPS_DATA.data["GAME SETTING"] == self.optionMap[option]]
            # temp_data = self.FPS_DATA.consumeRow(colName="GAME SETTING",key=self.optionMap[option],consume=True,consumeAll=False)

        # temp_data = self.FPS_DATA.consumeRow(colName="GAME NAME",key=targetGame,consume=True,consumeAll=False)
        temp_data = temp_data[temp_data["GAME NAME"] == targetGame]

        temp_data = temp_data[temp_data["GAME AVG FRAME"] >= minFPS]
        temp_data = temp_data[temp_data["GAME AVG FRAME"] <= maxFPS]

        temp_data = temp_data[temp_data["RESOLUTION"] == resolution]

        # returnList = (temp_data["CPU NAME"], temp_data["GPU NAME"])

        returnList = pd.DataFrame(temp_data)[["CPU NAME","GPU NAME","GAME AVG FRAME"]]
        return returnList