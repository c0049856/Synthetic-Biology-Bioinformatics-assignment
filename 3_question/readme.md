## 3. Explore PCR planning with the virtual simulator 

Read Fellermann et al. (2019), Design of experiments and the virtual PCR simulator: An online game for pharmaceutical scientists and biotechnologists. Pharmaceutical Statistics 18, 402–406. DOI 10.1002/pst.1932. 

1. Open the simulator introduction and access links 

2. Familiarise yourself with the controls and with the meanings of DNA yield and purity. Run a baseline reaction and record every setting and both outputs.
- the baseline reaction gives us 0.1ql yield and 10.5% purity.
- If we only change the polymerase from Taq to Phusion, we immediately get 0.2 yield, and 13.4% purity. This is the first adjustable factor we are changing (does it count?)
- then we can change the amount of cycles. now it is 15. If we move it to 35 (with every other thing intact), we get 1.2 yield, with 34.5% purity. Let's test this with low value (low amount of cycles, 5): it gives us 0.0 yield, and 7.4% purity. What about a high number (let's do 50)? It gave us 3.3 yield, and 52.4% of purity. Which is already much better.
- But what if the second condition is annealing temperature? We can calculate the annealing temperature required for the reaction, using NEB Tm calculator.
- We can calculate the final primer concentration using c1v1=c2v2. But the simulator does not specify the volume we are using (the final volume for the reaction). Therefore, we are going to assume it is 50ql, because that is what 1 unit of Phusion polymerase is going to work the best with.
- therefore, c1v1=c2v2 will give us: 10qlx1ql/50ql = 0.2qm = 200nM for each primer. This is a bit lower than NEBs recommendation for Phusion, which would be 0.5qM (500nM) for each primer. Since we can only change two parameters, we cannot really change it. Primer concentration is a variable we still need to check and optimise for real reactions.
- After putting this information (Phusion, 200nM) in NEB Tm calculator, we get the annealing temperature of 61C. So now, we are gonna check all of the settings the same as default (including no of cycles at 15) and only change the annealing C to 61 instead of 68.
- original parameters gave us 0.2 yield, and purity of 14.1%. Now lets check this with annealing temp at 45 (low) - this gives us 0.2 yield, and 12.9% purity;
- now with high annealing temperature: lets use 79 (basically denaturation). Surprisingly, we got purity of 14.8% and yield of 0.3
- lets try with 35 cycles and annealing temp of 61. This gives us 1.3 yield and 35.7% purity.
- that is two conditions done. But how to maximize the yield and purity? Let's look at NEB Phusion parameters (online), this is what it suggests for 50ql reaction:
  -  10ql phusion buffer;
  -  1ql 10dM dNTPs;
  -  2.5ql 10qL F/R primers;
  -  variable template amount;
  -  0.5ql phusion DNA polymerase
- Thermocycling:
  - 25-35 cycles:
    - 98C for 5-10 seconds;
    - 42-72C for 10-30 seconds;
    - 72C for 15-39 seconds/kb.
If we wanted to maximize the yield and purity for our reaction, we should increase teh thermocycling temperatures accordingly (the extension temperature now is too low). If we move extension temperature to 72 and annealing to 61, but keep cycles at 15, we still get 0.2 yield and 13.5 purity. If we increase the numebr of cycles to 35, we then get 1.2 yield, with 34.2% purity.
Let's change the timings: annealing lets put 20 seconds, extension lets leave on 20 (no of cycles 35, denaturation at 80, annealing at 61, extension at 72). This now gives us 2.1 yield, and 46.2% of purity.
lets also change denaturation (on top of everything) to 98. AHA! This si giving us yield of 95.0, and purity of 81.8%. Let's lower annealing time to 10 seconds. this moved this down to 57.4 yield and 59.7% purity.
okay, then lets do annealing at 20 and extension at 30 seconds. this gives us 96.5 yield, and 82.8% purity.
If we change annealing temp tp 65 (from 61), we get: 102.5 yield and 88.2% purity.
if on top of that we change denaturation to 8 sec instead of 10, we get: 86.1 and 79.3% purity.

SO far the best results we have are: 35 cycles; denaturation at 98 for 10, annealing at 65 for 20, extension at 72 for 30. The results change every time we run the simulation (?)
if we increase annealing time to 25 secs, we get 106.2 yield with 89.8% purity. 

