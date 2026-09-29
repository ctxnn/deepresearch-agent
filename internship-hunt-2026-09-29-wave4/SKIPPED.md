# SKIPPED — wave 4 (checked 29 Sep 2026)

Opened or retrieved on 29 Sep 2026 and not ranked as new HARD or SOFT. Pay is quoted only as printed.

## Already pitched today (not re-ranked)

These names were on the do-not-pitch list for this wave. If a live page was still up, it is recorded here and not treated as a new find.

| Name | What was still visible | Why skipped |
| --- | --- | --- |
| Atlys | Talent Acquisition Intern, Delhi, Ashby published 2026-09-08. Several City Scout posts published 17–25 Sep 2026. Compensation object empty. | Named skip. |
| AiStudio | Forward Deployed Engineer Intern, India-Remote, Ashby published 2026-09-03. Compensation object is present; this check did not treat it as a new stipend. Outside the 14-day publish window. | Named skip. |
| Ema | AI/Data Resident still the prior-wave Ashby id. Not inside the 14-day publish window on this pass. | Named skip (EMA). |
| Meraki Labs | AI Engineer Intern, Bangalore, Ashby published 2026-09-07. Compensation object empty. | Named skip. Outside the 14-day window. |
| Seeing Systems | Not re-opened. | Named skip for the EU pass. |

## Ashby: India intern posts in the last 14 days that miss a gate

Window used: `publishedAt` on or after **2026-09-15**, through this check on 29 Sep 2026. Method: Ashby posting API `includeCompensation=true` on 1,365 board slugs (225 YC companies tagged India, a hiring AI/robotics YC sample, and a manual slug list). **235** boards returned jobs. **1,130** returned 404.

- SPAN, HR Intern, Bengaluru, published **2026-09-16**. Pay as written: **INR 20,000/Month**. Duration 6 months, in person. Eligibility: “Currently pursuing/ Completed a Masters in Human Resources, Business or a related field.” Compensation object empty; the figure is in the description. https://jobs.ashbyhq.com/span/1a44454a-c4eb-4a73-8f5b-7d3b921c0c1f
- Fourier, Senior Electrical Engineer – India, Hyderabad, published **2026-09-15**. Compensation object: **₹25L – ₹35L**. Bachelor’s in electrical engineering plus “extensive industry experience.” Not an internship. https://jobs.ashbyhq.com/fourier/08e320ee-161c-458d-9bf4-789a9f4df4e5
- Other Fourier India rows on the same board (Director, Electrical Engineering, **₹60L – ₹90L**, published 2026-05-04; Sr. Mechanical Engineer, **₹20L – ₹35L**, published 2026-05-29) are full-time and outside the 14-day window.

No other India intern row published in that window had a written monthly rupee stipend. Sarvam’s two marketing interns and Airbound’s mechanical internship are in `SOFT.md` because the amount is missing, not because the page was dead.

## Ashby intern rows with written USD that do not hire from India

- Gecko Robotics, AI/Machine Learning Engineering Intern, New York, Summer 2027, published **2026-09-16**. Pay as written: **$50 – $90 per hour**. “Currently pursuing a bachelor’s, master’s, or doctoral degree” with expected graduation **between December 2027 and May 2028**. “Due to government program requirements, candidates must be authorized to work in the United States.” Onsite Monday–Friday. https://jobs.ashbyhq.com/gecko-robotics/c097505b-0a28-4a33-a917-268f463641e8
- Gecko Robotics, Full Stack Software Engineering Intern, same dates and visa line. Pay as written: **$40 – $80 per hour**. Graduation window is the same December 2027–May 2028 band. https://jobs.ashbyhq.com/gecko-robotics/01138338-ff3c-4982-8ba3-5401386bf082
- GrayMatter Robotics, Robotics Engineering Intern: Systems & Applications – Immediate Start, Los Angeles, published **2026-09-24**. Pay as written: **$30 – $40 per hour**. “Paid internship running approximately October 2026 through March 2027.” “Candidates must be available to start no later than October 1, 2026.” US citizen, national, lawful permanent resident, or a listed US-person category, and “must secure work authorization in the United States.” https://jobs.ashbyhq.com/graymatter-robotics/aa7c2419-7bb9-4080-9403-937c4db01bb6
- Physical Intelligence, Mechatronics Intern, San Francisco, published **2026-09-17**. Compensation object empty. “Completed 3A Mechanical or Mechatronics Engineering,” with a note that students below 3A are considered for exceptional projects. Duration January–May 2027. No visa sentence. https://jobs.ashbyhq.com/physicalintelligence/0bcf909e-b38b-4276-91a1-e55c4c56a33a
- 1X, CNC Machine Park Intern, Hayward, published **2026-09-18**. Pay as written: **$30.00/hr**. Machine-shop support, not an ML internship. No sponsorship sentence in the fetched text. https://jobs.ashbyhq.com/1x/ebc45d87-58d7-40d8-9e3d-5f3c8aa5eb48

