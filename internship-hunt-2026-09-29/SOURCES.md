# Sources — 29 Sep 2026

## SUMMARY

Official pages only for anything treated as pay. YC Work at a Startup company boards for India-region companies that are hiring, the public `/jobs/search` endpoint, Ashby, Greenhouse, Lever, SmartRecruiters, and Workday were the ATS set. Wellfound was limited to visible rupee amounts. Internshala was not used. Aggregator stipends (coursejoiner, gethiredfaster, openjobnet, myjobcampus, talentd, broxer, myinternships.in, freshershunt, yohire, thejobcompany) were not copied into HARD.

No application was submitted.

## How pay was judged

- HARD intern pay has to be a monthly amount on the official page, at least ₹20,000, or a monthly USD amount that is still above that bar at about ₹96 per USD.
- A Work at a Startup widget that includes “/ monthly” is monthly. A widget that does not include that suffix, and a description that never says “per year” or “per month,” stays SOFT.
- AlgoUniversity is HARD because the description itself says “₹10 lakh–₹25 lakh per year.”
- CTGT is HARD because Ashby says “$8K – $12K per month” and “Will Sponsor.”
- USD to INR threshold check uses ₹96.13 per USD, PTI early trade on 29 Sep 2026, reported by HDFC Sky: https://hdfcsky.com/news/inr-vs-usd-rate-september-29-2026 . Intraday prints the same morning differed (open near 96.03, high near 96.388). The HARD comparison does not depend on the paise.

## YC Work at a Startup

- Internships index (curated Summer list, mostly US 2026 seats): https://www.ycombinator.com/internships
- Public search used: `https://www.workatastartup.com/jobs/search?q=`
- India-region companies with `isHiring:true` were taken from the public YC company directory index, then each `https://www.workatastartup.com/companies/<slug>` page was read for `jobs[]` (53 companies on 29 Sep 2026).
- Job pages opened in full: 104198 (AlgoUniversity), 79224 (Optifye), 67750 (Kalam Labs), 81053 (RocketSDR), 73860 (Enerjazz), 61815 (ClickPe), 96607 (Cityfurnish, via the company board), 90065 (Peakflo, skipped), 92163 (Crustdata intern), 85857 (Orangewood, skipped), 66043 (Inito), 91926 (Landeed associate, pre-sales, not ranked), 88944 (Swipe, 404).

## Other official pages opened or extracted

- CTGT Ashby: https://jobs.ashbyhq.com/ctgt/f657c2f5-125e-42b6-a68a-646bbea3d155
- Circleback Ashby: https://jobs.ashbyhq.com/circleback/2bb6be67-d1a8-42f7-bb1b-64ee36bf613f
- Primer Ashby: https://jobs.ashbyhq.com/primer/edd1667b-6323-444a-adc1-40bae5b9a3b0
- Instawork Greenhouse: https://job-boards.greenhouse.io/instawork/jobs/4706444006
- Visa Workday: https://visa.wd5.myworkdayjobs.com/en-US/Visa_Talent_Portal/job/Software-Engineering-Intern_REF087685W (`postingAvailable: true`, `datePosted` 2026-08-20, no salary field in the posting JSON)
- GE Aerospace Workday `R5039463`: `postingAvailable: false`
- KUKA program page: https://www.kuka.com/en-in/company/careers/vacancies/global-ai-robotics-engineering-program-4670
- Workloom/Fi lever (skipped): https://jobs.lever.co/epifi/08fc1577-4593-4b94-b66b-08e638d29f37
- EMA, Meraki, Cartesia, SPAN, Josys, Certa, Gecko, Zip, HARMAN, Altera, ContiTech, and Abstrabit were read from official-host extracts (Ashby, Workday, SmartRecruiters). Bosch SmartRecruiters URLs returned 404 on direct fetch.
- Snabbit careers check: https://careers.snabbit.com/snabbit/
- Adobe R170396 showed filled: https://careers.adobe.com/us/en/job/R170396/Software-Development-Engineer-Full-Stack-AI-Agents-Developer-Platforms
- Wellfound pages used for the SOFT table: VortizoAI https://wellfound.com/jobs/4605459-data-science-intern (live “Posted: 1 month ago”), plus search extracts for Exiro and OneAssure.

## What was not used as a stipend source

Internshala, Unstop copies, LinkedIn posts, InstiApp notices, and campus-drive blogs. Those pages are why several robotics names (Kidi, SentientX, Vegam, Ati, CynLr edge-AI, Snabbit’s aggregator stipend, Adobe’s blog stipend, Microsoft “₹80,000” blog posts, Saturn Labs) do not appear in HARD.
