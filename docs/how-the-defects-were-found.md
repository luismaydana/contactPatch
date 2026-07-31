# How the defects were found

Five errors sat inside this model for months without anyone noticing, including the person who wrote it. They were all found in a single day. This is a record of what actually surfaced them, because the method transfers and the defects do not.

The short version: **none of them were found by reading the code looking for bugs.** Every one came out of being asked a question the code had never been asked.

## The one that mattered most, and the accident that exposed it

Someone asked a question that had nothing to do with bugs: *how does this compare to the stupidest possible model?*

The stupid model is one line. Take last year's pole time at that circuit, multiply by a constant. No physics, no tyre, no energy.

It scored better than the physics. σ 0.99% against 1.32%.

That result did not identify a single defect. What it did was **remove the assumption that the model was basically fine**. Up to that point every investigation started from "the model works, where is the small error?" and after it, the question became "is anything in here doing what it claims?" Nothing else changed. The same code was read by the same person, and the errors became visible.

That is the transferable part. A baseline is not primarily a benchmark. It is a device for revoking your own benefit of the doubt.

## The lap that never closed

Found by asking what the model does at the start/finish line.

A flying lap is a loop, so the speed leaving the timing line has to be the speed arriving at it. Printing both took one line:

```
Monza      v at the line 101.60 m/s     v at the end 83.04 m/s
```

Eighteen metres per second, out of nothing, every lap, every circuit. Worth up to 1.67% of lap time, which is more than the model's entire stated uncertainty at one venue.

Two things about how this survived. First, it never crashed, never produced a negative number, never tripped a gate; it just quietly made every lap faster than it should have been. Nothing in the test suite asked whether a lap is a loop, because nobody thought to.

Second, and this is the uncomfortable part: `ARCHITECTURE.md` contains a written proof that the solver is correct, and that proof is right. Its base case says *the last point has nothing after it to brake for*. On a circuit, there is. **The proof was sound for a road, and the code drives a circuit.**

So writing the proof down did not prevent the bug. It is what made the bug findable in hindsight, which is a weaker claim than the one usually made for proofs and still worth the effort.

## The constant that did two jobs

Found by grepping for a number that appeared twice with different meanings.

`ETA_ERS = 0.92` is the efficiency of *spending* battery energy. The same constant was being used to credit energy *recovered* under braking, which is a physically different quantity with a lower value. The battery was being charged at a rate the lap had not earned.

The tell was that a second file, `ers_dp.py`, had a separately named `ETA_REGEN = 0.70` and got it right. One module had two names for two things; the other had one name for both. **The bug was invisible at the call site precisely because the name was plausible in both places.**

The measured cost was +0.56% of lap time, and the diagnosis was confirmed by its shape rather than by argument: the effect was smallest at Monza, which brakes least, and largest at Las Vegas and Austin, which brake most. An energy-accounting error has to scale with how much energy passes through the accounting. It did.

## The threshold nobody checked the units of

Found by an outside reader doing arithmetic I never had.

The deployment threshold was `P_ICE / F_DRIVE`, the speed at which *combustion power alone* stops saturating the drive-force cap. The quantity that matters is where *total* power stops saturating it, because below that point extra electrical power reaches the road as nothing. 33.3 m/s against a correct 52.5.

Worse than wasted charge: that threshold sets the acceleration-zone boundaries, the zones get ranked by length, and the two longest receive full power. Move the threshold and a different pair of zones gets the boost. The effect on lap time was up to 0.73% **with the sign changing between circuits**, so it was pure scatter and no amount of calibration could have absorbed it.

## The reference that was never checked for rain

Found by checking an assumption while building something else.

Every v2.3 call is built from a venue's 2025 pole lap. The model has a carefully declared rule that voids a call if the *2026* session is wet. Nobody had written the same rule for the *reference*.

Las Vegas 2025 ran on intermediates. Pole was 1:47.934 against 1:32.312 in the dry the year before. That call was built from a wet racing line and a top-speed anchor 16 km/h low.

The nine other references were checked one by one rather than assumed. Baku had rainfall recorded in the session and a dry pole lap on softs, within 0.25 s of the previous year at identical top speed, so it stays. **The check that matters is the compound the lap actually ran on, not whether it rained somewhere in the hour.**