## Named India boards (Greenhouse token, then the board they actually use)

`https://boards-api.greenhouse.io/v1/boards/{token}/jobs` returned **404** on 29 Sep 2026 for `cred`, `phonepe`, `swiggy`, `zepto`, `urbancompany`, `urbanclap`, `browserstack`, `freshworks`, and `chargebee`. `https://job-boards.greenhouse.io/{token}` also 404’d for those tokens, including a PhonePe job URL that search snippets still quote.

| Company | Board actually opened | Intern result |
| --- | --- | --- |
| CRED | Lever `https://api.lever.co/v0/postings/cred?mode=json`. 8 postings, all `full time` (accounts payable, partnerships, copy, credit-card growth, content). | No intern title. |
| PhonePe | `https://www.phonepe.com/careers/` and `/careers/job-openings/`. No Greenhouse, Lever, or Ashby token in the HTML. The static openings page did not list requisitions. | No intern requisition retrieved. |
| Swiggy | MyNextHire `https://swiggy.mynexthire.com/employer/careers/reqlist/get` with `source: careers`. **84** requisitions. | No title containing intern, trainee, fresher, or campus. The zero-experience rows are sales, account, content, and fleet roles. |
| Zepto | `https://www.zepto.com/s/careers` is a culture page. Lever `zepto` and `zeptonow` 404. Greenhouse token 404. | No official intern requisition retrieved. |
| Urban Company | `https://careers.urbancompany.com/` is a marketing shell. Lever `urbancompany` and `urbanclap` 404. Greenhouse token 404. | No official intern requisition retrieved. |
| BrowserStack | Workday `browserstack.wd3.myworkdayjobs.com/External`. Search text `Internship` returned **0**. Search text `Intern` returned 13 rows whose titles are account manager, marketing, strategy, and compliance. | No intern title. |
| Freshworks | SmartRecruiters `https://api.smartrecruiters.com/v1/companies/Freshworks/postings`. **124** postings, **30** with `country=in` (Bengaluru, Chennai, Hyderabad). India titles are lead, staff, and principal. | No intern, trainee, or fresher title. |
| Chargebee | `https://jobs.chargebee.com/search/?q=intern` (SuccessFactors). The result set shown was Principal, Revenue Solutions – Field CFO. | No intern title. |

## EU robotics internships that do not sponsor from India, or that exclude a bachelor’s

