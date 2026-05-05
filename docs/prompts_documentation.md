For the classification and enrichment step, I did not start with the final prompt immediately. My initial version was a simple zero-shot prompt. It explained the input sources and gave the model direct category and priority rules.

**Initial prompt snippet:**

```text
You are ArcVault's AI intake assistant.

The input can come from email, web form, support portal, or webhook/API submission.

Your task is to read the customer request and map it to the category that fits best.

Categories:
- Bug Report: if the user reports that something is broken, not working, or showing an error.
- Feature Request: if the user asks for something new or improved.
- Billing Issue: if the user talks about invoices, payments, charges, or pricing.
- Technical Question: if the user asks how to set up or use something.
- Incident/Outage: if the system is down or many users are affected.

Priority:
- High: system not working, customer cannot complete work, urgent request, security issue, data loss, or production failure.
- Medium: limited issue, billing concern, blocked setup, or important feature request.
- Low: general question, small improvement, or no urgency.
```

This first version was easy to understand, but after testing it, I noticed that it was too informal. The phrase “if the user…” made the rules simple, but not always precise enough. Some messages can fit more than one category depending on the context. For example, an Okta message can be a Technical Question when the customer asks how to set up SSO, but it can be a Bug Report if the customer says login started failing after a product update. Because the routing logic depends on the category, I needed the prompt to reduce ambiguity as much as possible.

**Refined prompt snippet:**

```text
Classify the request into exactly one category:

- "Bug Report": choose this when the customer describes an existing feature that is failing, producing an error, or not working as expected.

- "Feature Request": choose this when the customer wants a new capability, an enhancement, or a workflow improvement, without reporting a current failure.

- "Billing Issue": choose this when the message concerns invoices, payments, refunds, contract rates, subscriptions, or unexpected charges.

- "Technical Question": choose this when the customer asks how to configure, integrate, authenticate, set up, or use ArcVault, and the message does not clearly describe a defect.

- "Incident/Outage": choose this when the message indicates an active service interruption, unavailable dashboard/API, system-wide failure, or impact on multiple users.
```

The refined version is still zero-shot, but it uses clearer decision criteria and a constrained label space. I kept it zero-shot because the assessment already defines the allowed categories, and I did not want to add examples that might make the model overfit to the five sample messages. Instead of giving many examples, I focused on making the category definitions more operational. This helped make the model’s behavior more consistent, especially for overlapping cases like Bug Report vs Technical Question and Bug Report vs Incident/Outage.

I also refined the priority section. My first priority rules were simple and written in a more conversational way.

**Initial priority snippet:**

```text
High:
- the system is not working
- the customer cannot complete their work
- the request is urgent
- there is a security issue
- there is data loss
- a production task failed

Medium:
- only one user is affected
- billing issue
- setup is blocked
- important feature request

Low:
- general question
- small improvement
- no urgency
```

The problem with this version is that it was too broad. For example, “system is not working” can mean anything from a small page issue to a full outage. So I rewrote the priority section around business impact, affected scope, risk, and urgency.

**Refined priority snippet:**

```text
Assign exactly one priority based on business impact:

- "High":
  - the product or a major feature appears unavailable
  - more than one user, team, or customer workflow is affected
  - the issue blocks an important production task
  - the message suggests security exposure, compliance risk, data loss, or incorrect data
  - the customer uses urgent language such as urgent, ASAP, blocking, cannot work, or unusable

- "Medium":
  - the issue affects one user or a limited area of the product
  - the customer reports a billing or payment discrepancy
  - the customer needs technical guidance before they can continue setup or implementation
  - the product is slow or degraded, but still partially usable
  - the request could improve compliance, auditability, operations, or team efficiency

- "Low":
  - the request is useful but not time-sensitive
  - the message is asking for general information or normal product guidance
  - the request is cosmetic, minor, or does not affect current work
  - there is no clear urgency, risk, or blocked workflow
```

This change made the priority logic more connected to real support operations. I wanted priority to be separate from category, because a category alone does not tell us the business impact. For example, a Feature Request can be Medium if it has compliance impact, while a Bug Report can be High if it blocks login or affects multiple users.

I also added extraction and hallucination-control instructions. In the first version, I only asked the model to extract identifiers from the message, but I did not clearly define how strict it should be.

**Initial extraction snippet:**

```text
Extract important identifiers from the message, such as account IDs, invoice numbers, error codes, amounts, integrations, or affected users.
```

This was not strict enough because the model could infer or invent information that was not actually written in the message. Since the output might be used by a downstream team, I wanted the extracted data to be reliable.

**Refined extraction snippet:**

```text
Extract only identifiers that are clearly present in the message.
Do not invent account IDs, invoice numbers, error codes, amounts, integrations, or affected scope.
For list fields, always return an empty array [] when no values are found. Do not return null for list fields.
```

This was an important refinement because it reduces hallucination risk. For example, if the message does not include an invoice number, the model should not guess one. If there is no error code, it should return an empty list instead of inventing a code.

Overall, I used AI assistance during the prompt refinement stage, but I did not use it as a replacement for the workflow design. My initial prompt captured the rough logic of the assessment, then I improved it using prompt-engineering ideas like role definition, constrained outputs, clearer decision boundaries, and hallucination control. The main tradeoff is that the final prompt is longer, but I preferred clarity and consistency because the LLM output directly affects routing and escalation. With more time, I would test the prompt on a larger set of ambiguous support messages and keep refining the wording based on the model’s mistakes.