## The filter that was hiding behind another filter

Found by reading what a published number was actually measuring.

Every call published a stability figure: the spread of the answer across three smoothing settings, around 0.4%, presented as evidence that the method is not fragile.

It swept the Savitzky-Golay window. Downstream of it sat a second box filter with its half-width hard-coded at 3, never varied, never mentioned. Sweeping that one instead moved the answer 7.5% across its plausible range.

The stability figure was real, honest, and measuring the wrong thing. Both are swept now, and the gate fires on every single call. **This one is not fixed, it is exposed**, and it is now the largest open question in the project: an answer that moves 2.57% under a defensible change of filter cannot claim 1.414% of precision without an argument nobody has made yet.

## What the corrections did, which was not what was expected

The expectation, written down and sealed before any code changed, was that σ would fall to somewhere between 1.0% and 1.3%. The closure defect varied six-fold between circuits, so removing it should have tightened the spread.

σ rose to 1.460%, and fell to 1.414% a day later when v4 removed a leak in the calibration.

The reason is measurable rather than speculative. Correlating how large the closure gap was at each circuit against how much removing it changed that circuit's error gives **r = −0.686**: the bigger the defect, the more its removal helped. The free speed had been **cancelling** against another error running the other way.

So the smaller σ was smaller partly because two mistakes were offsetting, and the number was flattering by coincidence rather than by accuracy. Two biases that cancel on the circuits you fitted have no obligation to keep cancelling on a circuit you have never seen, which is exactly the situation every remaining prediction is in.

That failure mode was already named in this project's own summer re-freeze document, about a different pair of errors. It has now been demonstrated on the model itself.

## What made the difference, in order

1. **A baseline that beat the model.** Not because it identified anything, but because it withdrew the assumption that the model was fine.
2. **Asking what a quantity should be, then printing it.** The lap closure, the two efficiencies, the threshold units. All visible in one line of output each, none of them ever printed.
3. **Checking that a published number measures what its label says.** The stability figure was the clearest case and it was also the most reassuring number in the project.
4. **Outside readers.** Several of these came from people reading the code cold with no stake in it being correct. The author had read those same lines many times.
5. **Sealing the fix list before fixing anything.** Not a discovery method, but the reason the result can be trusted: with the corrections declared in advance, σ going the wrong way is a finding rather than an embarrassment to be quietly re-tuned away.

## What did not work

Worth recording so it is not repeated.

The 23-case C++ test suite caught none of this, and could not have: it asserts signs, finiteness and monotonicity, and contains no pinned lap time. A test named *Ground effect increases downforce at high speed* asserts only that ride height is below its static value, which is true at any speed, and passes despite the model's downforce falling above 48 m/s.

Rereading the code did not work either. Every one of these lines had been read many times by the person who wrote them. **What worked was making the code answer a question, not making a person look at it.**

---

---

# Second round: the day after I said it was done

Everything above was written on 2026-07-29, at the end of a day that finished with a clean verification pass. Hashes reproducing, links resolving, no leaks, no forbidden strings. I wrote that the repository was ready to publish and I believed it.

The next morning I went back at it from five angles instead of one, each with a single question and no permission to be reassured. Can this protocol be cheated. Does every number recompute. Does the documentation work for someone who has never seen it. Do the repo and the site tell one story. What can a stranger learn about me from the files alone.

The answers were a calibration leak that invalidated the headline number, a false claim inside the document whose whole job is to let a reader check me, a test that reported success for zero work, and an arithmetic slip that had been quietly making the model look worse than it is.

## The one that forced a third re-freeze

`refit_loo.py` computes the seven-fold leave-one-out error that produces sigma. At the point where it predicts the held-out circuit it was passing that circuit's **2026** session air density. The density of the race it was predicting.

Production cannot do that. When a call is sealed in July the 2026 session has not happened, so `predict_v2.py` carries the 2025 value over. Every aerodynamic force scales linearly in density.

So sigma had never been an out-of-fold error at all. It was measured with an input the sealed calls do not have, by an amount nobody could state without recomputing it.