- Stryker, Internship Software for AI Applications in Robotic-Assisted Surgery, 6 months, start March or April 2027, Freiburg. Official Workday page, `datePosted` **2026-08-31**, requisition R572200. Pay as written: **Freiburg 39Std: €2.476,89 EUR Monthly**. Eligibility: “Currently pursuing a Master’s degree” in computer science, biomedical engineering, medical engineering, software engineering, information technology, or a related field. Location line is Freiburg. https://stryker.wd1.myworkdayjobs.com/en-US/StrykerCareers/job/Freiburg-Germany/Internship-Software-for-AI-Applications-in-Robotic-Assisted-Surgery---6-Months---Start-Spring-2027_R572200-1
- ANYbotics, Software Engineering Internship – AI Platform, Zurich, onsite, 6 months. Lever id `7e305a48-4628-4a6a-b054-0367b6f6e586`. Pay as written: “a fair market salary” (no figure). Non-EU applicants: the internship must be mandatory, a work permit is required, and the candidate “Must reside in CH.” Schengen citizens, or ETH/EPFL students on a compulsory internship, are the other path. https://jobs.lever.co/anybotics/7e305a48-4628-4a6a-b054-0367b6f6e586
- Doctolib, Medical Data Intern, Berlin, Ashby published **2026-09-22**. Terminology and ontology work. “You have medical skills gained through a diploma or degree that includes medical-domain learning.” Compensation object empty. “A Deutschlandticket sponsored by Doctolib” is a transit ticket, not a visa. https://jobs.ashbyhq.com/doctolib/42b97078-9d79-432d-95d4-0a44fcbb65b9
- Neura’s English AI intern page is in `SOFT.md` because a current robotics degree is accepted and the missing piece is the number. It is not listed here as a sponsor offer.

## Institute PDFs

This pass looked for an official IIT, NIT, IIIT, or CSIR PDF **dated after 20 Sep 2026**, still open, BE-eligible, AI/ML/robotics, and at least ₹20,000/month. Mandi, BHU, Roorkee, Kharagpur, Madras, ISM, ISI, IISER Thiruvananthapuram, and NIT Calicut were not re-opened.

- NIT Uttarakhand recruitments index, read via search on 29 Sep 2026: **Advt. No. 08/2026**, dated **21/09/2026**, is “Advertisement for Non-Teaching Staff (On deputation or contractual basis).” Not an AI/ML/robotics internship. https://nituk.ac.in/recruitments
- Same index: **Advt. No. 09/2026**, dated **11/09/2026**, walk-in for Project Associate / JRF / Research Associate on “VLSI Design and Implementation of Imagined Speech based Neuroprosthesis.” Dated before 20 Sep 2026, so it is outside this wave’s date filter. The PDF URL returned 403 to this client, so the stipend and the walk-in day were not taken from an older May 2026 copy of the same project.
- IIT Indore JRF, Advt dated **17/09/2026**, last date **30 September 2026**, **Rs. 37,000 + HRA**. Project is streamflow forecasting with deep learning. Essential qualification is a master’s in engineering. Dated before 20 Sep 2026. https://www.iiti.ac.in/uploads/career/2026/Sep/d4ed0d62873a06acf71fb85e216f06eb.pdf
- IIIT Bhopal JRF, advertisement dated **07-September-2026**, last date **27 September 2026**, **₹37,000 per month + HRA**. SENSE-VIBE, machine learning on vibration and audio. Dated before this window, and the last date had passed by 29 Sep 2026. https://iiitbhopal.ac.in/Media/Notice/N26090002/61114.pdf
- DTU Research Intern, advertisement dated **25/09/2026**, last date **12/10/2026**, **Rs. 15,000/- per month**. Deep learning for glaucoma. DTU is outside the IIT/NIT/IIIT/CSIR set, and the written stipend is under ₹20,000. https://dtu.ac.in/Web/upload/jobs/2026/sep/file0908.pdf
- IIT Patna underwater-intrusion JRF write-ups dated around 27 Sep 2026 appeared on job blogs (last date 4 Oct 2026, Rs 37,000–42,000). No official IIT Patna PDF was retrieved. Not ranked.
- IIT Hyderabad Junior Project Assistant robotics PDF still shows last date **31 August 2026** and **Rs 18,200 per month**. Closed and under the floor. https://iith.ac.in/assets/files/careers/staff/Advertisement-for-Junior-Project-Assistant.pdf
- NITK Surathkal NITHRA project-intern PDF (humanoid, NLP) still shows an email deadline of **31 May 2026**. https://www.nitk.ac.in/document/attachments/9693/Ad_Post_of_Project_Interns-NLP.pdf
- CSIR-NPL walk-in advertisement in search is the February 2026 notice (interview 12 February 2026), including a research-intern line at Rs. 24,000. Not a September notice.
