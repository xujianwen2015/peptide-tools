###
### NOTICE: this file did not exit in the original Dimorphite_DL release. 
### The is newly created based on "sites_substructures.smarts" file
### - made a readable Python module from it. Andrey Frolov, 2020-09-15
### - added last column with acid-base classification. Andrey Frolov, 2020-09-11 
### - added TATA substructure. Andrey Frolov, 2020-09-15
### Should be consistent with the current "sites_substructures.smarts" file
### 

data_txt='''
TATA   CC(=O)N1CN(CN(C1)C(C)=O)C(C)=O  NaN    NaN   NaN   base

*Azide	[N+0:1]=[N+:2]=[N+0:3]-[H]	2	4.65	0.07071067811865513    acid
Nitro	[C,c,N,n,O,o:1]-[NX3:2](=[O:3])-[O:4]-[H]	3	-1000.0	0   acid
AmidineGuanidine1	[N:1]-[C:2](-[N:3])=[NX2:4]-[H:5]	3	12.025333333333334	1.5941046150769165   base
AmidineGuanidine2	[C:1](-[N:2])=[NX2+0:3]	2	10.035538461538462	2.1312826469414716  base
Sulfate	[SX4:1](=[O:2])(=[O:3])([O:4]-[C,c,N,n:5])-[OX2:6]-[H]	5	-2.36	1.3048043093561141  acid
Sulfonate	[SX4:1](=[O:2])(=[O:3])(-[C,c,N,n:4])-[OX2:5]-[H]	4	-1.8184615384615386	1.4086213481855594  acid
Sulfinic_acid	[SX3:1](=[O:2])-[O:3]-[H]	2	1.7933333333333332	0.4372070447739835  acid
Phenyl_carboxyl	[c,n,o:1]-[C:2](=[O:3])-[O:4]-[H]	3	3.463441968255319	1.2518054407928614  acid
Carboxyl	[C:1](=[O:2])-[O:3]-[H]	2	3.456652971502591	1.2871420886834017   acid
Thioic_acid	[C,c,N,n:1](=[O,S:2])-[SX2,OX2:3]-[H]	2	0.678267	1.497048763660801  acid
Phenyl_Thiol	[c,n:1]-[SX2:2]-[H]	1	4.978235294117647	2.6137000480499806 acid
Thiol	[C,N:1]-[SX2:2]-[H]	1	9.12448275862069	1.3317968158171463  acid

# [*]OP(=O)(O[H])O[H]. Note that this matches terminal phosphate of ATP, ADP, AMP.
Phosphate	[PX4:1](=[O:2])(-[OX2:3]-[H])(-[O+0:4])-[OX2:5]-[H]	2	2.4182608695652172	1.1091177991945305	5	6.5055	0.9512787792174668  diacid

# Note that Internal_phosphate_polyphos_chain and
# Initial_phosphate_like_in_ATP_ADP were added on 6/2/2020 to better detail with
# molecules that have polyphosphate chains (e.g., ATP, ADP, NADH, etc.). Unlike
# the other protonation states, these two were not determined by analyzing a set
# of many compounds with experimentally determined pKa values.

# For Internal_phosphate_polyphos_chain, we use a mean pKa value of 0.9, per
# DOI: 10.7554/eLife.38821. For the precision value we use 1.0, which is roughly
# the precision of the two ionizable hydroxyls from Phosphate (see above). Note
# that when using recursive SMARTS strings, RDKit considers only the first atom
# to be a match. Subsequent atoms define the environment.
Internal_phosphate_polyphos_chain	[$([PX4:1](=O)([OX2][PX4](=O)([OX2])(O[H]))([OX2][PX4](=O)(O[H])([OX2])))][O:2]-[H]	1	0.9	1.0  acid

# For Initial_phosphate_like_in_ATP_ADP, we use the same values found for the
# lower-pKa hydroxyl of Phosphate (above).
Initial_phosphate_like_in_ATP_ADP	[$([PX4:1]([OX2][C,c,N,n])(=O)([OX2][PX4](=O)([OX2])(O[H])))]O-[H]	1	2.4182608695652172	1.1091177991945305 acid

# [*]P(=O)(O[H])O[H]. Cannot match terminal phosphate of ATP because O not among [C,c,N,n]
Phosphonate	[PX4:1](=[O:2])(-[OX2:3]-[H])(-[C,c,N,n:4])-[OX2:5]-[H]	2	1.8835714285714287	0.5925999820080644	5	7.247254901960784	0.8511476450801531  diacid

Phenol	[c,n,o:1]-[O:2]-[H]	1	7.065359866910526	3.277356122295936  acid
Peroxide1	[O:1]([$(C=O),$(C[Cl]),$(CF),$(C[Br]),$(CC#N):2])-[O:3]-[H]	2	8.738888888888889	0.7562592839596507  acid
Peroxide2	[C:1]-[O:2]-[O:3]-[H]	2	11.978235294117647	0.8697645895163075  acid
O=C-C=C-OH	[O:1]=[C;R:2]-[C;R:3]=[C;R:4]-[O:5]-[H]	4	3.554	0.803339458581667  acid
Vinyl_alcohol	[C:1]=[C:2]-[O:3]-[H]	2	8.871850714285713	1.660200255394124 acid
Alcohol	[C:1]-[O:2]-[H]	1	14.780384615384616	2.546464970533435 acid
N-hydroxyamide	[C:1](=[O:2])-[N:3]-[O:4]-[H]	3	9.301904761904762	1.2181897185891002  acid
*Ringed_imide1	[O,S:1]=[C;R:2]([$([#8]),$([#7]),$([#16]),$([#6][Cl]),$([#6]F),$([#6][Br]):3])-[N;R:4]([C;R:5]=[O,S:6])-[H]	3	6.4525	0.5555627777308341  acid
*Ringed_imide2	[O,S:1]=[C;R:2]-[N;R:3]([C;R:4]=[O,S:5])-[H]	2	8.681666666666667	1.8657779975741713  acid
*Imide	[F,Cl,Br,S,s,P,p:1][#6:2][CX3:3](=[O,S:4])-[NX3+0:5]([CX3:6]=[O,S:7])-[H]	4	2.466666666666667	1.4843629385474877  acid
*Imide2	[O,S:1]=[CX3:2]-[NX3+0:3]([CX3:4]=[O,S:5])-[H]	2	10.23	1.1198214143335534  acid
*Amide_electronegative	[C:1](=[O:2])-[N:3](-[Br,Cl,I,F,S,O,N,P:4])-[H]	2	3.4896	2.688124315081677  acid
*Amide	[C:1](=[O:2])-[N:3]-[H]	2	12.00611111111111	4.512491341218857  acid
*Sulfonamide	[SX4:1](=[O:2])(=[O:3])-[NX3+0:4]-[H]	3	7.9160326086956525	1.9842121316708763  acid
Anilines_primary	[c:1]-[NX3+0:2]([H:3])[H:4]	1	3.899298673194805	2.068768503987161  base
Anilines_secondary	[c:1]-[NX3+0:2]([H:3])[!H:4]	1	4.335408163265306	2.1768842022330843  base
Anilines_tertiary	[c:1]-[NX3+0:2]([!H:3])[!H:4]	1	4.16690685045614	2.005865735782679  base
Aromatic_nitrogen_unprotonated	[n+0&H0:1]	0	4.3535441240733945	2.0714072661859584   base
Amines_primary_secondary_tertiary	[C:1]-[NX3+0:2]	1	8.159107682388349	2.5183597445318147   base

# e.g., [*]P(=O)(O[H])[*]. Note that cannot match the internal phosphates of ATP, because
# oxygen is not among [C,c,N,n,F,Cl,Br,I]  
Phosphinic_acid	[PX4:1](=[O:2])(-[C,c,N,n,F,Cl,Br,I:3])(-[C,c,N,n,F,Cl,Br,I:4])-[OX2:5]-[H]	4	2.9745	0.6867886750744557  diacid

# e.g., [*]OP(=O)(O[H])O[*]. Cannot match ATP because P not among [C,c,N,n,F,Cl,Br,I]  
Phosphate_diester	[PX4:1](=[O:2])(-[OX2:3]-[C,c,N,n,F,Cl,Br,I:4])(-[O+0:5]-[C,c,N,n,F,Cl,Br,I:4])-[OX2:6]-[H]	6	2.7280434782608696	2.5437448856908316  acid

# e.g., [*]P(=O)(O[H])O[*]. Cannot match ATP because O not among [C,c,N,n,F,Cl,Br,I].
Phosphonate_ester	[PX4:1](=[O:2])(-[OX2:3]-[C,c,N,n,F,Cl,Br,I:4])(-[C,c,N,n,F,Cl,Br,I:5])-[OX2:6]-[H]	5	2.0868	0.4503028610465036   acid

Primary_hydroxyl_amine	[C,c:1]-[O:2]-[NH2:3]	2	4.035714285714286	0.8463816543155368  acid
*Indole_pyrrole	[c;R:1]1[c;R:2][c;R:3][c;R:4][n;R:5]1[H]	4	14.52875	4.06702491591416  acid
*Aromatic_nitrogen_protonated	[n:1]-[H]	0	7.17	2.94602395490212  acid
'''


