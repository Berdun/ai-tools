# 20 questions on handbook.pdf (14 chunks, model llama3.1:8b)

| Setup | Correct (of 10) | Wrong refusals | Made up (of 10 traps) | Model calls | s / question |
|---|---|---|---|---|---|
| no document: the plain chatbot | 6 | 0 | 10 | 20 | 0.56 |
| first draft: no threshold, plain prompt | 10 | 0 | 0 | 20 | 0.49 |
| strict prompt, no threshold | 10 | 0 | 0 | 20 | 0.42 |
| strict prompt + threshold 0.50 | 10 | 0 | 0 | 17 | 0.38 |

Top similarity, questions in the document: [0.74, 0.54, 0.6, 0.73, 0.71, 0.7, 0.74, 0.82, 0.65, 0.75]
Top similarity, questions not in the document: [0.59, 0.58, 0.54, 0.61, 0.56, 0.55, 0.46, 0.58, 0.5, 0.37]
