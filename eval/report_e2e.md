# E2E evaluation

Model `gpt-4.1-mini` · embeddings `text-embedding-3-small` · retrieval `hybrid` · MIN_SIMILARITY 0.35 · MIN_BM25_SCORE 4.0

**34/34 passed** · avg 1.2s per case

## [PASS] vac-accrual
> **Q1:** How many vacation days do I accrue each month?

Standalone query: _How many vacation days do I accrue each month?_  
Expected: ['TKT-00003'] · Cited: ['TKT-00003'] · 2.4s

Full-time employees accrue 1.25 vacation days per month, which totals 15 days per year [1].

## [PASS] vac-pto-rollover
> **Q1:** Can I roll over unused PTO?

Standalone query: _Can I roll over unused PTO?_  
Expected: ['TKT-00003'] · Cited: ['TKT-00003'] · 1.1s

Yes, you can roll over unused PTO, but only up to 5 unused vacation days can be carried over into the next calendar year. Any balance above 5 days will expire on January 31. You can check your current PTO balance under 'Time Off' in the employee portal [1].

## [PASS] sick-today
> **Q1:** I'm sick today, what should I do?

Standalone query: _I'm sick today, what should I do?_  
Expected: ['TKT-00004'] · Cited: ['TKT-00004'] · 1.3s

If you are sick today, you should notify your manager before the start of your shift either via Slack or phone. After that, log your sick day in the employee portal within 24 hours. If your absence lasts longer than 3 consecutive days, you will need to upload a doctor's note to the portal [1].

## [PASS] sick-note
> **Q1:** Do I need a doctor's note if I'm out for a while?

Standalone query: _Do I need a doctor's note if I'm out for a while?_  
Expected: ['TKT-00004'] · Cited: ['TKT-00004'] · 0.9s

Yes, if you are absent for more than 3 consecutive days due to illness, you need to provide a doctor's note. This note should be uploaded to the employee portal within 24 hours of notifying your manager about your sick day [1].

## [PASS] payday
> **Q1:** When is payday?

Standalone query: _When is payday?_  
Expected: ['TKT-00005'] · Cited: ['TKT-00005'] · 1.1s

Payday occurs bi-weekly on Fridays. If a payday falls on a public holiday, the funds are deposited on the previous business day [1].

## [PASS] paystubs
> **Q1:** Where can I find my pay stubs?

Standalone query: _Where can I find my pay stubs?_  
Expected: ['TKT-00005'] · Cited: ['TKT-00005'] · 1.0s

You can find your pay stubs under 'Payroll > Pay Statements' in the employee portal. Pay stubs are available after each bi-weekly payroll run on Fridays, or the previous business day if payday falls on a public holiday [1].

## [PASS] bank-change
> **Q1:** How do I update the bank account my paycheck goes to?

Standalone query: _How do I update the bank account my paycheck goes to?_  
Expected: ['TKT-00006'] · Cited: ['TKT-00006'] · 1.1s

To update the bank account for your paycheck direct deposit, go to 'Payroll > Banking Details' in the employee portal. Submit your changes before the Tuesday prior to payday for them to take effect in the next pay cycle. After submitting, you will receive a confirmation email and must verify the change using multi-factor authentication for security purposes [1].

## [PASS] free-glasses
> **Q1:** Do employees get free glasses?

Standalone query: _Do employees get free glasses?_  
Expected: ['TKT-00007'] · Cited: ['TKT-00007'] · 1.1s

Yes, all employees receive one free pair of SuperGlasses frames with prescription lenses per calendar year. Additionally, they get 40% off on any additional eyewear purchases. Employees can use their discount code found on the portal's 'Perks' page at checkout on superglasses.com [1].

## [PASS] open-enrollment
> **Q1:** When is open enrollment for dental insurance?

Standalone query: _When is open enrollment for dental insurance?_  
Expected: ['TKT-00008'] · Cited: ['TKT-00008'] · 1.0s

Open enrollment for dental insurance runs from November 1 to November 30. During this period, you can review plan options and make your elections under 'Benefits > Enrollment'. If you do not make any changes, your current elections will roll over to the next year [1].

## [PASS] password
> **Q1:** I forgot my password

Standalone query: _I forgot my password_  
Expected: ['TKT-00009'] · Cited: ['TKT-00009'] · 1.0s

To reset your network or email password, visit the self-service password portal at password.superglasses.internal and verify your identity with your registered phone. If you are locked out after 5 failed attempts, contact the IT Help Desk at extension 4357 for assistance [1].

## [PASS] vpn
> **Q1:** VPN setup

Standalone query: _VPN setup_  
Expected: ['TKT-00010'] · Cited: ['TKT-00010'] · 1.0s

To set up the VPN, you need to install the VPN client from the IT Software Center. After installation, sign in using your corporate credentials. This connection is necessary for remote employees to access internal systems like the order management system or the lens lab dashboard [1].

## [PASS] phishing
> **Q1:** What should I do with a suspicious email?

