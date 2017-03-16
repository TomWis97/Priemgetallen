from math import sqrt
import requests
import time

# Settings
masterAddress = 'http://master:5000'

def calcPrime(minRange, maxRange):
    nummers = []
    for getal in range(minRange, maxRange):
        isPriem = True
        for i in range(2, int(sqrt(getal))+1):
            if getal % i == 0:
                isPriem = False
                break
        if isPriem:
            nummers.append(getal)
    return nummers


while True:
    # Get work
    r = requests.get(masterAddress + '/api/getjob')
    maxRange = r.json()['startnum'] + r.json()['steps']
    job = {
        'id':       int(r.json()['id']),
        'startnum': int(r.json()['startnum']),
        'endnum':   int(r.json()['startnum'] + r.json()['steps'])
    }
    print("Fetched job #{}. Start: {}, end: {}".format(job['id'],
          job['startnum'], job['endnum']))
    data = calcPrime(job['startnum'], job['endnum'])
    #print(data)
    returnDict = {'id': job['id'], 'data': data}
    startTime = time.time()
    r = requests.post(masterAddress + '/api/results', json=returnDict)
    print('Finished job #{id}. Master status: {status}. Amount: {len}'.format(
        id=job['id'],
        status=r.json()['status'],
        len=r.json()['amount']
    ))
    #print("Processing POST took {} seconds.".format(time.time()-startTime))