This is the same shape as the closure defect one section above, and the shape is worth more than the instance. Both were a quantity nobody printed, sitting in a path nobody thought of as a measurement. The closure bug hid because I never printed the speed at both ends of the lap. This one hid because I read the calibration script and the prediction script as two programs, when the whole point of a leave-one-out is that they have to be the *same* program run against a circuit it has not seen. A fold is a claim about equality between two code paths. I had never checked the equality.

## The one that is worst to write down

`predictions/VERIFY.md` is the page that tells a reader not to trust me. On 2026-07-29 I rewrote it at length to retract a claim that git commit dates prove ordering. Several hundred words, ending on the line that a page telling you to trust its author about the evidence for trusting its author would be worth nothing.

One heading below that, it said the sealed hashes "were committed and pushed before any of the ten sessions ran".

Nothing had been pushed. The working branch was 38 commits ahead of a remote containing none of it. That is the *same defect* that had forced the v3 re-freeze the day before, described in this same repository, in a file I had edited that afternoon.

I missed it because I read what I meant. That is the transferable part and it is duller than it sounds: rereading your own document does not audit it, because the sentence you wrote is the sentence you see. What found it was a pass with one question attached, is there a way to cheat this, run by someone with no memory of having written the page.

## The corrections that were themselves wrong

The `KNOWN-ISSUES` entry A0b was corrected twice in one day and was wrong both times.

The first version said the friction clamp bites at 93.3 m/s on "most of the sealed set". I recomputed it. Wrong, and wrong in the direction that made the defect look small. The correction said 91.7 m/s and claimed the clamp binds on **all** circuits by construction. Wrong in the opposite direction, and loudest at Mexico City, which it named as the extreme case and which turns out to be the one circuit where the clamp does not bind at all.

Both wrong versions came from importing the physics module and evaluating at its defaults instead of following what the prediction path does. The first skipped the load model. The second dropped the top-speed ratio out of `V_CAP` and held density fixed at 1.225. At 2,240 m the air is thin, the downforce is lower, the tyre never reaches its floor. The third version reads density out of each sealed commitment and gets six of nine.

There is no flattering way to record this. A defect list is a claim to have checked, so being wrong inside one is worse than being wrong outside it. What it demonstrates is narrow and useful: recomputing against a module's defaults is not recomputing against the code, and the person most likely to make that substitution is the one who already believes he knows the answer.

## What worked, and it was not effort

Five separate passes, each with one question, beat a full day of careful verification by the same person on the same files. That is not because the questions were clever.

**Removing context, not adding effort.** Everything on the second day was read cold. Nothing could be skimmed, because nothing was familiar. I had read those lines so many times that I recognised them instead of reading them.

**One adversarial angle stated as a job.** "Find how I could cheat" produced things "review this repository" never would. That pass went hunting for what the hash does *not* cover and came back with the round number: a field outside the seal, editable after the fact, that decides which grand prix a sealed call gets graded against.

**Asking for the negative out loud.** Every pass was required to report finding nothing rather than fill the space. Several categories came back clean and those are load-bearing. The seals verify, the manifest binds, and no scrubbing failure survived in the published tree.

**Not believing any of it without recomputing.** One pass attributed the rotation defect entirely to the energy model. Re-measured across all nine circuits, the split was different and varied by venue. Another read three photographs confidently and the repository's own files contradicted it. A finding that is trusted instead of checked has just moved the single point of failure.

## What this says about the first round

The section above ends by claiming the method transfers. It does. I understated what it costs.

The first round found five defects and ended with a corrected model and a sealed set. The second round found that the *corrections* had a leak, the *verification document* carried a false claim, and the *defect list* had two wrong entries. Every one of those artifacts came out of the process the first round recommends.

That is not an argument against the process. It is the actual shape of the thing. An audit produces a new artifact, and the new artifact has not been audited. The only stopping condition that is not arbitrary comes from outside: a timestamp that makes the current state permanent and turns every later finding into something disclosed rather than repaired. That is why the anchor matters more than any single fix, and why it is written into the v4 declaration as the end of the sequence.
