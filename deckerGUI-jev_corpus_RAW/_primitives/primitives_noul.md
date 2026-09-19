# Noul

> A Noul question asks the model to evaluate a yes/no question and return the probability that the answer is yes.

Use a Noul when the answer is yes or no. For example, does this message ask for a refund, does this resume mention distributed systems, does this comment contain personal data. If the answer is one of several options, use a [Choice](/primitives/choice). If it's a position on a spectrum, use a [Score](/primitives/score). [Choose a question type](/primitives#choose-a-question-type) compares all three.

A Noul answer is a single number, `noul`, the probability that the answer is yes.

## Writing a Noul question

A Noul question evaluates a single yes/no question (or statement). It is defined by its `instructions`: the yes/no question to evaluate. It's good practice to phrase it so a high probability means "yes", so that the returned answer is unambiguous in its meaning.

You can optionally add `criteria` with `true` and `false` descriptions to clarify what each outcome means, which can be helpful when the question itself has more nuance to explain. Try your Noul question prompts with and without criteria to see which works better in your use-case.

## Request

| Field          | Required | Description                                                                  |
| -------------- | -------- | ---------------------------------------------------------------------------- |
| `type`         | Yes      | Must be `"noul"`.                                                            |
| `instructions` | Yes      | The yes/no question or statement to evaluate.                                |
| `criteria`     | No       | Optional `{ true, false }` descriptions clarifying what a yes and a no mean. |

```js example
example = {
state: 'I have asked three times now. Can I please just talk to a real person?',
selectedModels: ['jev-latest'],
questions: {
  is_human_escalation: {
    type: 'noul',
    instructions: 'Is the customer asking for a human agent?',
  },
  is_repeat_contact: {
    type: 'noul',
    instructions: 'Has the customer contacted support about this before?',
    criteria: {
      true: 'Mentions a prior attempt, ticket, or that they have asked before',
      false: 'No sign of any previous contact',
    },
  },
},
}
```

## Response

```json theme={null}
{
  "model": "jev-latest",
  "answers": {
    "is_human_escalation": {
      "type": "noul",
      "noul": 0.99
    },
    "is_repeat_contact": {
      "type": "noul",
      "noul": 0.93
    }
  },
  "usage": {
    "input_tokens": 360,
    "output_tokens": 39
  }
}
```

`noul` ranges from 0 to 1, representing the probability that the answer is **yes**. Most often you will threshold it into a boolean when your code needs a hard decision.

## Noul does not return a separate confidence value

A value near 1 means a strong yes. A value near 0 means a strong no. A value near 0.5 gives yes and no similar probability.

For "Is the candidate strong in Python?", define what "strong" means. An unclear definition makes the probability hard to interpret. A value of 0.5 does not mean medium skill. Use a [Score](/primitives/score) to measure skill along defined levels. [Choose a question type](/primitives#choose-a-question-type) explains the distinction.

## Example questions

```
"Is the customer requesting a refund?"
"Does this resume mention experience with distributed systems?"
"Does the message contain personally identifiable information?"
"Does the room have a minifridge?"
```

## Tips and advanced usage

* **Phrasing.** Beyond a plain question, you can phrase the instruction as a statement for the model to evaluate for truthfulness. For "the customer is requesting a refund", a value near 1 means the statement is true. Try both phrasings with your own data to see what works best.
* **Optional `criteria`.** The instruction is enough for most Noul questions, but when the boundary between yes and no is subtle, pass `criteria` with `true` and `false` descriptions to pin down what each outcome means — as shown in the request example above.