WHAT CLAUDE SAID: 
- The denaturation temperature: purity went from 46 to 82% when denaturation got changed from 80 to 98C. WHich makes sense, because at 80C 5kB plasmid template barely melts, and also this explains why annealing temperature change made no difference. The effect of annealing temperature depends on the other conditions.
- The run-to-run variation: the simulator is stochastic, which is the whole point of Fellermann's paper. It behaves like a real lab with noise. Therefore, each condition must be ran at least three times, and mead SD should be reported.


We have a new baseline now, these are the parameters: 
no cycles 35; denaturation at 98 for 10, annealing at 65 for 25, extension at 72 for 30. each dNTP is 1ql, each rpimer is 1ql, plasmid is at 50ng, polymerase at 1U (phusion). 
We have done 3 runs, with the following yield and purity: 124.2, 96.8%; 120.7, 96.6%; 121.9, 97.1%. In total, this gives us a mean +- SD of 122.3+-1.8 (yield) and 96.8+-0.3 purity. 

For 2x2 we can use cycles and annealing temperature, with everything else at the baseline. 3 reps each:
Condition A: 25 cycles (low), 58 annealing (low): 118.8 yield, 96.7% purity; 122.2 yield, 97% purity; 116.4 yield, 96.8% purity. 
condition B: 25 cycles, 68 annealing (high): 67.8 yield, 77% purity; 67.3 yield, 76.6% purity; 73.9 yield, 78.9% purity. 
condition C: 35 cycles (high), 58 annealing: 118.4, 96.4%; 119.8, 96.8%; 119.2,  97.0%. 
condition D: 35 cycles, 68 annealing: 107.8, 91.7%; 109.0, 92.4%; 111.5, 93.2%. 
Condition E: 25 cycles, 61 annealing: 115.8, 95.8%; 119.0, 96.9%; 121.1, 97.0%. 
Condition F: 35 cycles, 61 annealing: 121.4, 96.9%; 118.5, 97.0%; 120.7, 96.9%. 

What am i predicting: more cycles should raise yield at both temperatures. at 58, more cycles probably will cause less purity, since it will be amplying mispriming products, but at 68 annealing, the purity should stay high. 

What Claude said: 
- at 58C, cycles do nothing. A and C are identical, and extra 10 cycles only add time. by 25 cycles, the reaction has already plateaued, maybe because dNTPs or primers ran out.
- at 68C, cycles matter a lot. yield goes from about 70 to about 109, and purity from 78% to 92%. 68 is above the primers' optimal annealing temperature, and fewer primers bind each cycle, so amplification is less efficient. with only 25 cycles, the reaction hasn't reached plateau, and the target makes up smaller share of DNA. More cycles partly make up for this, but even at 35 cycles, 68 does not catch up.
- 58 and 61 C gave the same results within the noise, and the simulator penalises poor priming at high temperatures much more than mispriming at low temperatures.
- the previous predictions were wrong. we expected low annealing plus extra cycles to cost purity, but then in fact high annealing plus too few cycles were the problem.
- proposed condition: condition E. It matches the best yield, and purity, and is shorter (and has three replicates already). 61 must be chosen over 58, because in a real reaction, lower annealing temperatures increase mispriming risks, and 61C is the NEB-calculated value. This is a good example for step 6 - something the simulator underplays and we still need to check.
- what to try next: cycle titration at 61 (for example, 15, 20, 25) to find the fewest cycles that reach plateau.
- lower plasmid input (10ng, 1g), lower input will need more cycles though - more time.
- real lab, gradient PCR around 58-66, with a gel to check for a single kB band. 

4. Choose two adjustable factors, such as annealing temperature and polymerase amount. Predict their effects, then test a low and a high value of each in all four combinations, keeping the other settings fixed.
  
5. Compare yield and purity across the runs. Identify whether the effect of one factor depends on the other. Choose a promising condition, test it again and explain what you would try next. 

6. Write a short PCR plan justified by your results. State which features the simplified simulator omits and which choices would still need checking in a real reaction. 

7. Keep a settings and results table, one comparison plot and a short explanation of your proposed PCR conditions.
