#globle list aminoacids
aminoacids = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y'] 
#define a function to decide an aminosequence
def whether_aa(x): 
    y = x.upper()
    count = 1
    length = len(y)
    for i in y:
        if i in aminoacids:
            if count==length:
                print "This is an aminoacid sequence"
                return True
            count+=1
            continue
        else:
            print "this is not an aminoacid sequence"
            return False
 
def hw1(protein_sequence):
    #Author: Chengbin Hu
    #05/22/2014
    #assign protein sequence to varible
    if whether_aa(protein_sequence):#if it is aminoacid sequence
        protein_length = len(protein_sequence) # obtain the length of the protein
        position_precentage_20 = protein_length*2/10 #get an "int" result for position at %20
        position_precentage_80 = protein_length*8/10 #get an "int" result for position at %80
        print "The protein sequence length is ", protein_length
        print "The 20% position is", position_precentage_20
        print "The 80% position is", position_precentage_80
        print "The N-terminus sequence is from amino acid 1 to", position_precentage_20
        print protein_sequence[:position_precentage_20]#print the N-terminal sequence
        print "The middle region is from " + str(position_precentage_20) + " to " + str(position_precentage_80)
        print protein_sequence[position_precentage_20:position_precentage_80]#print the middle region sequence
        print "The C-terminus is from "+ str(position_precentage_80) + " to the end"
        print protein_sequence[position_precentage_80:] #print the C-terminal sequence
    else:
        print "This function is designed only for aminoacid sequence"
        
def hw2(protein_sequence):
    if whether_aa(protein_sequence):
        DictA = dict(zip(aminoacids,[0]*20))
        length = len(protein_sequence)
        for item2 in DictA:
            for item in protein_sequence:
                if item == item2:
                    DictA[item2]+=1
            DictA[item2] = DictA[item2]*100.0/length#calcuate the precentage of  amninoacids
        print DictA
    else:
        print "This function is designed only for aminoacid sequence"
        
def hw3a(pdrfit):
    #Author Chengbin Hu
    pond = open(pdrfit, "r")
    ls = pond.readlines()#read all the lines
    pond.close()
    ls_score = [None]*(len(ls)-1) #creat a list to contain scores
    for i in range(len(ls)):
        if i ==0: # we don't need first line of ponderfit data
            continue
        else:
            a = ls[i].split()
            ls_score[i-1]=a[2] #store score to new list
    score = open("pondrscore.txt","w")
    for i in ls_score:
        score.write(i+"\n")#write score to file
        print i
    score.close()
def hw3b(pdbfile,n):
    # second part pdb file
    # Chengbin Hu
    pdb = open(pdbfile,"r")
    ls2 = pdb.readlines()# reall pdb
    pdb.close()
    
    if n==1:
        new_pdb= open("ligpdb.pdb", "w")
        for item in ls2:
            if item.split()[0]=='HETATM': #whether start with ATOM?
                print item #check item
                new_pdb.write(item) #write to file
    else:
        new_pdb= open("recpdb.pdb", "w")
        for item in ls2:
            if item.split()[0]=='ATOM': #whether start with ATOM?
                print item #check item
                new_pdb.write(item) #write to file
    new_pdb.close()
    