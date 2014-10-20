from urllib2 import urlopen, URLError

def fetchID(scorename):
    namefile = open(scorename,"r")
    ls = namefile.readlines()
    namefile.close()
    ls_name = []
    for ite in ls:
        ls_name.append(ite.split()[0])
    return ls_name

def fetch_compage(ID):
    url = "http://zinc.docking.org/substance/"+ID[1:]
    try:
        comp = urlopen(url)
        return comp
    except URLError as e:
        print "Error: ", e, " ", ID
        return False    


def IDtoname(namels,exportname):
    namefile = open(exportname,"w")
    idnum = 1
    for item in namels:
        x = fetch_compage(item)
        if x:
            compage=x.readlines()
            for i in range(len(compage)):
                if "//zinc.docking.org/synonym/" in compage[i]:
                    namefile.write(str(idnum)+"  "+item+"    "+compage[i+1].split(">")[1][:-6]+"\n")
        idnum+=1
    namefile.close()


def main():
    compoundnamels=fetchID("combinevp35.txt")
    IDtoname(compoundnamels,"vp35top1000structure.txt")
    


if __name__ == '__main__':
    main()