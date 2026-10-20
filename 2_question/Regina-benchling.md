The plasmid: 
- backbone taken from addgene (https://www.addgene.org/browse/sequence/513490/)
), 2,686 + 514 filler sequence (copying the non-coding regions);
- insert:
  - promoter taken from https://www.addgene.org/browse/sequence/372941/. lac promoter used (31bp), and 109bp filler sequence (from random sequence generator) added;
  -   RBS: Shine-Dalgarno sequence used (aggagg), with 17bp filler sequence;
  -   the GFP coding sequence taken from: https://www.addgene.org/browse/sequence/139439/, 708bp, extented to 717 adding 9bp filler sequence;
  -   the terminator taken from: https://www.addgene.org/browse/sequence/139439/ T7Te terminator (28bp) + 92 filler sequence.

Once the insert was created, the restriction enzyme sequences were checked and added (EcoRI GAATTC) in front of the promoter and BamHI (GGATCC) right after the terminator. 

The restriction was performed on the backbone and the insert, then they were ligated together to receive 4185bp restriction assembly. The insert had to be inverted and therefore the orientation did not match. 

Then the insert was redesigned (with BamHI in front of promoter and EcoRI right after the terminator), resulting in the correct orientation insert. 


For Gibson/Golden Gate, primers were introduced that would create a BsaI cut site. The overall product created was 4212bp long (primers introduced overhangs). 

If BsaI site is introduced: 
- do we need two BsaI sites? 
------------------------------------------------------------------------------------
Comparing them side by side there is a difference in the position to where the insert has been inserted. The restriction enzymes cut the backbone open at ~1,040bp, opened it up and put the insert there. For Gibson/Golden Gate ligation, the primers introduced 