Standalone query: _What should I do with a suspicious email?_  
Expected: ['TKT-00011'] · Cited: ['TKT-00011'] · 1.1s

If you receive a suspicious email, you should report it using the 'Report Phishing' button in Outlook. Avoid clicking any links or opening attachments that ask for login credentials or customer payment information. If you accidentally click a malicious link, immediately disconnect from the network and contact Security at security@superglasses.internal for assistance [1].

## [PASS] rx-data
> **Q1:** Am I allowed to look at a customer's prescription data?

Standalone query: _Am I allowed to look at a customer's prescription data?_  
Expected: ['TKT-00012'] · Cited: ['TKT-00012'] · 0.9s

You are allowed to access a customer's prescription data only when it is necessary to fulfill or support their order. You must never share this information over unsecured channels or copy it into personal notes or spreadsheets, as customer prescription and health data is protected information [1].

## [PASS] first-week
> **Q1:** What do I need to do during my first week?

Standalone query: _What do I need to do during my first week?_  
Expected: ['TKT-00013'] · Cited: ['TKT-00013'] · 1.3s

During your first week, you need to complete the onboarding checklist in the employee portal. This includes signing your offer documents, setting up direct deposit, completing security and privacy training, and scheduling a 1:1 meeting with your manager. Additionally, your laptop will be shipped to your home address three business days before your start date to ensure you have the necessary equipment ready [1].

## [PASS] returns
> **Q1:** How long do customers have to return frames?

Standalone query: _How long do customers have to return frames?_  
Expected: ['TKT-00014'] · Cited: ['TKT-00014'] · 1.7s

Customers have 30 days from delivery to return frames for a full refund [1].

## [PASS] shipping-time
> **Q1:** How long does standard shipping take?

Standalone query: _How long does standard shipping take?_  
Expected: ['TKT-00016'] · Cited: ['TKT-00016'] · 0.8s

Standard shipping takes 7-10 business days, including lens production time [1].

## [PASS] lost-package
> **Q1:** The package shows delivered but the customer never got it

Standalone query: _The package shows delivered but the customer never got it_  
Expected: ['TKT-00017'] · Cited: ['TKT-00017'] · 1.1s

If a package is marked as delivered but the customer has not received it, you should wait 48 hours first. After that, file a carrier claim from the 'Shipping Issues' tab and send a replacement order using the reason code 'SHIP-LOST'. Note that if the replacement order is over $300, you will need supervisor approval before proceeding [1].

## [PASS] rx-verify
> **Q1:** What should I check on a prescription before sending it to the lens lab?

Standalone query: _What should I check on a prescription before sending it to the lens lab?_  
Expected: ['TKT-00018'] · Cited: ['TKT-00018'] · 1.3s

Before sending a prescription to the lens lab, you should verify that it includes the following details: sphere, cylinder, axis, and pupillary distance (PD). Additionally, ensure that the prescription is signed and is less than 2 years old. If any information is missing, set the order to 'On Hold - Rx' and email the customer using the 'Rx Missing Info' template [1].

## [PASS] pd-keyword
> **Q1:** PD missing on order

Standalone query: _PD missing on order_  
Expected: ['TKT-00018'] · Cited: ['TKT-00018'] · 1.2s

If the pupillary distance (PD) is missing on an order, you should set the order status to 'On Hold - Rx' and email the customer using the 'Rx Missing Info' template to request the missing information. This ensures the prescription is complete before the order proceeds to the lens lab [1].

## [PASS] chat-sla
> **Q1:** How fast should I reply to live chats?

Standalone query: _How fast should I reply to live chats?_  
Expected: ['TKT-00020'] · Cited: ['TKT-00020'] · 0.9s

You should respond to live chats within 60 seconds according to the customer service response time standards [1].

## [PASS] tier2
> **Q1:** Tier 2 escalation

Standalone query: _Tier 2 escalation_  
Expected: ['TKT-00021'] · Cited: ['TKT-00021'] · 1.0s

Tier 2 escalation occurs when a customer case meets specific criteria such as the customer requesting a manager, a refund exceeding $250, a possible allergic reaction to frame materials, or mention of legal action. In these situations, the case should be escalated to a Tier 2 supervisor. The process involves using the 'Escalate' button in the help desk tool and adding a summary note to the case [1].

## [PASS] expenses
> **Q1:** How do I submit an expense report?

Standalone query: _How do I submit an expense report?_  
Expected: ['TKT-00022'] · Cited: ['TKT-00022'] · 1.0s

To submit an expense report, go to 'Finance > Expenses' in the employee portal and submit your business expenses such as travel, client meals, and home-office equipment within 30 days of purchase. For any expense over $25, you need to attach an itemized receipt. Approved expenses will be reimbursed on the next payroll cycle [1].

## [PASS] stipend
> **Q1:** stipend

Standalone query: _stipend_  
Expected: ['TKT-00023'] · Cited: ['TKT-00023'] · 1.0s

