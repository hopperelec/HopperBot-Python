# Commonly used function for combining lists of lists
def getIn(inside):
    return [inner for outer in inside for inner in outer]

# Import required modules
from functools import lru_cache,wraps
from collections import Counter
from nltk import ngrams
from os import listdir
from json import dump as jsonwrite, load as jsonread

def saveAuthorCounts(authorCounts):
    with open('authorCounts.json','w+') as jsonfile:
        jsonwrite({k:dict(sorted(v.items(),key=lambda item:item[1],reverse=True)) for k,v in authorCounts.items()},jsonfile,indent=4)

@lru_cache(10)
def getCounts(ns=4,lengthWeight=1,lengthType=1,save=False):
    words = {k:getIn([formatM(message,ns) for message in v]) for k,v in data.items()}
    authorCounts = {k:Counter(word for word in words[k]) for k in data.keys()}
    authorCounts = {author:{value:counts*(len(value.split() if lengthType == 0 else value)**lengthWeight) for value,counts in values.items() if counts >= 3} for author,values in authorCounts.items()}
    if save:
        saveAuthorCounts(authorCounts)
    return authorCounts

def probabilityCounts(authorCounts,probabilityWeight=1,save=True):
    authorCounts = {author:{value:counts/(len(values)**probabilityWeight) for value,counts in values.items()} for author,values in authorCounts.items()}
    if save:
        saveAuthorCounts(authorCounts)
    return authorCounts

@lru_cache(99)
def formatM(m,testNs):
    return getIn([result for result in [[' '.join(ngram) for ngram in ngrams(m.split(' '),n)] for n in range(1,testNs+1)] if result != []])

# Get messages from file
data = {}
for filename in listdir("messages"):
    if filename.endswith('.txt') and filename != "all.txt":
        with open("messages/"+filename,'r',errors='ignore') as txtfile:
            data[filename[:-4]] = [line.strip() for line in txtfile.readlines()]

# Get a dict of dicts showing the number of times each word is used by each author
ns,probabilityWeight,lengthWeight = 6,1,3
authorCounts = getCounts(ns,lengthWeight)
authorCounts = probabilityCounts(authorCounts,probabilityWeight)

# Output
for key in authorCounts.keys():
    print(key+':',', '.join(list({k:dict(sorted(v.items(),key=lambda item:item[1],reverse=True)) for k,v in authorCounts.items() if k == key}[key].keys())[:100])+"\n")

# Use accuracy to try and find the best combination of weights
input("Press any key to run accuracy test...")
print('This may take a while so please be patient!')
weights = [-1,-0.66,-0.33,0,0.33,0.66,1,1.33,1.66,2,2.33,2.66,3]
messagesToTest = len(sorted(data.values(),key=len)[0])
bestResult = [0,[[]]]
results = {testN:{ngramWeight:{probabilityWeight:[] for probabilityWeight in weights} for ngramWeight in weights} for testN in range(1,9)}
for testN in range(1,9):
    print(testN,'ngrams:')
    for lengthWeight in weights:
        print(f'    {lengthWeight} length weight:')
        originalCounts = getCounts(testN,lengthWeight,False)
        for probabilityWeight in weights:
            print(' '*8+str(probabilityWeight),'probability weight:')
            authorCounts = probabilityCounts(originalCounts,probabilityWeight,False)
            correctFirst,correctSecond,correctThird,tests = 0,0,0,0
            for k,v in data.items():
                for m in v[:messagesToTest]:
                    tests += 1
                    m = formatM(m,testN)
                    result = sorted([(key,sum([(0 if not word in value.keys() else value[word]) for word in m])) for key,value in authorCounts.items()],key=lambda item:item[1],reverse=True)
                    if result[0][0] == k:
                        correctFirst += 1
                    elif result[1][0] == k:
                        correctSecond += 1
                    # elif result[2][0] == k:
                    #     correctThird += 1
            result = (correctFirst+correctSecond/2)/tests
            results[testN][lengthWeight][probabilityWeight] = [correctFirst,correctSecond]
            if result > bestResult[0]:
                print(' '*12+'!!!!! NEW BEST !!!!!')
                bestResult = [result,[[testN,lengthWeight,probabilityWeight]]]
            elif result == bestResult[0]:
                print(' '*12+'!!! ANOTHER BEST !!!')
                bestResult[1] += [[testN,lengthWeight,probabilityWeight]]
            # print(f"{' '*12}Accuracy (first try)): {int(correctFirst/tests*1000)/10}%")
            # print(f"{' '*12}Accuracy (atleast second try)): {int((correctFirst+correctSecond)/tests*1000)/10}%")
            # print(f"{' '*12}Accuracy (atleast third try)): {int((correctFirst+correctSecond+correctThird)/tests*1000)/10}%")
print('Best results:')
print('    Score:',bestResult[0])
for i,result in enumerate(bestResult[1]):
    print(f'    Result {i+1}:')
    print(' '*8+'ns:',result[0])
    print(' '*8+'length weight:',result[1])
    print(' '*8+'probability weight:',result[2])
with open('accuracyResults.json','w+') as jsonfile:
    jsonwrite(results,jsonfile)
