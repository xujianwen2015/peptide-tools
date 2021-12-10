import sys, os, re, string, csv
import argparse
import json
import os.path
import math
from rdkit import Chem
from rdkit.Chem import AllChem, Recap, Descriptors, Draw
from numpy import *
from matplotlib.pyplot import *

import subprocess

from pka_sets_fasta import *
from smarts_matcher_aminoacids import *

from itertools import cycle
import bisect 


# Turns a dictionary into a class 
class Dict2Class(object): 
    def __init__(self, my_dict): 
        for key in my_dict: 
            setattr(self, key, my_dict[key]) 



def clean_up_output(text):
    txt=text.split('\n')
    text_new=''
    for line in txt: 
        if "mkdir: cannot create directory '/.local': Permission denied" in line: continue
        text_new += line+'\n'
    return text_new

def get_status_output(*args, **kwargs):
    #from subprocess import Popen
    p = subprocess.Popen(*args, **kwargs)
    stdout, stderr = p.communicate()
    return p.returncode, stdout, stderr

def run_exe(exe):
    #if sys.version_info[0] < 3:
    #    from commands import getstatusoutput
    #    status, output = getstatusoutput(exe)
    #else:
    status, stdout, stderr = get_status_output(exe.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output =  stdout.decode("utf-8")
    if status != 0: raise Exception("ERROR: happend while executing "+exe+" : " + output)
    output = clean_up_output(output)
    return output

def calc_pkas_dimorphite_dl(unknown_fragments):
    from rdkit import Chem
    from dimorphite_dl import Protonate

    skip_site_names = ['TATA','*Amide']

    base_pkas=[]
    acid_pkas=[]
    diacid_pkas=[]

    for smiles in unknown_fragments:
        protonation_sites = Protonate({'smiles':smiles}).get_protonation_sites()

        for sites in protonation_sites:
            #(3, 'BOTH', '*Amide') 
            site_name = sites[2]

            if site_name in skip_site_names: continue

            if site_name in D_dimorphite_dl_type_pka.keys():
                site_data = D_dimorphite_dl_type_pka[site_name]
                if site_data['type']=='base':
                        base_pkas.append((site_data['pka'],smiles))
                if site_data['type']=='acid':
                        acid_pkas.append((site_data['pka'],smiles))
                if site_data['type']=='diacid':
                        diacid_pkas.append(((site_data['pka1'],site_data['pka2']),smiles))
                
            else:
                print('Error:  not known dimorphite site type ' + site_type)
                sys.exit(1)
    return (base_pkas,acid_pkas,diacid_pkas)
    

def calc_pkas_acdlabs(smi_list):
    # use ACDlabs.
    # perceptabat executable should be in the path.

    pka_lim_1=0
    pka_lim_2=15

    pka_lim_ac_1=0
    pka_lim_ac_2=12

    tmpfile='TMP_SMI_FOR_PKA.smi'
    #tmpfile4='TMP_SMI_FOR_PKA.json'
    if os.path.isfile(tmpfile): os.remove(tmpfile)
    with open(tmpfile,'w') as smifile:
        i=0
        for smi in smi_list:
            i+=1
            smifile.write(smi+" tmpname"+str(i)+'\n')

    tmpfile2='TMP_CLAB_OUTPUT.txt'
    if os.path.isfile(tmpfile2): os.remove(tmpfile2)
    exe = 'perceptabat -TFNAME'+tmpfile2+' -MPKAAPP -TPKA ' + tmpfile
    tmpoutput = run_exe(exe)
    if not os.path.isfile(tmpfile2): 
        print("ERROR: no tmpfile generated by acdlabs "+tmpfile2)
        sys.exit(1)


    with open(tmpfile2,'r') as f:
        base_pkas=[]
        acid_pkas=[]
        diacid_pkas=[]
        D={}
        f.readline() # skip first line
        for line in f.readlines():
            ln=line.split()
            mol_idx = int(ln[0])
            if mol_idx not in D.keys(): D[mol_idx]={}
            #if 'ACD_pKa_Apparent' in ln[1]: D[mol_idx]['pka']=float(ln[2])
            if 'ACD_pKa_Apparent' in ln[1]: pka = float(ln[2])
            if 'ACD_pKa_DissType_Apparent' in ln[1]: 
                if ln[2] in ['MB','B']:
                    if pka > pka_lim_1 and pka < pka_lim_2: 
                        base_pkas.append((pka,smi_list[mol_idx-1]))
                if ln[2] in ['MA','A']:
                    if pka > pka_lim_ac_1 and pka < pka_lim_ac_2: 
                        acid_pkas.append((pka,smi_list[mol_idx-1]))
            
#PKA: Calculate apparent values using classic algorithm
#1	 ID: 1
#1	 ACD_pKa_IonicForm_Apparent: L
#1	 ACD_pKa_Apparent_1: 10.689
#1	 ACD_pKa_Error_Apparent_1: 0.10
#1	 ACD_pKa_DissAtom_Apparent_1: 5
#1	 ACD_pKa_DissType_Apparent_1: MB
#1	 ACD_pKa_Equation_Apparent_1: HL/H+L
#1	 ACD_pKa_All_Apparent_1: pKa(HL/H+L; 5) = 10.69+/-0.10
#2	 ID: 2
#2	 ACD_pKa_IonicForm_Apparent: L
#...
#4	 ID: 4
#4	 ACD_pKa_Caution_Apparent: The structure does not contain ionization centers calculated by current version of ACD/pKa
#5	 ID: 5
#5	 ACD_pKa_IonicForm_Apparent: L
#5	 ACD_pKa_Apparent_1: 10.679
#5	 ACD_pKa_Error_Apparent_1: 0.10
#5	 ACD_pKa_DissAtom_Apparent_1: 1
#5	 ACD_pKa_DissType_Apparent_1: MB
#5	 ACD_pKa_Equation_Apparent_1: HL/H+L
#5	 ACD_pKa_All_Apparent_1: pKa(HL/H+L; 1) = 10.68+/-0.10
#5	 ACD_pKa_Apparent_2: 9.334
#5	 ACD_pKa_Error_Apparent_2: 0.10
#5	 ACD_pKa_DissAtom_Apparent_2: 6
#5	 ACD_pKa_DissType_Apparent_2: B 
#5	 ACD_pKa_Equation_Apparent_2: H2L/H+HL
#5	 ACD_pKa_All_Apparent_2: pKa(H2L/H+HL; 6) = 9.33+/-0.10

    lClean=False
    if lClean:     
            if os.path.isfile(tmpfile): os.remove(tmpfile)
            if os.path.isfile(tmpfile2): os.remove(tmpfile2)

    return (base_pkas,acid_pkas,diacid_pkas)
       





def calc_pkas(smi_list, use_acdlabs=False, use_dimorphite=True):

    if use_acdlabs and use_dimorphite: raise Exception('Error: requested to use both ACDlabs and Dimorphite for pka calculation. Should be only one. ')
    if not use_acdlabs and not use_dimorphite: raise Exception('Error: requested to use none of ACDlabs or Dimorphite for pka calculation. Should be at least one. ')

    if use_acdlabs:
        base_pkas,acid_pkas,diacid_pkas = calc_pkas_acdlabs(smi_list)

    if use_dimorphite:
        base_pkas,acid_pkas,diacid_pkas = calc_pkas_dimorphite_dl(smi_list)

    #if use_opera:
    #    base_pkas,acid_pkas,diacid_pkas = calc_pkas_opera(smi_list)
    
    return (base_pkas,acid_pkas,diacid_pkas)


        
def calculateBasicCharge(pH, pKa):
        return 1 / (1 + 10**(pH - pKa))

def calculateAcidicCharge(pH, pKa):
        return -1 / (1 + 10**(pKa - pH))

def calculateDiacidCharge(pH, pKa1, pKa2):
        Ka1=10**(-pKa1)
        Ka2=10**(-pKa2)
        H=10**(-pH)
        f1 = (H*Ka1)/(H**2+H*Ka1+Ka1*Ka2)  # fraction of [AH-]
        f2 = f1 * Ka2 / H                  # fraction of [A2-]
        return -2*f2 + (-1)*f1     # average charge of phosphate group


def calculateMolCharge(base_pkas, acid_pkas, diacid_pkas, pH):
    charge = 0
    for pka in base_pkas:
        charge += calculateBasicCharge(pH, pka)

    for pka in acid_pkas:
        charge += calculateAcidicCharge(pH, pka)

    for pkas in diacid_pkas:
        charge += calculateDiacidCharge(pH, pkas)

    #print(pH,charge)
    return charge

pH_llim=-1
pH_hlim=15


def calculateIsoelectricPoint(base_pkas, acid_pkas, diacid_pkas):   
    tolerance=0.01
    charge_tol=0.05
    na=len(acid_pkas)+len(diacid_pkas)
    nb=len(base_pkas)
    min_pH, max_pH = pH_llim , pH_hlim

    while True:
        mid_pH = 0.5 * (max_pH + min_pH)
        charge = calculateMolCharge(base_pkas, acid_pkas, diacid_pkas, mid_pH)
        
        if na == 0 and nb != 0:
            #print "---!Warning: no acidic ionizable groups, only basic groups present in the sequence. pI is not defined and thus won't be calculated. However, you can still plot the titration curve. Continue."
            refcharge = charge_tol * nb

        elif nb == 0 and na != 0:
            #print "---!Warning: no basic ionizable groups, only acidic groups present in the sequence. pI is not defined and thus won't be calculated. However, you can still plot the titration curve. Continue."
            refcharge = -charge_tol * na

        else:
            refcharge = 0.0


        if charge > refcharge + tolerance:
            min_pH = mid_pH
        elif charge < refcharge - tolerance:
            max_pH = mid_pH
        else:
            return mid_pH
            
        if mid_pH <= pH_llim:
            return pH_llim
        elif mid_pH >= pH_hlim:
            return pH_hlim
            

def CalcChargepHCurve(base_pkas, acid_pkas, diacid_pkas):
    #pH_a=arange(0,14,0.1)
    pH_a=arange(pH_llim,pH_hlim,0.1)
    Q_a=pH_a*0.0    
    for i in range(len(pH_a)):
        Q = calculateMolCharge(base_pkas, acid_pkas, diacid_pkas, pH_a[i])
        Q_a[i]=Q
    pH_Q = np.vstack((pH_a,Q_a))
    return pH_Q



def fragmentMol(mol, breakableBonds, atomNum):
    # Function from breaking and capping
    readwritemol = Chem.RWMol(mol)
    for bond in breakableBonds: 
        atm1 = bond[0]
        atm2 = bond[1]
        readwritemol.RemoveBond(atm1, atm2)
        amineC = readwritemol.AddAtom(Chem.Atom(6))
        amineCO = readwritemol.AddAtom(Chem.Atom(8))
        amineCOC = readwritemol.AddAtom(Chem.Atom(6))
        readwritemol.AddBond(atm1, amineC, Chem.BondType.SINGLE) 
        readwritemol.AddBond(amineC, amineCO, Chem.BondType.DOUBLE) 
        readwritemol.AddBond(amineC, amineCOC, Chem.BondType.SINGLE) 
        newatom2 = readwritemol.AddAtom(Chem.Atom(atomNum))
        readwritemol.AddBond(atm2, newatom2, Chem.BondType.SINGLE) 
        fragmentedSmiles = Chem.MolToSmiles(readwritemol)
    return fragmentedSmiles

def break_amide_bonds_and_cap(mol):
    ### SMARTS pattern
    amideSMARTS = '[NX3,NX4;H0,H1][CX3](=[OX1])' # secondary and tertiary amide bonds
    amidePattern = Chem.MolFromSmarts(amideSMARTS)
    atomNum = 6

    breakableBonds = []
    #molname=mol.GetProp("_Name")
    smiles = Chem.MolToSmiles(mol)
    if mol.HasSubstructMatch(amidePattern):
        #smiles = Chem.MolToSmiles(mol)
        #results.write("%s," % molname)
        atomIDs = mol.GetSubstructMatches(amidePattern)
        for bond in atomIDs:
            breakableBonds.append((bond[0],bond[1]))
        fragmentedSmiles = fragmentMol(mol, breakableBonds, atomNum)
    else:
        fragmentedSmiles = smiles

    fragmentedSmilesList = fragmentedSmiles.split(".")
    numFrags = len(fragmentedSmilesList)
    #print("%s fragmented into %s pieces" % (molname,numFrags))
    return fragmentedSmilesList


def mean(lst):
    """calculates mean"""
    return sum(lst) / len(lst)

def stddev(lst):
    """returns the standard deviation of lst"""
    mn = mean(lst)
    variance = sum([(e-mn)**2 for e in lst])
    return math.sqrt(variance)

def stddev(lst):
    """returns the standard deviation of lst"""
    mn = mean(lst)
    variance = sum([(e-mn)**2 for e in lst])
    return math.sqrt(variance)

def stderr(lst):
    """returns the standard error of the mean of lst"""
    mn = mean(lst)
    variance = sum([(e-mn)**2 for e in lst])
    return math.sqrt(variance) / math.sqrt(len(lst))

def print_output_prop_dict(prop_dict,prop,l_print_pka_set=False):
    global tit
    lj=12
    #keys = prop_dict.keys()
    keys = list(prop_dict.keys())
    keys.remove('std'); keys.insert(0, 'std')
    keys.remove('err'); keys.insert(0, 'err')
    keys.remove(prop + ' mean'); keys.insert(0, prop+' mean')
    tit="sequence"
    print(" ")
    print("======================================================================================================================================================")
    print(prop)
    print( "---------------------------------")
    for k in keys:
        p = prop_dict[k]
        print(k.rjust(lj)  + "  " +  str(round(p,2)).ljust(lj) )
    print(" ")

    if l_print_pka_set: print_pka_set()

    return


### PLOT titration curve
def plot_titration_curve(pH_Q_dict,figFileName):
    matplotlib.rcParams.update({'font.size': 16})
    lines = ["-","--","-.",":"]
    w1=4.0 ; w2=3.0 ; w3=2.0 ; w4=1.0
    linew = [w1,w1, w2,w2, w3,3, w4,w4]
    linecycler = cycle(lines)
    linewcycler = cycle(linew)

    figure(figsize=(8,6))
    i=0
    for pKaset in pKa_sets_to_use:
        i+=1
        pH_Q = pH_Q_dict[pKaset] 
        l=plot(pH_Q[:,0],pH_Q[:,1],next(linecycler),label=pKaset,linewidth=next(linewcycler)) 
        if pKaset == 'IPC_peptide': 
            setp(l,linewidth=8,linestyle='-',color='k')

        # Store data for output
        if i==1: 
            pH = pH_Q[:,0]
            Q_M = pH_Q[:,1]
        else:
            Q_M = column_stack([Q_M,pH_Q[:,1]])

    plot(pH,pH*0,'k-')
    plot([7,7],[np.min(Q_M),np.max(Q_M)],'k-')
    #xlim([np.min(pH),np.max(pH)])
    xlim([3,11])
    ylim([np.min(Q_M),np.max(Q_M)])

    legend(loc="center right", bbox_to_anchor=[1.1, 0.5],ncol=1, shadow=True, fontsize=10).get_frame().set_alpha(1)
    ylabel('peptide charge')
    xlabel('pH')
	
    title('pI based on hybrid pKa set. Fasta and Fragments.')    
	
    minorticks_on()
    grid(True)

    #show()
    savefig(figFileName)
    return



def calc_rdkit_pI(options={'smiles':'','inputFile':'','outputFile':'','use_acdlabs':False,'use_dimorphite':True,'l_print_fragments':False,'l_plot_titration_curve':False,'l_print_pka_set':False,'l_json':False}):

    args = Dict2Class(options)

    # Get options
    if len(args.smiles)!=0:
        # assume smiles input
        suppl = [ Chem.MolFromSmiles(args.smiles) ]    
    elif len(args.inputFile)!=0:
        # Assume filename as input
        inputFile = args.inputFile
        filename, ext = os.path.splitext(inputFile)

        # Initialize file reader
        if   ext == '.sdf':
            suppl = Chem.SDMolSupplier(inputFile) 
        elif ext == '.smi':
            suppl = Chem.SmilesMolSupplier(inputFile,titleLine=False) 
        else:
            raise Exception('!Warning: extension of file is not smi or sdf. Assume it is smi. Continue. ')
            suppl = Chem.SmilesMolSupplier(inputFile,titleLine=False) 

    else:
        raise Exception('Error: either smiles or input file should be given for rdkit_pI.py. Exit. ')
        sys.exit(1)



    # run calculations
    dict_output_rdkit_pI={}
    molid_ind = 0
    molid_ind_list = []
    molid_list = []
    for mol in suppl:
        molid_ind+=1
        molid='tmpmolid'+str(molid_ind)
        molid_list += [molid]

        # break amide bonds
        frags_smi_list = break_amide_bonds_and_cap(mol)
        #print(frags_smi_list)


        # match known amino-acids with defined pKas
        unknown_frags,base_pkas_fasta,acid_pkas_fasta,diacid_pkas_fasta = get_pkas_for_known_AAs(frags_smi_list)
        #print('UNKNOWN_FRAGMENTS: '+'   '.join(unknown_frags))

        # caclulate pKas for unknown fragmets
        if len(unknown_frags) > 0: base_pkas_calc,acid_pkas_calc,diacid_pkas_calc = calc_pkas(unknown_frags,use_acdlabs=args.use_acdlabs,use_dimorphite=args.use_dimorphite)
        else: base_pkas_calc,acid_pkas_calc,diacid_pkas_calc = [],[],[]

        # loop over all pKa sets
        seq_dict={}
        pI_dict={}
        Q_dict={}
        pH_Q_dict={}
        for pKaset in pKa_sets_to_use:

            # merge fasta and calcualted pkas
            base_pkas = base_pkas_fasta[pKaset] + base_pkas_calc
            acid_pkas = acid_pkas_fasta[pKaset] + acid_pkas_calc
            diacid_pkas = diacid_pkas_fasta[pKaset] + diacid_pkas_calc

            all_base_pkas=[]
            all_acid_pkas=[]
            all_diacid_pkas=[]
            if len(base_pkas) != 0: all_base_pkas,all_base_pkas_smi = zip(*base_pkas) 
            else: all_base_pkas,all_base_pkas_smi = [],[]
            if len(acid_pkas) != 0: all_acid_pkas,all_acid_pkas_smi = zip(*acid_pkas) 
            else: all_acid_pkas,all_acid_pkas_smi = [],[]
            if len(diacid_pkas) != 0: all_diacid_pkas,all_diacid_pkas_smi = zip(*diacid_pkas) 
            else: all_diacid_pkas,all_diacid_pkas_smi = [],[]

            # calculate isoelectric point
            pI = calculateIsoelectricPoint(all_base_pkas, all_acid_pkas, all_diacid_pkas)
            pH_Q = CalcChargepHCurve(all_base_pkas, all_acid_pkas, all_diacid_pkas)
            pH_Q = pH_Q.T
            #print( "pI ACDlabs %6.3f" % (pI) )

            # calculate isoelectric point
            Q = calculateMolCharge(all_base_pkas, all_acid_pkas, all_diacid_pkas, 7.4)
            #print( "Q at pH7.4 ACDlabs %4.1f" % (Q) )

            pI_dict[pKaset] = pI
            Q_dict[pKaset] = Q
            pH_Q_dict[pKaset] = pH_Q

        # pI 
        pIl=[]
        #for k,v in pI_dict.iteritems(): pIl += [v]
        for k in pI_dict.keys(): pIl += [pI_dict[k]]
        pI_dict['pI mean']=mean(pIl)
        pI_dict['std']=stddev(pIl)
        pI_dict['err']=stderr(pIl)
        #seq_dict[seq]=pI_dict
        #PrintOutput(pI_dict,'pI',l_print_pka_set=args.l_print_pka_set)

        # charge at pH=7.4
        Ql=[]
        #for k,v in Q_dict.iteritems(): Ql += [v]
        for k in Q_dict.keys(): Ql += [Q_dict[k]]
        Q_dict['Q at pH7.4 mean']=mean(Ql)
        Q_dict['std']=stddev(Ql)
        Q_dict['err']=stderr(Ql)
        #seq_dict[seq]=Q_dict
        #PrintOutput(Q_dict,'Q at pH7.4',l_print_pka_set=False)

        # print interval
        pKaset='IPC_peptide'
        int_tr = 0.2

        pH_Q = pH_Q_dict[pKaset]
        Q=pH_Q[:,1]
        pH=pH_Q[:,0]
        pH_int = ( pH[(Q>-int_tr) & (Q<int_tr)] )
        interval = (pH_int[0], pH_int[-1])

        # plot titration curve
        if args.l_plot_titration_curve:
            figFileName = "OUT_titration_curve_rdkit_pI.png"
            plot_titration_curve(pH_Q_dict,figFileName)
        else:
            figFileName = ""
        
        molid_ind_list.append(molid_ind)
        dict_output_rdkit_pI[molid_ind]={'molid':molid,
                                    'pI':pI_dict,
                                    'QpH7':Q_dict,
                                    'pI_interval':interval,
                                    'plot_filename':figFileName,
                                    'base_pkas_fasta':base_pkas_fasta,
                                    'acid_pkas_fasta':acid_pkas_fasta,
                                    'diacid_pkas_fasta':diacid_pkas_fasta,
                                    'base_pkas_calc':base_pkas_calc,
                                    'acid_pkas_calc':acid_pkas_calc,
                                    'diacid_pkas_calc':diacid_pkas_calc,
                                    'pI_interval_threshold':int_tr,
                                    'pKa_set':pKaset
                                    }

    dict_output_rdkit_pI['molid_ind_list'] = molid_ind_list

    return dict_output_rdkit_pI



def print_output(dict_output_rdkit_pI,args):

    #for molid in dict_output_rdkit_pI['molid_list']:
    for molid_ind in dict_output_rdkit_pI['molid_ind_list']:
    
        molid = dict_output_rdkit_pI[molid_ind]

        print_output_prop_dict(dict_output_rdkit_pI[molid_ind]['pI'],'pI',l_print_pka_set=args.l_print_pka_set)
        print_output_prop_dict(dict_output_rdkit_pI[molid_ind]['QpH7'],'Q at pH7.4',l_print_pka_set=False)

        if args.use_acdlabs: predition_tool = 'ACDlabs'
        elif args.use_dimorphite: predition_tool = 'modified Dimorphite-DL'

        int_tr = dict_output_rdkit_pI[molid_ind]['pI_interval_threshold']
        base_pkas_fasta = dict_output_rdkit_pI[molid_ind]['base_pkas_fasta']
        acid_pkas_fasta = dict_output_rdkit_pI[molid_ind]['acid_pkas_fasta']
        diacid_pkas_fasta = dict_output_rdkit_pI[molid_ind]['diacid_pkas_fasta']
        base_pkas_calc = dict_output_rdkit_pI[molid_ind]['base_pkas_calc']
        acid_pkas_calc = dict_output_rdkit_pI[molid_ind]['acid_pkas_calc']
        diacid_pkas_calc = dict_output_rdkit_pI[molid_ind]['diacid_pkas_calc']
        pKaset = dict_output_rdkit_pI[molid_ind]['pKa_set']

        print(" ")
        print("pH interval with charge between %4.1f and %4.1f for pKa set: %s and prediction tool: %s" % (-int_tr,int_tr,pKaset,predition_tool) )
        print("%4.1f - %4.1f" % (dict_output_rdkit_pI[molid_ind]['pI_interval'][0],dict_output_rdkit_pI[molid_ind]['pI_interval'][1]))

        if args.l_print_fragments:

            # merge fasta and calcualted pkas
            base_pkas = base_pkas_fasta[pKaset] + base_pkas_calc
            acid_pkas = acid_pkas_fasta[pKaset] + acid_pkas_calc
            diacid_pkas = diacid_pkas_fasta[pKaset] + diacid_pkas_calc
            all_base_pkas=[]
            all_acid_pkas=[]
            all_diacid_pkas=[]
            if len(base_pkas) != 0: all_base_pkas,all_base_pkas_smi = zip(*base_pkas) 
            else: all_base_pkas,all_base_pkas_smi = [],[]
            if len(acid_pkas) != 0: all_acid_pkas,all_acid_pkas_smi = zip(*acid_pkas) 
            else: all_acid_pkas,all_acid_pkas_smi = [],[]
            if len(diacid_pkas) != 0: all_diacid_pkas,all_diacid_pkas_smi = zip(*diacid_pkas) 
            else: all_diacid_pkas,all_diacid_pkas_smi = [],[]
        
            print(" ")
            print("List of calculated BASE pKa's with the corresponding fragments")
            for pkas,smi in zip(all_base_pkas,all_base_pkas_smi):
                s_pkas = ["%4.1f"%(pkas)]
                print("smiles or AA, base pka : %-15s %s" % (smi,' '.join(s_pkas)))

            print(" ")
            print("List of calculated ACID pKa's with the corresponding fragments")
            for pkas,smi in zip(all_acid_pkas,all_acid_pkas_smi):
                s_pkas = ["%4.1f"%(pkas)]
                print("smiles or AA, acid pka : %-15s %s" % (smi,' '.join(s_pkas)))

            print(" ")
            print("List of calculated DIACID pKa's with the corresponding fragments")
            for pkas,smi in zip(all_diacid_pkas,all_diacid_pkas_smi):
                s_pkas = ["%4.1f  %4.1f"%(pkas[0],pkas[1])]
                print("smiles or AA, diacid pka : %-15s %s" % (smi,' '.join(s_pkas)))

    return







def args_parser():
    #usage = "rdkit_pI.py  -i input_file  --print_fragment_pkas"
    parser = argparse.ArgumentParser(description="Script caclultes isoelectric point of a molecules by cutting all amide bonds, retreiving stored pka values for known AAs, predicting pKas of unknown fragemnts using modified Dimorphite-DL or ACDlabs, and calculating Henderson-Hasselbalch equation.")
    parser.add_argument("-i", dest="inputFile", help="input file with molecule structure. smi or sdf",default='')
    parser.add_argument("-s", dest="smiles", help="input smiles. if used then single smi is assumed and fasta returned in stdout. filenames are ignored",default='')
    parser.add_argument("-o", dest="outputFile", help="output file with molecule structure. fasta",default='')

    parser.add_argument("--plot_titration_curve",default=False, action='store_true',dest="l_plot_titration_curve", help="Plot titration curve and store it in OUT_titration_curve_rdkit_pI.png file.")
    parser.add_argument("--print_fragment_pkas",default=False, action='store_true',dest="l_print_fragments", help="Print out fragments with corresponding pKas used in pI calcution.")
    parser.add_argument("--print_pka_set",default=False, action='store_true',dest="l_print_pka_set", help="Print out stored pka sets explicitly.")
    parser.add_argument("--use_acdlabs",default=False, action='store_true',dest="use_acdlabs", help="Use acdlabs for pka prediction of unknown fragments.")
    parser.add_argument("--use_dimorphite",default=False, action='store_true',dest="use_dimorphite", help="Use modified Dimorphite-DL for pka prediction of unknown fragments.")
    parser.add_argument("--json",default=False, action='store_true',dest="l_json", help="Output in JSON format.")

    args = parser.parse_args()
    options = args.__dict__

    return args,options



if __name__ == "__main__":

    args,options = args_parser()

    dict_output_rdkit_pI = calc_rdkit_pI(options)

    if args.l_json:
        print(json.dumps(dict_output_rdkit_pI))
    else:
        print_output(dict_output_rdkit_pI,args)    
        


    