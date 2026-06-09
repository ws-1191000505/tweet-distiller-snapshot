# AI Infrastructure Bottleneck Method

Use this reference when the task is to distill Serenity-style research into a reusable way to find AI infrastructure bottlenecks and underpriced beneficiaries.

## Core Question

Do not start with "Which AI stock is cheap?" Start with:

> What new AI workload is forcing the infrastructure stack to reveal a scarce layer that the market has not fully priced?

The method is strongest when it connects a specific demand shock to a constrained layer, then to a company whose exposure is not obvious from broad AI beta.

## Four-Layer Map

1. Demand driver
   - Examples: larger training clusters, inference scaling, custom ASICs, Blackwell/rack-scale systems, CPO, 1.6T/3.2T optics, power density, memory bandwidth.
   - Reject vague drivers like "AI is growing" unless tied to a concrete deployment or architecture change.

2. Physical or technical bottleneck
   - Look for parts of the stack where capacity, qualification time, material physics, yield, power, thermal, test, or customer approval creates scarcity.
   - Examples from the current dataset: InP photonics, continuous-wave lasers, optical transceivers, burn-in/test, HBM/memory, advanced packaging, thermal/power.

3. Beneficiary chain
   - Map prime beneficiaries, second-order suppliers, equipment vendors, materials, foundries, test providers, and small-cap specialists.
   - Prefer focal tickers with direct exposure. Downgrade context tickers, customers, peers, or index-like large caps.

4. Evidence stack
   - Highest-quality events combine customer signal, supply-chain constraint, earnings/order evidence, and field-check/rumor.
   - Single-source bullish language is weak unless supported by later measurable evidence.

## Serenity-Style Search Pattern

Use this sequence:

1. Identify an AI architecture transition.
2. Ask which layer becomes harder, slower, more expensive, or capacity-constrained.
3. List companies that own the scarce capability.
4. Separate obvious winners from overlooked beneficiaries.
5. Check whether the smaller beneficiary has customer access, qualification, funding, capacity, or operating leverage.
6. Check whether price already moved before the event.
7. Classify the event as early discovery, continuation confirmation, late validation, or after-the-fact commentary.
8. Validate against SOXX-relative forward returns and drawdown.

## Underpriced Beneficiary Heuristics

An underpriced beneficiary usually has at least two of these traits:

- It sits one or two layers away from the headline AI winner.
- It controls a narrow technical capability that cannot be quickly replicated.
- Its customer link is plausible but not fully obvious in consensus coverage.
- Its revenue base is small enough that a single ramp can change the financial model.
- It has evidence of qualification, backlog, NRE, prepayment, funding, or capacity expansion.
- It benefits from the constraint even if the final product vendor changes.

## Signal Classification

| Label | Meaning |
| --- | --- |
| `early_discovery` | Thesis appears before a meaningful price move and before consensus recognition. |
| `continuation_confirmation` | There was prior runup, but new evidence confirms the thesis and later upside remains material. |
| `late_validation` | The thesis is likely true, but the price has already captured most of it. |
| `after_fact_commentary` | The post mainly explains a move that already happened. |
| `context_only` | Ticker is a customer, peer, or comparison rather than the intended beneficiary. |

Manual SIVE review supports `continuation_confirmation`: prior runup existed, but follow-through was still large and thesis-consistent.

## What Not To Learn

- Do not learn "buy SIVE" or any other ticker-specific rule.
- Do not treat broad AI networking exposure as automatically alpha.
- Do not equate absolute return with skill when SOXX also rallied.
- Do not treat every bullish thesis as a signal; in the current dataset, broad `bullish_thesis` rows were weaker than evidence-stacked events.
- Do not ignore liquidity and proxy pricing for OTC or non-US instruments.