Remote and hybrid employees are eligible for a one-time home-office stipend of up to $500. This stipend can be used to purchase a desk, chair, or monitor. To receive the stipend, submit your purchase as an expense under the category 'Home Office Stipend' within 90 days of your start date [1].

## [PASS] reviews
> **Q1:** When are performance reviews?

Standalone query: _When are performance reviews?_  
Expected: ['TKT-00024'] · Cited: ['TKT-00024'] · 0.9s

Performance reviews take place twice a year, specifically in April and October. Employees should complete their self-assessment in the 'Performance' module at least one week before their scheduled review meeting. Managers then submit final ratings within two weeks of the meeting [1].

## [PASS] lab-ppe
> **Q1:** What protective gear do I need in the lens lab?

Standalone query: _What protective gear do I need in the lens lab?_  
Expected: ['TKT-00025'] · Cited: ['TKT-00025'] · 0.9s

In the lens lab, you must wear safety glasses and nitrile gloves when operating edging and coating machines. This is required for all warehouse and lens lab staff to ensure safety while working with the equipment [1].

## [PASS] followup-carryover
> **Q1:** How many vacation days do I get per year?
> **Q2:** Can I carry any of them over?

Standalone query: _Can I carry over any of my accrued vacation days to the next year?_  
Expected: ['TKT-00003'] · Cited: ['TKT-00003'] · 3.3s

Yes, you can carry over up to 5 unused vacation days into the next calendar year. Any balance above 5 days will expire on January 31 [1].

## [PASS] followup-vpn-pw
> **Q1:** How do I connect to the VPN?
> **Q2:** And what if I forget my password?

Standalone query: _What should I do if I forget my corporate password needed to sign in to the VPN?_  
Expected: ['TKT-00009'] · Cited: ['TKT-00009'] · 3.7s

If you forget your password, you can reset it by visiting the self-service password portal at password.superglasses.internal. You will need to verify your identity using your registered phone. If you get locked out after 5 failed attempts, contact the IT Help Desk at extension 4357 for assistance [1].

## [PASS] followup-returns-refund
> **Q1:** How do I process a customer return?
> **Q2:** When should that be escalated to a supervisor?

Standalone query: _When should a customer return be escalated to a supervisor?_  
Expected: ['TKT-00021'] · Cited: ['TKT-00021'] · 3.0s

Escalate a customer case to a Tier 2 supervisor if:

- The customer requests a manager.
- The refund amount exceeds $250.
- The case involves a possible allergic reaction to frame materials.
- The customer mentions legal action.

Use the 'Escalate' button in the help desk tool and add a summary note when escalating [1].

## [PASS] oos-capital
> **Q1:** What is the capital of Mongolia?

Standalone query: _What is the capital of Mongolia?_  
Expected: fallback · Cited: - · 0.3s

I couldn't find anything about that in the employee knowledge base. Please reach out to your manager or the HR team, who can help you directly.

## [PASS] oos-401k
> **Q1:** What is the company 401k match?

Standalone query: _What is the company 401k match?_  
Expected: fallback · Cited: - · 0.3s

I couldn't find anything about that in the employee knowledge base. Please reach out to your manager or the HR team, who can help you directly.

## [PASS] oos-dog
> **Q1:** Can I bring my dog to the office?

Standalone query: _Can I bring my dog to the office?_  
Expected: fallback · Cited: - · 0.2s

I couldn't find anything about that in the employee knowledge base. Please reach out to your manager or the HR team, who can help you directly.

## [PASS] oos-parking
> **Q1:** Where do I park on my first day?

Standalone query: _Where do I park on my first day?_  
Expected: fallback · Cited: - · 0.7s

I couldn't find anything about that in the employee knowledge base. Please reach out to your manager or the HR team, who can help you directly.

## [PASS] excluded-archived
> **Q1:** Where is the legacy inventory spreadsheet?

Standalone query: _Where is the legacy inventory spreadsheet?_  
Expected: fallback · Cited: - · 0.4s  
Note: only source is archived TKT-00027

I couldn't find anything about that in the employee knowledge base. Please reach out to your manager or the HR team, who can help you directly.

## [PASS] excluded-pending
> **Q1:** Which reason code do I use for a defective lens remake?

Standalone query: _Which reason code do I use for a defective lens remake?_  
Expected: fallback · Cited: - · 0.7s  
Note: only source is pending TKT-00015

I couldn't find anything about that in the employee knowledge base. Please reach out to your manager or the HR team, who can help you directly.

## [PASS] vac-request-gap
> **Q1:** How do I request a vacation?

Standalone query: _How do I request a vacation?_  
Expected: ['TKT-00026'] · Cited: ['TKT-00026'] · 1.0s  
Note: only published source is the Spanish TKT-00026; English TKT-00002 is pending

To request a vacation, log in to the employee portal and submit a vacation request. Make sure to add your manager as the approver. Vacation requests should be submitted at least two weeks in advance to allow for proper approval [1].
